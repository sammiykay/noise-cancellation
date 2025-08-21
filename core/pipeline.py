"""Main processing pipeline for noise cancellation."""

import time
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
import numpy as np

from utils.logging_setup import get_logger
from utils.paths import generate_output_path, get_unique_path
from core.media import (
    get_media_info, extract_audio, load_audio, save_audio,
    remux_audio_video, convert_audio_format
)
from engines.spectral_gate import SpectralGateEngine, SpectralGateConfig
from engines.rnnoise import RNNoiseEngine, RNNoiseConfig
from engines.demucs import DemucsEngine, DemucsConfig

logger = get_logger("pipeline")


class ProcessingStage(Enum):
    """Processing pipeline stages."""
    IDLE = "idle"
    VALIDATING = "validating"
    LOADING = "loading"
    EXTRACTING_AUDIO = "extracting_audio"
    NOISE_REDUCTION = "noise_reduction"
    POST_PROCESSING = "post_processing"
    SAVING = "saving"
    REMUXING = "remuxing"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


class Engine(Enum):
    """Available noise reduction engines."""
    SPECTRAL_GATE = "spectral_gate"
    RNNOISE = "rnnoise"
    DEMUCS = "demucs"


@dataclass
class ProcessingJob:
    """Container for processing job information."""
    input_path: Path
    output_path: Optional[Path] = None
    engine: Engine = Engine.SPECTRAL_GATE
    engine_config: Optional[Dict[str, Any]] = None
    output_format: str = "wav"
    sample_rate: Optional[int] = None
    preserve_video: bool = True
    normalize_loudness: bool = False
    target_lufs: float = -23.0
    
    # Job state
    stage: ProcessingStage = ProcessingStage.IDLE
    progress: float = 0.0
    message: str = ""
    error_message: str = ""
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    # Results
    original_duration: Optional[float] = None
    processed_duration: Optional[float] = None
    estimated_snr_before: Optional[float] = None
    estimated_snr_after: Optional[float] = None
    
    def __post_init__(self):
        """Initialize computed fields."""
        if self.output_path is None:
            # This will be set later with proper output directory from settings
            pass
    
    @property
    def processing_time(self) -> Optional[float]:
        """Get processing time in seconds."""
        if self.start_time is None:
            return None
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.stage in (ProcessingStage.COMPLETE, ProcessingStage.ERROR, ProcessingStage.CANCELLED)
    
    @property
    def is_video(self) -> bool:
        """Check if input is a video file."""
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        return self.input_path.suffix.lower() in video_extensions


