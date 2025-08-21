"""Demucs-based noise reduction engine (optional advanced feature)."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np
import json

from utils.logging_setup import get_logger
from utils.paths import get_temp_path
from core.media import save_audio, load_audio

logger = get_logger("demucs")


class DemucsConfig:
    """Configuration for Demucs-based noise reduction."""
    
    def __init__(
        self,
        model_name: str = "htdemucs",
        device: str = "cpu",
        segment_length: Optional[float] = None,
        overlap: float = 0.25,
        jobs: int = 1,
        vocal_enhancement: bool = True,
        noise_reduction_strength: float = 0.8
    ):
        """
        Initialize Demucs configuration.
        
        Args:
            model_name: Demucs model to use ('htdemucs', 'hdemucs_mmi', etc.)
            device: Processing device ('cpu', 'cuda', 'mps')
            segment_length: Length of segments in seconds (None for automatic)
            overlap: Overlap between segments (0.0 to 0.5)
            jobs: Number of parallel jobs
            vocal_enhancement: Whether to enhance vocal separation
            noise_reduction_strength: Strength of noise reduction (0.0 to 1.0)
        """
        self.model_name = model_name
        self.device = device
        self.segment_length = segment_length
        self.overlap = max(0.0, min(0.5, overlap))
        self.jobs = max(1, jobs)
        self.vocal_enhancement = vocal_enhancement
        self.noise_reduction_strength = max(0.0, min(1.0, noise_reduction_strength))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'segment_length': self.segment_length,
            'overlap': self.overlap,
            'jobs': self.jobs,
            'vocal_enhancement': self.vocal_enhancement,
            'noise_reduction_strength': self.noise_reduction_strength
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DemucsConfig':
        """Create configuration from dictionary."""
        return cls(**data)


class DemucsEngine:
    """Demucs-based noise reduction engine."""
    
    def __init__(self, config: DemucsConfig):
        """
        Initialize Demucs engine.
        
        Args:
            config: Engine configuration
        """
        self.config = config
        self.available = self._check_availability()
        
        if self.available:
            logger.info(f"Demucs engine initialized with model: {config.model_name}")
        else:
            logger.warning("Demucs not available - install with: pip install demucs")
    
    def _check_availability(self) -> bool:
        """Check if Demucs is available."""
        try:
            result = subprocess.run(
                ["python", "-c", "import demucs; print('available')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and "available" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def is_available(self) -> bool:
        """Check if Demucs engine is available."""
        return self.available
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available Demucs models.
        
        Returns:
            List of model information dictionaries
        """
        if not self.available:
            return []
        
        models = [
            {
                "name": "htdemucs",
                "description": "Hybrid Transformer Demucs (latest, best quality)",
                "best_for": "General purpose, highest quality",
                "requirements": "High memory, slower processing"
            },
            {
                "name": "htdemucs_ft",
                "description": "Fine-tuned Hybrid Transformer Demucs",
                "best_for": "Music with complex arrangements",
                "requirements": "High memory, slower processing"
            },
            {
                "name": "hdemucs_mmi",
                "description": "Hybrid Demucs with extra training",
                "best_for": "Balanced quality and speed",
                "requirements": "Medium memory"
            },
            {
                "name": "mdx_extra",
                "description": "MDX model with extra features",
                "best_for": "Fast processing with good quality",
                "requirements": "Lower memory, faster"
            }
        ]
        
        # Filter to only available models
        available_models = []
        for model in models:
            if self._is_model_available(model["name"]):
                available_models.append(model)
        
        return available_models
    
    def _is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        try:
            result = subprocess.run(
                ["python", "-c", f"from demucs.pretrained import get_model; get_model('{model_name}')"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    
    def separate_sources(
        self,
        audio: np.ndarray,
        sample_rate: int,
        progress_callback: Optional[callable] = None
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Separate audio sources using Demucs.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate in Hz
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary with separated sources or None if failed
        """
        if not self.available:
            logger.error("Demucs not available")
            return None
        
        try:
            if progress_callback:
                progress_callback(0.1, "Preparing audio for Demucs separation...")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)
                input_path = temp_dir / "input.wav"
                output_dir = temp_dir / "separated"
                
                # Save input audio
                save_audio(audio, input_path, sample_rate, normalize=False)
                
                if progress_callback:
                    progress_callback(0.3, f"Running Demucs separation with {self.config.model_name}...")
                
                # Run Demucs separation
                success = self._run_demucs_separation(input_path, output_dir, progress_callback)
                
                if not success:
                    logger.error("Demucs separation failed")
                    return None
                
                # Load separated sources
                if progress_callback:
                    progress_callback(0.9, "Loading separated sources...")
                
                sources = self._load_separated_sources(output_dir, input_path.stem)
                
                if progress_callback:
                    progress_callback(1.0, "Source separation complete")
                
                return sources
                
        except Exception as e:
            logger.error(f"Error in Demucs source separation: {e}")
            return None
    
    def process(
        self,
        audio: np.ndarray,
        sample_rate: int,
        progress_callback: Optional[callable] = None
    ) -> np.ndarray:
        """
        Process audio with Demucs for noise reduction.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate in Hz
            progress_callback: Optional progress callback
            
        Returns:
            Processed audio signal
        """
        if not self.available:
            raise RuntimeError("Demucs not available")
        
        # Separate sources
        sources = self.separate_sources(audio, sample_rate, progress_callback)
        
        if sources is None:
            raise RuntimeError("Source separation failed")
        
        # Create cleaned audio by combining vocals and reducing other sources
        cleaned_audio = self._create_cleaned_audio(sources, audio.shape)
        
        logger.info("Demucs noise reduction completed")
        return cleaned_audio
    
    def _run_demucs_separation(
        self,
        input_path: Path,
        output_dir: Path,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """Run Demucs separation command."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                "python", "-m", "demucs.separate",
                "--model", self.config.model_name,
                "--device", self.config.device,
                "-o", str(output_dir),
                "--float32",  # Use float32 for better compatibility
                "--two-stems", "vocals"  # Separate into vocals and accompaniment
            ]
            
            if self.config.segment_length is not None:
                cmd.extend(["--segment", str(self.config.segment_length)])
            
            if self.config.overlap > 0:
                cmd.extend(["--overlap", str(self.config.overlap)])
            
            if self.config.jobs > 1:
                cmd.extend(["--jobs", str(self.config.jobs)])
            
            cmd.append(str(input_path))
            
            logger.info(f"Running Demucs: {' '.join(cmd)}")
            
            # Run with progress monitoring
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if process.returncode != 0:
                logger.error(f"Demucs separation failed: {process.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Demucs separation timed out")
            return False
        except Exception as e:
            logger.error(f"Error running Demucs separation: {e}")
            return False
    
    def _load_separated_sources(
        self, 
        output_dir: Path, 
        input_name: str
    ) -> Dict[str, np.ndarray]:
        """Load separated audio sources from Demucs output."""
        sources = {}
        
        # Demucs creates a subdirectory with the model name
        model_dir = output_dir / self.config.model_name / input_name
        
        if not model_dir.exists():
            logger.error(f"Demucs output directory not found: {model_dir}")
            return sources
        
        # Load available source files
        source_files = {
            "vocals": "vocals.wav",
            "no_vocals": "no_vocals.wav",
            "drums": "drums.wav",
            "bass": "bass.wav",
            "other": "other.wav"
        }
        
        for source_name, filename in source_files.items():
            source_path = model_dir / filename
            if source_path.exists():
                result = load_audio(source_path)
                if result is not None:
                    audio, _ = result
                    sources[source_name] = audio
                    logger.debug(f"Loaded {source_name} source: {audio.shape}")
        
        return sources
    
    def _create_cleaned_audio(
        self, 
        sources: Dict[str, np.ndarray], 
        original_shape: tuple
    ) -> np.ndarray:
        """Create cleaned audio from separated sources."""
        # Start with vocals (if available)
        if "vocals" in sources:
            cleaned = sources["vocals"].copy()
        else:
            # Fallback: use original shape filled with zeros
            cleaned = np.zeros(original_shape)
        
        # Apply noise reduction by mixing in reduced accompaniment
        noise_reduction = self.config.noise_reduction_strength
        
        if "no_vocals" in sources and noise_reduction < 1.0:
            # Mix back some of the accompaniment with reduced volume
            accompaniment = sources["no_vocals"]
            mix_factor = 1.0 - noise_reduction
            
            # Ensure same length
            min_len = min(len(cleaned), len(accompaniment))
            cleaned[:min_len] += mix_factor * accompaniment[:min_len]
        
        # If we have individual instrument tracks, apply selective reduction
        instruments = ["drums", "bass", "other"]
        for instrument in instruments:
            if instrument in sources and noise_reduction < 1.0:
                instrument_audio = sources[instrument]
                
                # Reduce instrument volume based on noise reduction strength
                reduction_factor = 0.3 * (1.0 - noise_reduction)  # Max 30% volume
                min_len = min(len(cleaned), len(instrument_audio))
                cleaned[:min_len] += reduction_factor * instrument_audio[:min_len]
        
        return cleaned
    
    def process_file(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Process audio file directly with Demucs.
        
        Args:
            input_path: Input audio file
            output_path: Output audio file
            progress_callback: Optional progress callback
            
        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            logger.error("Demucs not available")
            return False
        
        try:
            # Load audio
            if progress_callback:
                progress_callback(0.1, "Loading audio file...")
            
            result = load_audio(input_path)
            if result is None:
                logger.error(f"Failed to load audio: {input_path}")
                return False
            
            audio, sample_rate = result
            
            # Process with Demucs
            processed = self.process(audio, sample_rate, progress_callback)
            
            # Save processed audio
            if progress_callback:
                progress_callback(0.95, "Saving processed audio...")
            
            success = save_audio(processed, output_path, sample_rate)
            
            if success and progress_callback:
                progress_callback(1.0, "File processing complete")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing file with Demucs: {e}")
            return False
    
    def estimate_processing_time(self, duration_seconds: float) -> float:
        """
        Estimate processing time for given audio duration.
        
        Args:
            duration_seconds: Audio duration in seconds
            
        Returns:
            Estimated processing time in seconds
        """
        # Demucs processing time varies greatly by model and hardware
        model_multipliers = {
            "htdemucs": 2.0,      # Slowest but best quality
            "htdemucs_ft": 2.5,   # Even slower
            "hdemucs_mmi": 1.5,   # Moderate speed
            "mdx_extra": 0.8      # Fastest
        }
        
        base_multiplier = model_multipliers.get(self.config.model_name, 1.5)
        
        # Adjust for device
        if self.config.device == "cuda":
            base_multiplier *= 0.3  # GPU is much faster
        elif self.config.device == "mps":
            base_multiplier *= 0.5  # Apple Silicon is faster
        
        return duration_seconds * base_multiplier