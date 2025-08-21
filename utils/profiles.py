"""Noise profile detection and management utilities."""

import numpy as np
import librosa
from typing import Tuple, Optional, List
from pathlib import Path

from utils.logging_setup import get_logger

logger = get_logger("profiles")


class NoiseProfile:
    """Container for noise profile data and metadata."""
    
    def __init__(
        self,
        power_spectrum: np.ndarray,
        frequencies: np.ndarray,
        duration: float,
        source_type: str = "auto",
        confidence: float = 0.0
    ):
        """
        Initialize noise profile.
        
        Args:
            power_spectrum: Power spectral density of noise
            frequencies: Frequency bins
            duration: Duration of noise sample in seconds
            source_type: How profile was obtained ('auto', 'manual', 'file')
            confidence: Confidence score (0.0 to 1.0)
        """
        self.power_spectrum = power_spectrum
        self.frequencies = frequencies
        self.duration = duration
        self.source_type = source_type
        self.confidence = confidence
        
    def save(self, path: Path) -> None:
        """Save noise profile to file."""
        np.savez(
            path,
            power_spectrum=self.power_spectrum,
            frequencies=self.frequencies,
            duration=self.duration,
            source_type=self.source_type,
            confidence=self.confidence
        )
        logger.info(f"Noise profile saved to {path}")
    
    @classmethod
    def load(cls, path: Path) -> 'NoiseProfile':
        """Load noise profile from file."""
        data = np.load(path)
        return cls(
            power_spectrum=data['power_spectrum'],
            frequencies=data['frequencies'],
            duration=float(data['duration']),
            source_type=str(data.get('source_type', 'file')),
            confidence=float(data.get('confidence', 0.0))
        )


def detect_silence_regions(
    audio: np.ndarray,
    sample_rate: int,
    min_duration: float = 0.5,
    threshold_db: float = -40.0
) -> List[Tuple[float, float]]:
    """
    Detect silent regions in audio for noise profile extraction.
    
    Args:
        audio: Audio signal
        sample_rate: Sample rate in Hz
        min_duration: Minimum silence duration in seconds
        threshold_db: Silence threshold in dB below peak
        
    Returns:
        List of (start_time, end_time) tuples in seconds
    """
    # Calculate frame-wise energy
    hop_length = 512
    frame_length = 2048
    
    # Convert to mono if stereo
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)
    
    # Calculate RMS energy
    rms = librosa.feature.rms(
        y=audio,
        frame_length=frame_length,
        hop_length=hop_length
    )[0]
    
    # Convert to dB
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    
    # Find silent frames
    silent_frames = rms_db < threshold_db
    
    # Convert frame indices to time
    times = librosa.frames_to_time(
        np.arange(len(rms_db)),
        sr=sample_rate,
        hop_length=hop_length
    )
    
    # Find continuous silent regions
    regions = []
    start_time = None
    
    for i, is_silent in enumerate(silent_frames):
        if is_silent and start_time is None:
            start_time = times[i]
        elif not is_silent and start_time is not None:
            duration = times[i] - start_time
            if duration >= min_duration:
                regions.append((start_time, times[i]))
            start_time = None
    
    # Handle case where silence extends to end
    if start_time is not None:
        duration = times[-1] - start_time
        if duration >= min_duration:
            regions.append((start_time, times[-1]))
    
    logger.info(f"Found {len(regions)} silence regions")
    return regions


def extract_noise_profile_auto(
    audio: np.ndarray,
    sample_rate: int,
    n_fft: int = 2048,
    hop_length: int = 512
) -> Optional[NoiseProfile]:
    """
    Automatically extract noise profile from leading/trailing silence.
    
    Args:
        audio: Audio signal
        sample_rate: Sample rate in Hz
        n_fft: FFT window size
        hop_length: Hop length for STFT
        
    Returns:
        NoiseProfile if successful, None otherwise
    """
    # Find silence regions
    silence_regions = detect_silence_regions(audio, sample_rate)
    
    if not silence_regions:
        logger.warning("No silence regions found for automatic noise profiling")
        return None
    
    # Use the longest silence region
    longest_region = max(silence_regions, key=lambda x: x[1] - x[0])
    start_time, end_time = longest_region
    
    logger.info(f"Using silence region {start_time:.2f}s - {end_time:.2f}s for noise profile")
    
    # Extract noise segment
    start_sample = int(start_time * sample_rate)
    end_sample = int(end_time * sample_rate)
    noise_segment = audio[start_sample:end_sample]
    
    return extract_noise_profile_from_segment(
        noise_segment, sample_rate, n_fft, hop_length, "auto"
    )


