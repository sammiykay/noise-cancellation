"""RNNoise-based noise reduction engine using FFmpeg's arnndn filter."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np

from utils.logging_setup import get_logger
from utils.paths import get_temp_path
from core.media import save_audio, load_audio

logger = get_logger("rnnoise")


class RNNoiseConfig:
    """Configuration for RNNoise noise reduction."""
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        mix_factor: float = 1.0,
        sample_rate: int = 48000
    ):
        """
        Initialize RNNoise configuration.
        
        Args:
            model_path: Path to RNNoise model file (.rnnn)
            mix_factor: Mix factor between original and processed audio (0.0 to 1.0)
            sample_rate: Target sample rate for processing (RNNoise works best at 48kHz)
        """
        self.model_path = model_path
        self.mix_factor = max(0.0, min(1.0, mix_factor))
        self.sample_rate = sample_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'model_path': str(self.model_path) if self.model_path else None,
            'mix_factor': self.mix_factor,
            'sample_rate': self.sample_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RNNoiseConfig':
        """Create configuration from dictionary."""
        model_path = Path(data['model_path']) if data.get('model_path') else None
        return cls(
            model_path=model_path,
            mix_factor=data.get('mix_factor', 1.0),
            sample_rate=data.get('sample_rate', 48000)
        )


class RNNoiseEngine:
    """RNNoise noise reduction engine using FFmpeg."""
    
    def __init__(self, config: RNNoiseConfig):
        """
        Initialize RNNoise engine.
        
        Args:
            config: Engine configuration
        """
        self.config = config
        self._validate_setup()
    
    def _validate_setup(self) -> None:
        """Validate RNNoise setup and model availability."""
        # Check if FFmpeg supports arnndn filter
        try:
            result = subprocess.run(
                ["ffmpeg", "-filters"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "arnndn" not in result.stdout:
                raise RuntimeError("FFmpeg does not support arnndn filter. Please install FFmpeg with RNNoise support.")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg validation timed out")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found in system PATH")
        
        logger.info("RNNoise engine validation successful")
    
    def get_available_models(self, models_dir: Path = Path("models")) -> List[Dict[str, Any]]:
        """
        Get list of available RNNoise models.
        
        Args:
            models_dir: Directory containing model files
            
        Returns:
            List of model information dictionaries
        """
        models = []
        
        if not models_dir.exists():
            logger.warning(f"Models directory not found: {models_dir}")
            return models
        
        # Standard RNNoise models
        standard_models = {
            "bd.rnnn": {
                "name": "Broadband (General Purpose)",
                "description": "General purpose noise reduction model",
                "best_for": "Mixed content, speech, music"
            },
            "cb.rnnn": {
                "name": "Cassette Tape",
                "description": "Optimized for cassette tape noise",
                "best_for": "Tape hiss, analog noise"
            },
            "mp.rnnn": {
                "name": "Music Performance",
                "description": "Optimized for musical performances",
                "best_for": "Live music, concerts, performances"
            },
            "sh.rnnn": {
                "name": "Speech Heavy",
                "description": "Optimized for speech content",
                "best_for": "Podcasts, interviews, voice recordings"
            }
        }
        
        for model_file, info in standard_models.items():
            model_path = models_dir / model_file
            if model_path.exists():
                models.append({
                    "path": model_path,
                    "filename": model_file,
                    **info
                })
        
        # Check for custom models
        for model_file in models_dir.glob("*.rnnn"):
            if model_file.name not in standard_models:
                models.append({
                    "path": model_file,
                    "filename": model_file.name,
                    "name": model_file.stem.replace("_", " ").title(),
                    "description": "Custom RNNoise model",
                    "best_for": "Custom application"
                })
        
        logger.info(f"Found {len(models)} available RNNoise models")
        return models
    
    def set_model(self, model_path: Path) -> None:
        """
        Set the RNNoise model to use.
        
        Args:
            model_path: Path to model file
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        self.config.model_path = model_path
        logger.info(f"RNNoise model set to: {model_path}")
    
    def process(
        self,
        audio: np.ndarray,
        sample_rate: int,
        progress_callback: Optional[callable] = None
    ) -> np.ndarray:
        """
        Process audio with RNNoise.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate in Hz
            progress_callback: Optional progress callback function
            
        Returns:
            Processed audio signal
        """
        if self.config.model_path is None:
            raise RuntimeError("No RNNoise model specified")
        
        try:
            if progress_callback:
                progress_callback(0.1, "Preparing audio for RNNoise processing...")
            
            # Create temporary files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)
                input_path = temp_dir / "input.wav"
                output_path = temp_dir / "output.wav"
                
                # Save input audio
                if progress_callback:
                    progress_callback(0.2, "Saving temporary audio file...")
                
                save_audio(audio, input_path, sample_rate, normalize=False)
                
                # Process with FFmpeg + RNNoise
                if progress_callback:
                    progress_callback(0.4, "Processing with RNNoise...")
                
                success = self._process_with_ffmpeg(
                    input_path, output_path, progress_callback
                )
                
                if not success:
                    raise RuntimeError("RNNoise processing failed")
                
                # Load processed audio
                if progress_callback:
                    progress_callback(0.9, "Loading processed audio...")
                
                result = load_audio(output_path)
                if result is None:
                    raise RuntimeError("Failed to load processed audio")
                
                processed_audio, _ = result
                
                # Apply mix factor if not 1.0
                if self.config.mix_factor < 1.0:
                    if progress_callback:
                        progress_callback(0.95, "Applying mix factor...")
                    
                    # Ensure same length
                    min_len = min(len(audio), len(processed_audio))
                    original = audio[:min_len]
                    processed = processed_audio[:min_len]
                    
                    # Mix original and processed
                    processed_audio = (
                        self.config.mix_factor * processed + 
                        (1.0 - self.config.mix_factor) * original
                    )
                
                if progress_callback:
                    progress_callback(1.0, "RNNoise processing complete")
                
                logger.info("RNNoise processing completed successfully")
                return processed_audio
                
        except Exception as e:
            logger.error(f"Error in RNNoise processing: {e}")
            raise
    
    def _process_with_ffmpeg(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Process audio file with FFmpeg + RNNoise.
        
        Args:
            input_path: Input audio file
            output_path: Output audio file
            progress_callback: Optional progress callback
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build FFmpeg command
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-af", f"arnndn=m={self.config.model_path}",
                "-ar", str(self.config.sample_rate),
                "-c:a", "pcm_s16le",
                str(output_path)
            ]
            
            logger.info(f"Running RNNoise command: {' '.join(cmd)}")
            
            # Run FFmpeg
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if process.returncode != 0:
                logger.error(f"FFmpeg RNNoise processing failed: {process.stderr}")
                return False
            
            if not output_path.exists():
                logger.error(f"Output file not created: {output_path}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("RNNoise processing timed out")
            return False
        except Exception as e:
            logger.error(f"Error in FFmpeg RNNoise processing: {e}")
            return False
    
    def process_file(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Process audio file directly with RNNoise.
        
        Args:
            input_path: Input audio file
            output_path: Output audio file
            progress_callback: Optional progress callback
            
        Returns:
            True if successful, False otherwise
        """
        if self.config.model_path is None:
            logger.error("No RNNoise model specified")
            return False
        
        try:
            if progress_callback:
                progress_callback(0.1, "Starting RNNoise file processing...")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Process directly with FFmpeg
            success = self._process_with_ffmpeg(
                input_path, output_path, progress_callback
            )
            
            if success and progress_callback:
                progress_callback(1.0, "File processing complete")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing file with RNNoise: {e}")
            return False
    
    def estimate_processing_time(self, duration_seconds: float) -> float:
        """
        Estimate processing time for given audio duration.
        
        Args:
            duration_seconds: Audio duration in seconds
            
        Returns:
            Estimated processing time in seconds
        """
        # RNNoise typically processes at 10-20x real-time depending on system
        # We'll estimate conservatively at 5x real-time
        return duration_seconds / 5.0
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently selected model.
        
        Returns:
            Model information dictionary or None
        """
        if self.config.model_path is None:
            return None
        
        models = self.get_available_models(self.config.model_path.parent)
        
        for model in models:
            if model["path"] == self.config.model_path:
                return model
        
        # Return basic info for unknown models
        return {
            "path": self.config.model_path,
            "filename": self.config.model_path.name,
            "name": self.config.model_path.stem.replace("_", " ").title(),
            "description": "RNNoise model",
            "best_for": "Noise reduction"
        }