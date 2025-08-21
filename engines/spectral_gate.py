"""Spectral gating noise reduction engine using librosa and noisereduce."""

import numpy as np
import librosa
import noisereduce as nr
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

from utils.logging_setup import get_logger
from utils.profiles import NoiseProfile, extract_noise_profile_auto, extract_noise_profile_manual

logger = get_logger("spectral_gate")


class SpectralGateConfig:
    """Configuration for spectral gating noise reduction."""
    
    def __init__(
        self,
        reduction_db: float = 20.0,
        time_smoothing: float = 0.1,
        frequency_smoothing: float = 0.1,
        stationary: bool = True,
        prop_decrease: float = 1.0,
        use_noise_profile: bool = True,
        noise_start_time: Optional[float] = None,
        noise_end_time: Optional[float] = None
    ):
        """
        Initialize spectral gate configuration.
        
        Args:
            reduction_db: Amount of noise reduction in dB (higher = more aggressive)
            time_smoothing: Temporal smoothing factor (0.0 to 1.0)
            frequency_smoothing: Spectral smoothing factor (0.0 to 1.0)
            stationary: Whether noise is stationary or non-stationary
            prop_decrease: Proportion of noise to reduce (0.0 to 1.0)
            use_noise_profile: Whether to use noise profile estimation
            noise_start_time: Manual noise profile start time (seconds)
            noise_end_time: Manual noise profile end time (seconds)
        """
        self.reduction_db = max(0.0, min(60.0, reduction_db))
        self.time_smoothing = max(0.0, min(1.0, time_smoothing))
        self.frequency_smoothing = max(0.0, min(1.0, frequency_smoothing))
        self.stationary = stationary
        self.prop_decrease = max(0.0, min(1.0, prop_decrease))
        self.use_noise_profile = use_noise_profile
        self.noise_start_time = noise_start_time
        self.noise_end_time = noise_end_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'reduction_db': self.reduction_db,
            'time_smoothing': self.time_smoothing,
            'frequency_smoothing': self.frequency_smoothing,
            'stationary': self.stationary,
            'prop_decrease': self.prop_decrease,
            'use_noise_profile': self.use_noise_profile,
            'noise_start_time': self.noise_start_time,
            'noise_end_time': self.noise_end_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpectralGateConfig':
        """Create configuration from dictionary."""
        return cls(**data)