def extract_noise_profile_manual(
    audio: np.ndarray,
    sample_rate: int,
    start_time: float,
    end_time: float,
    n_fft: int = 2048,
    hop_length: int = 512
) -> Optional[NoiseProfile]:
    """
    Extract noise profile from manually selected time range.
    
    Args:
        audio: Audio signal
        sample_rate: Sample rate in Hz
        start_time: Start time in seconds
        end_time: End time in seconds
        n_fft: FFT window size
        hop_length: Hop length for STFT
        
    Returns:
        NoiseProfile if successful, None otherwise
    """
    # Validate time range
    audio_duration = len(audio) / sample_rate
    if start_time < 0 or end_time > audio_duration or start_time >= end_time:
        logger.error(f"Invalid time range: {start_time:.2f}s - {end_time:.2f}s")
        return None
    
    # Extract noise segment
    start_sample = int(start_time * sample_rate)
    end_sample = int(end_time * sample_rate)
    noise_segment = audio[start_sample:end_sample]
    
    logger.info(f"Extracting noise profile from {start_time:.2f}s - {end_time:.2f}s")
    
    return extract_noise_profile_from_segment(
        noise_segment, sample_rate, n_fft, hop_length, "manual"
    )


def extract_noise_profile_from_segment(
    noise_segment: np.ndarray,
    sample_rate: int,
    n_fft: int = 2048,
    hop_length: int = 512,
    source_type: str = "manual"
) -> Optional[NoiseProfile]:
    """
    Extract noise profile from audio segment.
    
    Args:
        noise_segment: Audio segment containing noise
        sample_rate: Sample rate in Hz
        n_fft: FFT window size
        hop_length: Hop length for STFT
        source_type: Source type for profile
        
    Returns:
        NoiseProfile if successful, None otherwise
    """
    if len(noise_segment) < n_fft:
        logger.error("Noise segment too short for analysis")
        return None
    
    # Convert to mono if stereo
    if len(noise_segment.shape) > 1:
        noise_segment = np.mean(noise_segment, axis=1)
    
    # Compute STFT
    stft = librosa.stft(
        noise_segment,
        n_fft=n_fft,
        hop_length=hop_length,
        window='hann'
    )
    
    # Calculate power spectrum (median across time)
    power_spectrum = np.median(np.abs(stft) ** 2, axis=1)
    
    # Get frequency bins
    frequencies = librosa.fft_frequencies(sr=sample_rate, n_fft=n_fft)
    
    # Calculate duration
    duration = len(noise_segment) / sample_rate
    
    # Estimate confidence based on spectral stability
    spectral_variance = np.var(np.abs(stft) ** 2, axis=1)
    confidence = 1.0 - np.mean(spectral_variance / (power_spectrum + 1e-8))
    confidence = np.clip(confidence, 0.0, 1.0)
    
    profile = NoiseProfile(
        power_spectrum=power_spectrum,
        frequencies=frequencies,
        duration=duration,
        source_type=source_type,
        confidence=confidence
    )
    
    logger.info(f"Noise profile extracted: duration={duration:.2f}s, confidence={confidence:.3f}")
    return profile


def estimate_snr(
    audio: np.ndarray,
    sample_rate: int,
    noise_profile: Optional[NoiseProfile] = None
) -> float:
    """
    Estimate signal-to-noise ratio of audio.
    
    Args:
        audio: Audio signal
        sample_rate: Sample rate in Hz
        noise_profile: Optional noise profile for more accurate estimation
        
    Returns:
        Estimated SNR in dB
    """
    # Convert to mono if stereo
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)
    
    # Calculate RMS of entire signal
    signal_rms = np.sqrt(np.mean(audio ** 2))
    
    if noise_profile is not None:
        # Use noise profile for noise estimation
        noise_power = np.mean(noise_profile.power_spectrum)
        noise_rms = np.sqrt(noise_power)
    else:
        # Estimate noise from quietest regions
        silence_regions = detect_silence_regions(audio, sample_rate)
        if silence_regions:
            # Use first silence region as noise estimate
            start_time, end_time = silence_regions[0]
            start_sample = int(start_time * sample_rate)
            end_sample = int(end_time * sample_rate)
            noise_segment = audio[start_sample:end_sample]
            noise_rms = np.sqrt(np.mean(noise_segment ** 2))
        else:
            # Fallback: use bottom 10th percentile as noise
            sorted_samples = np.sort(np.abs(audio))
            noise_rms = np.mean(sorted_samples[:len(sorted_samples)//10])
    
    # Calculate SNR
    if noise_rms > 0:
        snr_db = 20 * np.log10(signal_rms / noise_rms)
    else:
        snr_db = float('inf')
    
    logger.debug(f"Estimated SNR: {snr_db:.2f} dB")
    return snr_db