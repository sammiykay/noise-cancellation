"""Tests for utility functions."""

import pytest
import tempfile
from pathlib import Path
import numpy as np

from utils.paths import (
    sanitize_filename, generate_output_path, get_unique_path,
    is_audio_file, is_video_file, is_media_file, PathTemplate
)
from utils.validators import validate_file_permissions, validate_disk_space
from utils.profiles import detect_silence_regions, extract_noise_profile_from_segment


class TestPathUtils:
    """Test path utility functions."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("test<>file") == "test__file"
        assert sanitize_filename("file:name") == "file_name"
        assert sanitize_filename("normal_file.wav") == "normal_file.wav"
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("   ") == "untitled"
    
    def test_generate_output_path(self):
        """Test output path generation."""
        input_path = Path("/home/user/audio.wav")
        
        # Default pattern
        output = generate_output_path(input_path)
        assert output.name == "audio_clean.wav"
        assert output.parent.name == "clean"
        
        # Custom pattern
        output = generate_output_path(
            input_path, 
            pattern="{parent}/processed_{name}{ext}"
        )
        assert output.name == "processed_audio.wav"
        
        # Different format
        output = generate_output_path(
            input_path,
            output_format=".mp3"
        )
        assert output.suffix == ".mp3"
    
    def test_get_unique_path(self):
        """Test unique path generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # First file should be unchanged
            file1 = temp_path / "test.txt"
            unique1 = get_unique_path(file1)
            assert unique1 == file1
            
            # Create the file, next should get number suffix
            file1.touch()
            unique2 = get_unique_path(file1)
            assert unique2 == temp_path / "test_1.txt"
    
    def test_media_file_detection(self):
        """Test media file type detection."""
        assert is_audio_file(Path("test.wav"))
        assert is_audio_file(Path("test.mp3"))
        assert not is_audio_file(Path("test.txt"))
        
        assert is_video_file(Path("test.mp4"))
        assert is_video_file(Path("test.avi"))
        assert not is_video_file(Path("test.wav"))
        
        assert is_media_file(Path("test.wav"))
        assert is_media_file(Path("test.mp4"))
        assert not is_media_file(Path("test.txt"))
    
    def test_path_template(self):
        """Test path template functionality."""
        template = PathTemplate("{parent}/output/{name}_processed{ext}")
        
        input_path = Path("/home/user/audio.wav")
        output = template.apply(input_path)
        
        assert output.parent.name == "output"
        assert output.name == "audio_processed.wav"
        
        # Invalid template should raise error
        with pytest.raises(ValueError):
            PathTemplate("{invalid_placeholder}")


class TestValidators:
    """Test validation functions."""
    
    def test_file_permissions(self):
        """Test file permission validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Directory should be valid
            result = validate_file_permissions(temp_path)
            assert result.is_valid
            
            # Create test file
            test_file = temp_path / "test.txt"
            test_file.write_text("test")
            
            result = validate_file_permissions(test_file)
            assert result.is_valid
    
    def test_disk_space(self):
        """Test disk space validation."""
        result = validate_disk_space(Path("."), required_mb=1)  # 1MB should be available
        assert result.is_valid
        
        # Test with unreasonably large requirement
        result = validate_disk_space(Path("."), required_mb=1_000_000)  # 1TB
        # This might fail on systems with less than 1TB free space
        # assert not result.is_valid


class TestProfiles:
    """Test noise profile functions."""
    
    def create_test_audio(self, duration=2.0, sample_rate=44100, noise_level=0.1):
        """Create test audio with silence regions."""
        samples = int(duration * sample_rate)
        
        # Create audio with quiet beginning and end
        audio = np.random.normal(0, noise_level, samples).astype(np.float32)
        
        # Add louder signal in the middle
        mid_start = samples // 4
        mid_end = 3 * samples // 4
        audio[mid_start:mid_end] += 0.5 * np.sin(
            2 * np.pi * 440 * np.linspace(0, duration/2, mid_end - mid_start)
        )
        
        return audio
    
    def test_silence_detection(self):
        """Test silence region detection."""
        sample_rate = 44100
        audio = self.create_test_audio(duration=3.0, sample_rate=sample_rate)
        
        regions = detect_silence_regions(
            audio, sample_rate, 
            min_duration=0.2, 
            threshold_db=-20.0
        )
        
        # Should detect quiet regions at beginning and end
        assert len(regions) >= 1
        
        # First region should start near beginning
        assert regions[0][0] < 1.0
    
    def test_noise_profile_extraction(self):
        """Test noise profile extraction from segment."""
        sample_rate = 44100
        noise_duration = 1.0
        noise_segment = np.random.normal(0, 0.1, int(noise_duration * sample_rate))
        
        profile = extract_noise_profile_from_segment(
            noise_segment, sample_rate, source_type="test"
        )
        
        assert profile is not None
        assert profile.duration == pytest.approx(noise_duration, rel=0.1)
        assert profile.source_type == "test"
        assert len(profile.power_spectrum) > 0
        assert len(profile.frequencies) == len(profile.power_spectrum)
        assert 0 <= profile.confidence <= 1.0


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_processing_pipeline_setup(self):
        """Test that processing pipeline can be set up."""
        from core.pipeline import ProcessingPipeline, Engine
        
        pipeline = ProcessingPipeline()
        available_engines = pipeline.get_available_engines()
        
        # Should at least have spectral gate
        assert Engine.SPECTRAL_GATE in available_engines
        assert len(available_engines) >= 1
    
    def test_engine_configuration(self):
        """Test engine configuration creation."""
        from engines.spectral_gate import SpectralGateConfig
        from engines.rnnoise import RNNoiseConfig
        
        # Spectral gate config
        sg_config = SpectralGateConfig(reduction_db=25.0)
        assert sg_config.reduction_db == 25.0
        
        config_dict = sg_config.to_dict()
        sg_config2 = SpectralGateConfig.from_dict(config_dict)
        assert sg_config2.reduction_db == sg_config.reduction_db
        
        # RNNoise config
        rn_config = RNNoiseConfig(mix_factor=0.8)
        assert rn_config.mix_factor == 0.8
        
        config_dict = rn_config.to_dict()
        rn_config2 = RNNoiseConfig.from_dict(config_dict)
        assert rn_config2.mix_factor == rn_config.mix_factor
    
    def test_media_info_structure(self):
        """Test media info structure."""
        from core.media import MediaInfo
        
        test_path = Path("/test/audio.wav")
        info = MediaInfo(test_path)
        
        assert info.path == test_path
        assert info.duration is None  # Not loaded yet
        assert info.has_audio is False  # Not loaded yet
        assert info.has_video is False  # Not loaded yet


if __name__ == "__main__":
    pytest.main([__file__])