"""Media file handling and FFmpeg integration utilities."""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import json
import soundfile as sf
import numpy as np

from utils.logging_setup import get_logger
from utils.paths import get_temp_path, get_unique_path, is_audio_file

logger = get_logger("media")


class MediaInfo:
    """Container for media file information."""
    
    def __init__(self, path: Path):
        self.path = path
        self.duration: Optional[float] = None
        self.sample_rate: Optional[int] = None
        self.channels: Optional[int] = None
        self.bit_depth: Optional[int] = None
        self.codec: Optional[str] = None
        self.format: Optional[str] = None
        self.has_video: bool = False
        self.has_audio: bool = False
        self.metadata: Dict = {}
    
    def __str__(self) -> str:
        return (f"MediaInfo({self.path.name}: "
                f"{self.duration:.2f}s, {self.sample_rate}Hz, "
                f"{self.channels}ch, {self.codec})")


def get_media_info(file_path: Path) -> Optional[MediaInfo]:
    """
    Extract media file information using FFprobe.
    
    Args:
        file_path: Path to media file
        
    Returns:
        MediaInfo object or None if failed
    """
    try:
        # Use FFprobe to get media information
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"FFprobe failed for {file_path}: {result.stderr}")
            return None
        
        data = json.loads(result.stdout)
        info = MediaInfo(file_path)
        
        # Extract format information
        if "format" in data:
            format_info = data["format"]
            info.duration = float(format_info.get("duration", 0))
            info.format = format_info.get("format_name", "")
            info.metadata = format_info.get("tags", {})
        
        # Extract stream information
        if "streams" in data:
            for stream in data["streams"]:
                codec_type = stream.get("codec_type", "")
                
                if codec_type == "audio":
                    info.has_audio = True
                    info.sample_rate = int(stream.get("sample_rate", 0))
                    info.channels = int(stream.get("channels", 0))
                    info.codec = stream.get("codec_name", "")
                    
                    # Try to get bit depth
                    bits_per_sample = stream.get("bits_per_sample")
                    if bits_per_sample:
                        info.bit_depth = int(bits_per_sample)
                    
                elif codec_type == "video":
                    info.has_video = True
        
        logger.debug(f"Media info extracted: {info}")
        return info
        
    except subprocess.TimeoutExpired:
        logger.error(f"FFprobe timeout for {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse FFprobe output for {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting media info for {file_path}: {e}")
        return None


def extract_audio(
    input_path: Path,
    output_path: Optional[Path] = None,
    sample_rate: Optional[int] = None,
    channels: Optional[int] = None,
    start_time: Optional[float] = None,
    duration: Optional[float] = None
) -> Optional[Path]:
    """
    Extract audio track from media file.
    
    Args:
        input_path: Source media file
        output_path: Output audio file (optional, will generate if None)
        sample_rate: Target sample rate (optional)
        channels: Target channel count (optional)
        start_time: Start time in seconds (optional)
        duration: Duration in seconds (optional)
        
    Returns:
        Path to extracted audio file or None if failed
    """
    if output_path is None:
        output_path = get_temp_path(input_path, "_audio").with_suffix(".wav")
    
    try:
        cmd = ["ffmpeg", "-y", "-i", str(input_path)]
        
        # Add time range if specified
        if start_time is not None:
            cmd.extend(["-ss", str(start_time)])
        if duration is not None:
            cmd.extend(["-t", str(duration)])
        
        # Audio processing options
        cmd.extend(["-vn"])  # No video
        
        if sample_rate is not None:
            cmd.extend(["-ar", str(sample_rate)])
        if channels is not None:
            cmd.extend(["-ac", str(channels)])
        
        # High quality PCM output
        cmd.extend(["-c:a", "pcm_s16le", str(output_path)])
        
        logger.info(f"Extracting audio: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg audio extraction failed: {result.stderr}")
            return None
        
        if not output_path.exists():
            logger.error(f"Output file not created: {output_path}")
            return None
        
        logger.info(f"Audio extracted successfully to {output_path}")
        return output_path
        
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg audio extraction timed out")
        return None
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return None


def load_audio(
    file_path: Path,
    sample_rate: Optional[int] = None,
    mono: bool = False,
    start_time: Optional[float] = None,
    duration: Optional[float] = None
) -> Optional[Tuple[np.ndarray, int]]:
    """
    Load audio file into numpy array.
    
    Args:
        file_path: Path to audio file
        sample_rate: Target sample rate (None to preserve original)
        mono: Convert to mono
        start_time: Start time in seconds
        duration: Duration in seconds
        
    Returns:
        Tuple of (audio_data, sample_rate) or None if failed
    """
    try:
        # First try direct loading for audio files
        if is_audio_file(file_path):
            try:
                # Calculate frame parameters if time range specified
                start_frame = None
                num_frames = None
                
                if start_time is not None or duration is not None:
                    with sf.SoundFile(file_path) as f:
                        original_sr = f.samplerate
                        
                        if start_time is not None:
                            start_frame = int(start_time * original_sr)
                        if duration is not None:
                            num_frames = int(duration * original_sr)
                
                # Load audio
                audio, sr = sf.read(
                    file_path,
                    start=start_frame,
                    frames=num_frames,
                    dtype=np.float32
                )
                
                # Convert to mono if requested
                if mono and len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)
                
                # Resample if different sample rate requested
                if sample_rate is not None and sr != sample_rate:
                    import librosa
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=sample_rate)
                    sr = sample_rate
                
                logger.debug(f"Audio loaded directly: shape={audio.shape}, sr={sr}")
                return audio, sr
                
            except Exception as direct_error:
                logger.warning(f"Direct audio loading failed, trying FFmpeg: {direct_error}")
        
        # For video files or failed audio files, extract audio using FFmpeg
        logger.info(f"Extracting audio from {file_path} using FFmpeg...")
        
        # Extract audio to temporary file
        temp_audio_path = extract_audio(
            file_path,
            sample_rate=sample_rate,
            start_time=start_time,
            duration=duration
        )
        
        if temp_audio_path is None:
            logger.error(f"FFmpeg audio extraction failed for {file_path}")
            return None
        
        try:
            # Load the extracted audio
            audio, sr = sf.read(temp_audio_path, dtype=np.float32)
            
            # Convert to mono if requested
            if mono and len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            logger.debug(f"Audio loaded from extracted file: shape={audio.shape}, sr={sr}")
            return audio, sr
            
        finally:
            # Clean up temporary file
            if temp_audio_path.exists():
                temp_audio_path.unlink()
        
    except Exception as e:
        logger.error(f"Error loading audio from {file_path}: {e}")
        return None