class ProcessingPipeline:
    """Main processing pipeline for noise cancellation."""
    
    def __init__(self):
        """Initialize processing pipeline."""
        self.current_job: Optional[ProcessingJob] = None
        self.cancelled = False
        
        # Initialize engines
        self._engines = {}
        self._init_engines()
    
    def _init_engines(self) -> None:
        """Initialize noise reduction engines."""
        try:
            # Spectral Gate (always available)
            self._engines[Engine.SPECTRAL_GATE] = None  # Lazy initialization
            
            # RNNoise (if available)
            try:
                self._engines[Engine.RNNOISE] = None  # Lazy initialization
            except Exception as e:
                logger.warning(f"RNNoise not available: {e}")
            
            # Demucs (if available)
            try:
                demucs_engine = DemucsEngine(DemucsConfig())
                if demucs_engine.is_available():
                    self._engines[Engine.DEMUCS] = None  # Lazy initialization
                else:
                    logger.info("Demucs not available (not installed)")
            except Exception as e:
                logger.warning(f"Demucs not available: {e}")
            
            logger.info(f"Initialized pipeline with engines: {list(self._engines.keys())}")
            
        except Exception as e:
            logger.error(f"Error initializing engines: {e}")
    
    def get_available_engines(self) -> list[Engine]:
        """Get list of available engines."""
        return list(self._engines.keys())
    
    def _get_engine(self, engine_type: Engine, config: Dict[str, Any]):
        """Get or create engine instance."""
        if engine_type not in self._engines:
            raise ValueError(f"Engine not available: {engine_type}")
        
        # Create engine instance based on type
        if engine_type == Engine.SPECTRAL_GATE:
            engine_config = SpectralGateConfig.from_dict(config)
            return SpectralGateEngine(engine_config)
        
        elif engine_type == Engine.RNNOISE:
            engine_config = RNNoiseConfig.from_dict(config)
            return RNNoiseEngine(engine_config)
        
        elif engine_type == Engine.DEMUCS:
            engine_config = DemucsConfig.from_dict(config)
            return DemucsEngine(engine_config)
        
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
    
    def process_job(
        self,
        job: ProcessingJob,
        progress_callback: Optional[Callable[[ProcessingJob], None]] = None
    ) -> bool:
        """
        Process a single job.
        
        Args:
            job: Processing job to execute
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        self.current_job = job
        self.cancelled = False
        
        job.start_time = time.time()
        job.stage = ProcessingStage.VALIDATING
        job.progress = 0.0
        job.message = "Starting processing..."
        
        try:
            if progress_callback:
                progress_callback(job)
            
            # Step 1: Validate input
            if not self._validate_job(job, progress_callback):
                return False
            
            # Step 2: Load media info
            if not self._load_media_info(job, progress_callback):
                return False
            
            # Step 3: Extract/load audio
            if not self._extract_audio(job, progress_callback):
                return False
            
            # Step 4: Apply noise reduction
            if not self._apply_noise_reduction(job, progress_callback):
                return False
            
            # Step 5: Post-processing
            if not self._post_process(job, progress_callback):
                return False
            
            # Step 6: Save/remux output
            if not self._save_output(job, progress_callback):
                return False
            
            # Complete
            job.stage = ProcessingStage.COMPLETE
            job.progress = 1.0
            job.message = "Processing complete"
            job.end_time = time.time()
            
            if progress_callback:
                progress_callback(job)
            
            logger.info(f"Job completed successfully: {job.input_path} -> {job.output_path}")
            return True
            
        except Exception as e:
            job.stage = ProcessingStage.ERROR
            job.error_message = str(e)
            job.message = f"Error: {str(e)}"
            job.end_time = time.time()
            
            if progress_callback:
                progress_callback(job)
            
            logger.error(f"Job failed: {e}")
            return False
    
    def cancel_current_job(self) -> None:
        """Cancel the currently running job."""
        self.cancelled = True
        if self.current_job:
            self.current_job.stage = ProcessingStage.CANCELLED
            self.current_job.message = "Processing cancelled"
            self.current_job.end_time = time.time()
            logger.info(f"Job cancelled: {self.current_job.input_path}")
    
    def _check_cancelled(self) -> bool:
        """Check if processing was cancelled."""
        if self.cancelled:
            if self.current_job:
                self.current_job.stage = ProcessingStage.CANCELLED
                self.current_job.message = "Processing cancelled"
                self.current_job.end_time = time.time()
            return True
        return False
    
    def _validate_job(self, job: ProcessingJob, progress_callback: Optional[Callable] = None) -> bool:
        """Validate job parameters."""
        job.stage = ProcessingStage.VALIDATING
        job.progress = 0.05
        job.message = "Validating input file..."
        
        if progress_callback:
            progress_callback(job)
        
        if self._check_cancelled():
            return False
        
        if not job.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {job.input_path}")
        
        if not job.input_path.is_file():
            raise ValueError(f"Input path is not a file: {job.input_path}")
        
        # Check if engine is available
        if job.engine not in self._engines:
            raise ValueError(f"Engine not available: {job.engine}")
        
        logger.debug(f"Job validation passed: {job.input_path}")
        return True
    
    def _load_media_info(self, job: ProcessingJob, progress_callback: Optional[Callable] = None) -> bool:
        """Load media file information."""
        job.stage = ProcessingStage.LOADING
        job.progress = 0.1
        job.message = "Loading media information..."
        
        if progress_callback:
            progress_callback(job)
        
        if self._check_cancelled():
            return False
        
        media_info = get_media_info(job.input_path)
        if not media_info:
            raise RuntimeError(f"Could not read media file: {job.input_path}")
        
        job.original_duration = media_info.duration
        
        if not media_info.has_audio:
            raise ValueError(f"No audio track found in: {job.input_path}")
        
        logger.debug(f"Media info loaded: {media_info}")
        return True
    
    def _extract_audio(self, job: ProcessingJob, progress_callback: Optional[Callable] = None) -> bool:
        """Extract or load audio from media file."""
        job.stage = ProcessingStage.EXTRACTING_AUDIO
        job.progress = 0.2
        
        if job.is_video:
            job.message = "Extracting audio from video..."
        else:
            job.message = "Loading audio file..."
        
        if progress_callback:
            progress_callback(job)
        
        if self._check_cancelled():
            return False
        
        # Load audio data
        result = load_audio(
            job.input_path,
            sample_rate=job.sample_rate,
            mono=False
        )
        
        if result is None:
            raise RuntimeError(f"Failed to load audio from: {job.input_path}")
        
        job._audio_data, job._sample_rate = result
        
        logger.debug(f"Audio loaded: shape={job._audio_data.shape}, sr={job._sample_rate}")
        return True
    
    def _apply_noise_reduction(self, job: ProcessingJob, progress_callback: Optional[Callable] = None) -> bool:
        """Apply noise reduction using selected engine."""
        job.stage = ProcessingStage.NOISE_REDUCTION
        job.progress = 0.3
        job.message = f"Applying noise reduction ({job.engine.value})..."
        
        if progress_callback:
            progress_callback(job)
        
        if self._check_cancelled():
            return False
        
        # Get engine instance
        engine_config = job.engine_config or {}
        engine = self._get_engine(job.engine, engine_config)
        
        # Create progress wrapper
        def engine_progress(progress: float, message: str):
            if self._check_cancelled():
                raise RuntimeError("Processing cancelled")
            
            job.progress = 0.3 + 0.5 * progress  # Map to 0.3-0.8 range
            job.message = f"Noise reduction: {message}"
            if progress_callback:
                progress_callback(job)
        
        # Apply noise reduction
        job._processed_audio = engine.process(
            job._audio_data,
            job._sample_rate,
            progress_callback=engine_progress
        )
        
        logger.debug(f"Noise reduction applied: {job.engine.value}")
        return True
    
    def _post_process(self, job: ProcessingJob, progress_callback: Optional[Callable] = None) -> bool:
        """Apply post-processing steps."""
        job.stage = ProcessingStage.POST_PROCESSING
        job.progress = 0.8
        job.message = "Applying post-processing..."
        
        if progress_callback:
            progress_callback(job)
        
        if self._check_cancelled():
            return False
        
        processed = job._processed_audio
        
        # Apply loudness normalization if requested
        if job.normalize_loudness:
            try:
                import pyloudnorm as pyln
                
                job.message = "Normalizing loudness..."
                if progress_callback:
                    progress_callback(job)
                
                meter = pyln.Meter(job._sample_rate)
                loudness = meter.integrated_loudness(processed)
                
                if loudness > -70:  # Only normalize if audio has meaningful content
                    processed = pyln.normalize.loudness(processed, loudness, job.target_lufs)
                
                logger.debug(f"Loudness normalized: {loudness:.2f} -> {job.target_lufs:.2f} LUFS")
                
            except ImportError:
                logger.warning("pyloudnorm not available, skipping loudness normalization")
            except Exception as e:
                logger.warning(f"Loudness normalization failed: {e}")
        
        # Apply gentle limiter to prevent clipping
        max_val = np.max(np.abs(processed))
        if max_val > 0.99:
            processed = processed / max_val * 0.95
            logger.debug("Applied gentle limiter to prevent clipping")
        
        job._processed_audio = processed
        return True
    
    def _save_output(self, job: ProcessingJob, progress_callback: Optional[Callable] = None) -> bool:
        """Save processed audio or remux video."""
        job.stage = ProcessingStage.SAVING
        job.progress = 0.9
        
        if progress_callback:
            progress_callback(job)
        
        if self._check_cancelled():
            return False
        
        # Ensure output path is unique
        job.output_path = get_unique_path(job.output_path)
        
        if job.is_video and job.preserve_video:
            # Remux video with new audio
            job.message = "Remuxing video with processed audio..."
            if progress_callback:
                progress_callback(job)
            
            # Save processed audio to temporary file
            temp_audio_path = job.output_path.with_suffix(".temp.wav")
            
            if not save_audio(job._processed_audio, temp_audio_path, job._sample_rate):
                raise RuntimeError("Failed to save temporary audio file")
            
            try:
                # Remux video
                success = remux_audio_video(
                    job.input_path,
                    temp_audio_path,
                    job.output_path,
                    preserve_metadata=True
                )
                
                if not success:
                    raise RuntimeError("Video remuxing failed")
                
            finally:
                # Clean up temporary file
                if temp_audio_path.exists():
                    temp_audio_path.unlink()
            
        else:
            # Save audio file
            job.message = "Saving processed audio..."
            if progress_callback:
                progress_callback(job)
            
            # Convert format if needed
            if job.output_format.lower() != "wav":
                # Save as WAV first, then convert
                temp_wav = job.output_path.with_suffix(".temp.wav")
                
                if not save_audio(job._processed_audio, temp_wav, job._sample_rate):
                    raise RuntimeError("Failed to save temporary WAV file")
                
                try:
                    success = convert_audio_format(
                        temp_wav,
                        job.output_path,
                        format=job.output_format,
                        sample_rate=job.sample_rate
                    )
                    
                    if not success:
                        raise RuntimeError(f"Audio format conversion failed: {job.output_format}")
                
                finally:
                    if temp_wav.exists():
                        temp_wav.unlink()
            else:
                # Save directly as WAV
                if not save_audio(job._processed_audio, job.output_path, job._sample_rate):
                    raise RuntimeError("Failed to save audio file")
        
        logger.info(f"Output saved: {job.output_path}")
        return True