class SpectralGateEngine:
    """Spectral gating noise reduction engine."""
    
    def __init__(self, config: SpectralGateConfig):
        """
        Initialize spectral gate engine.
        
        Args:
            config: Engine configuration
        """
        self.config = config
        self.noise_profile: Optional[NoiseProfile] = None
    
    def set_noise_profile(self, profile: NoiseProfile) -> None:
        """Set noise profile for reduction."""
        self.noise_profile = profile
        logger.info(f"Noise profile set: {profile.source_type}, confidence={profile.confidence:.3f}")
    
    def create_noise_profile(
        self,
        audio: np.ndarray,
        sample_rate: int,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> Optional[NoiseProfile]:
        """
        Create noise profile from audio.
        
        Args:
            audio: Audio signal
            sample_rate: Sample rate in Hz
            start_time: Manual start time for noise region
            end_time: Manual end time for noise region
            
        Returns:
            NoiseProfile if successful, None otherwise
        """
        if start_time is not None and end_time is not None:
            # Manual noise profile
            profile = extract_noise_profile_manual(
                audio, sample_rate, start_time, end_time
            )
        else:
            # Automatic noise profile
            profile = extract_noise_profile_auto(audio, sample_rate)
        
        if profile:
            self.set_noise_profile(profile)
        
        return profile
    
    def reduce_noise_basic(
        self,
        audio: np.ndarray,
        sample_rate: int,
        progress_callback: Optional[callable] = None
    ) -> np.ndarray:
        """
        Reduce noise using basic noisereduce algorithm.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate in Hz
            progress_callback: Optional progress callback function
            
        Returns:
            Processed audio signal
        """
        try:
            if progress_callback:
                progress_callback(0.1, "Initializing noise reduction...")
            
            # Convert to mono for processing if stereo
            original_shape = audio.shape
            if len(audio.shape) > 1:
                audio_mono = np.mean(audio, axis=1)
            else:
                audio_mono = audio.copy()
            
            if progress_callback:
                progress_callback(0.3, "Analyzing audio spectrum...")
            
            # Use noise profile if available
            if self.config.use_noise_profile and self.noise_profile is not None:
                # Extract noise segment for noisereduce
                noise_sample = self._extract_noise_sample(audio_mono, sample_rate)
                
                if progress_callback:
                    progress_callback(0.5, "Applying spectral gating...")
                
                # Apply noise reduction with profile
                reduced = nr.reduce_noise(
                    y=audio_mono,
                    sr=sample_rate,
                    y_noise=noise_sample,
                    prop_decrease=self.config.prop_decrease,
                    stationary=self.config.stationary,
                    n_grad_freq=2,  # Frequency smoothing
                    n_grad_time=4   # Time smoothing
                )
            else:
                if progress_callback:
                    progress_callback(0.5, "Applying spectral gating...")
                
                # Apply noise reduction without profile
                reduced = nr.reduce_noise(
                    y=audio_mono,
                    sr=sample_rate,
                    prop_decrease=self.config.prop_decrease,
                    stationary=self.config.stationary
                )
            
            if progress_callback:
                progress_callback(0.8, "Finalizing output...")
            
            # Restore original channel structure if needed
            if len(original_shape) > 1:
                reduced = np.column_stack([reduced] * original_shape[1])
            
            # Apply additional smoothing if configured
            if self.config.time_smoothing > 0 or self.config.frequency_smoothing > 0:
                reduced = self._apply_smoothing(reduced, sample_rate)
            
            if progress_callback:
                progress_callback(1.0, "Noise reduction complete")
            
            logger.info("Spectral gating noise reduction completed")
            return reduced
            
        except Exception as e:
            logger.error(f"Error in spectral gating: {e}")
            raise
    
    def reduce_noise_advanced(
        self,
        audio: np.ndarray,
        sample_rate: int,
        progress_callback: Optional[callable] = None
    ) -> np.ndarray:
        """
        Reduce noise using advanced spectral subtraction.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate in Hz
            progress_callback: Optional progress callback function
            
        Returns:
            Processed audio signal
        """
        try:
            if progress_callback:
                progress_callback(0.1, "Initializing advanced processing...")
            
            # STFT parameters
            n_fft = 2048
            hop_length = n_fft // 4
            win_length = n_fft
            
            # Convert to mono for processing
            original_shape = audio.shape
            if len(audio.shape) > 1:
                audio_mono = np.mean(audio, axis=1)
            else:
                audio_mono = audio.copy()
            
            if progress_callback:
                progress_callback(0.3, "Computing STFT...")
            
            # Compute STFT
            stft = librosa.stft(
                audio_mono,
                n_fft=n_fft,
                hop_length=hop_length,
                win_length=win_length,
                window='hann'
            )
            
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            if progress_callback:
                progress_callback(0.5, "Estimating noise spectrum...")
            
            # Estimate noise spectrum
            if self.noise_profile is not None:
                # Use existing noise profile
                noise_spectrum = self.noise_profile.power_spectrum
                # Interpolate to match STFT frequency bins
                freqs_profile = self.noise_profile.frequencies
                freqs_stft = librosa.fft_frequencies(sr=sample_rate, n_fft=n_fft)
                noise_spectrum = np.interp(freqs_stft, freqs_profile, noise_spectrum)
                noise_spectrum = np.sqrt(noise_spectrum)  # Convert power to magnitude
            else:
                # Estimate from quieter frames
                frame_energy = np.sum(magnitude ** 2, axis=0)
                quiet_threshold = np.percentile(frame_energy, 20)
                quiet_frames = magnitude[:, frame_energy <= quiet_threshold]
                
                if quiet_frames.shape[1] > 0:
                    noise_spectrum = np.median(quiet_frames, axis=1)
                else:
                    noise_spectrum = np.median(magnitude, axis=1)
            
            if progress_callback:
                progress_callback(0.7, "Applying spectral subtraction...")
            
            # Apply spectral subtraction
            alpha = self._db_to_ratio(self.config.reduction_db)  # Over-subtraction factor
            beta = 0.1  # Spectral floor factor
            
            # Calculate gain
            gain = 1 - alpha * (noise_spectrum[:, np.newaxis] / (magnitude + 1e-8))
            gain = np.maximum(gain, beta)  # Apply spectral floor
            
            # Apply smoothing
            if self.config.frequency_smoothing > 0:
                for i in range(gain.shape[1]):
                    gain[:, i] = self._smooth_spectrum(gain[:, i], self.config.frequency_smoothing)
            
            if self.config.time_smoothing > 0:
                for i in range(gain.shape[0]):
                    gain[i, :] = self._smooth_temporal(gain[i, :], self.config.time_smoothing)
            
            # Apply gain
            processed_magnitude = magnitude * gain
            
            if progress_callback:
                progress_callback(0.9, "Reconstructing audio...")
            
            # Reconstruct STFT
            processed_stft = processed_magnitude * np.exp(1j * phase)
            
            # Inverse STFT
            processed_audio = librosa.istft(
                processed_stft,
                hop_length=hop_length,
                win_length=win_length,
                window='hann'
            )
            
            # Restore original length
            if len(processed_audio) < len(audio_mono):
                processed_audio = np.pad(
                    processed_audio, 
                    (0, len(audio_mono) - len(processed_audio)),
                    mode='constant'
                )
            elif len(processed_audio) > len(audio_mono):
                processed_audio = processed_audio[:len(audio_mono)]
            
            # Restore stereo if needed
            if len(original_shape) > 1:
                processed_audio = np.column_stack([processed_audio] * original_shape[1])
            
            if progress_callback:
                progress_callback(1.0, "Advanced processing complete")
            
            logger.info("Advanced spectral gating completed")
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error in advanced spectral gating: {e}")
            raise
    
    def process(
        self,
        audio: np.ndarray,
        sample_rate: int,
        progress_callback: Optional[callable] = None
    ) -> np.ndarray:
        """
        Main processing method.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate in Hz
            progress_callback: Optional progress callback function
            
        Returns:
            Processed audio signal
        """
        # Create noise profile if configured and not already set
        if (self.config.use_noise_profile and self.noise_profile is None and
            self.config.noise_start_time is not None and self.config.noise_end_time is not None):
            self.create_noise_profile(
                audio, sample_rate, 
                self.config.noise_start_time, self.config.noise_end_time
            )
        elif self.config.use_noise_profile and self.noise_profile is None:
            self.create_noise_profile(audio, sample_rate)
        
        # Choose processing method based on configuration
        if self.config.reduction_db > 30 or not self.config.stationary:
            return self.reduce_noise_advanced(audio, sample_rate, progress_callback)
        else:
            return self.reduce_noise_basic(audio, sample_rate, progress_callback)
    
    def _extract_noise_sample(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Extract noise sample from audio using noise profile."""
        if self.noise_profile is None:
            return audio[:sample_rate]  # Use first second as fallback
        
        # Use the duration from noise profile to extract similar length
        noise_duration = min(self.noise_profile.duration, 2.0)  # Max 2 seconds
        noise_samples = int(noise_duration * sample_rate)
        
        # Extract from beginning (typically where noise profile was taken)
        return audio[:noise_samples]
    
    def _apply_smoothing(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply additional temporal and spectral smoothing."""
        if len(audio.shape) > 1:
            # Process each channel separately
            smoothed = np.zeros_like(audio)
            for ch in range(audio.shape[1]):
                smoothed[:, ch] = self._apply_smoothing(audio[:, ch], sample_rate)
            return smoothed
        
        # Apply temporal smoothing using moving average
        if self.config.time_smoothing > 0:
            window_size = int(self.config.time_smoothing * sample_rate * 0.01)  # 1% of sample rate
            if window_size > 1:
                kernel = np.ones(window_size) / window_size
                audio = np.convolve(audio, kernel, mode='same')
        
        return audio
    
    def _smooth_spectrum(self, spectrum: np.ndarray, factor: float) -> np.ndarray:
        """Apply frequency domain smoothing."""
        if factor <= 0:
            return spectrum
        
        window_size = max(1, int(len(spectrum) * factor * 0.1))
        kernel = np.ones(window_size) / window_size
        return np.convolve(spectrum, kernel, mode='same')
    
    def _smooth_temporal(self, temporal: np.ndarray, factor: float) -> np.ndarray:
        """Apply temporal smoothing."""
        if factor <= 0:
            return temporal
        
        window_size = max(1, int(len(temporal) * factor * 0.05))
        kernel = np.ones(window_size) / window_size
        return np.convolve(temporal, kernel, mode='same')
    
    def _db_to_ratio(self, db: float) -> float:
        """Convert dB to linear ratio."""
        return 10 ** (db / 20)