def save_audio(
    audio: np.ndarray,
    output_path: Path,
    sample_rate: int,
    bit_depth: int = 16,
    normalize: bool = True
) -> bool:
    """
    Save audio array to file.
    
    Args:
        audio: Audio data array
        output_path: Output file path
        sample_rate: Sample rate in Hz
        bit_depth: Bit depth (16, 24, 32)
        normalize: Whether to normalize audio
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Normalize audio if requested
        if normalize and audio.size > 0:
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val * 0.95  # Leave some headroom
        
        # Determine format based on bit depth
        if bit_depth == 16:
            subtype = 'PCM_16'
        elif bit_depth == 24:
            subtype = 'PCM_24'
        elif bit_depth == 32:
            subtype = 'PCM_32'
        else:
            logger.warning(f"Unsupported bit depth {bit_depth}, using 16-bit")
            subtype = 'PCM_16'
        
        # Write audio file
        sf.write(
            output_path,
            audio,
            sample_rate,
            subtype=subtype
        )
        
        logger.info(f"Audio saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving audio to {output_path}: {e}")
        return False


def remux_audio_video(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    preserve_metadata: bool = True
) -> bool:
    """
    Replace audio track in video file.
    
    Args:
        video_path: Original video file
        audio_path: New audio file
        output_path: Output video file
        preserve_metadata: Whether to preserve metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",  # Copy video stream
            "-c:a", "aac",   # Encode audio as AAC
            "-map", "0:v:0", # Map video from first input
            "-map", "1:a:0", # Map audio from second input
            "-shortest"      # Match shortest stream
        ]
        
        # Copy subtitles and other streams if present
        cmd.extend(["-map", "0:s?", "-c:s", "copy"])
        
        # Preserve metadata
        if preserve_metadata:
            cmd.extend(["-map_metadata", "0"])
        
        cmd.append(str(output_path))
        
        logger.info(f"Remuxing video: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg remux failed: {result.stderr}")
            return False
        
        if not output_path.exists():
            logger.error(f"Output video not created: {output_path}")
            return False
        
        logger.info(f"Video remuxed successfully: {output_path}")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg remux timed out")
        return False
    except Exception as e:
        logger.error(f"Error remuxing video: {e}")
        return False


def convert_audio_format(
    input_path: Path,
    output_path: Path,
    format: str = "wav",
    sample_rate: Optional[int] = None,
    channels: Optional[int] = None,
    bitrate: Optional[str] = None
) -> bool:
    """
    Convert audio to different format.
    
    Args:
        input_path: Source audio file
        output_path: Target audio file
        format: Target format (wav, mp3, aac, flac)
        sample_rate: Target sample rate
        channels: Target channel count
        bitrate: Target bitrate (for compressed formats)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = ["ffmpeg", "-y", "-i", str(input_path)]
        
        # Audio format specific settings
        if format.lower() == "mp3":
            cmd.extend(["-c:a", "libmp3lame"])
            if bitrate:
                cmd.extend(["-b:a", bitrate])
            else:
                cmd.extend(["-q:a", "0"])  # Variable bitrate, high quality
                
        elif format.lower() == "aac":
            cmd.extend(["-c:a", "aac"])
            if bitrate:
                cmd.extend(["-b:a", bitrate])
            else:
                cmd.extend(["-b:a", "192k"])
                
        elif format.lower() == "flac":
            cmd.extend(["-c:a", "flac"])
            
        else:  # WAV or other PCM
            cmd.extend(["-c:a", "pcm_s16le"])
        
        # Set sample rate and channels if specified
        if sample_rate:
            cmd.extend(["-ar", str(sample_rate)])
        if channels:
            cmd.extend(["-ac", str(channels)])
        
        cmd.append(str(output_path))
        
        logger.info(f"Converting audio format: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg conversion failed: {result.stderr}")
            return False
        
        logger.info(f"Audio converted successfully: {output_path}")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg conversion timed out")
        return False
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        return False


def get_audio_duration(file_path: Path) -> Optional[float]:
    """
    Get duration of audio/video file in seconds.
    
    Args:
        file_path: Path to media file
        
    Returns:
        Duration in seconds or None if failed
    """
    info = get_media_info(file_path)
    return info.duration if info else None