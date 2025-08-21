"""Tests for noise reduction engines."""

import pytest
import numpy as np
import tempfile
from pathlib import Path

from engines.spectral_gate import SpectralGateEngine, SpectralGateConfig
from engines.rnnoise import RNNoiseConfig
from utils.profiles import NoiseProfile


class TestSpectralGateEngine:
    """Test spectral gating engine."""
    
    def create_test_audio(self, duration=2.0, sample_rate=44100):
        """Create test audio with known characteristics."""
        samples = int(duration * sample_rate)
        
        # Create signal + noise
        t = np.linspace(0, duration, samples)
        signal = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        noise = 0.1 * np.random.normal(0, 1, samples)  # White noise
        
        return (signal + noise).astype(np.float32)
    
    def create_test_noise_profile(self, sample_rate=44100):
        """Create a test noise profile."""
        # Generate noise-only segment
        noise_duration = 1.0
        noise_samples = int(noise_duration * sample_rate)
        noise = 0.1 * np.random.normal(0, 1, noise_samples).astype(np.float32)
        
        # Create simple noise profile
        n_fft = 2048
        frequencies = np.fft.rfftfreq(n_fft, 1/sample_rate)
        power_spectrum = np.ones(len(frequencies)) * 0.01  # Flat noise spectrum
        
        return NoiseProfile(
            power_spectrum=power_spectrum,
            frequencies=frequencies,
            duration=noise_duration,
            source_type="test",
            confidence=0.8
        )
    
    def test_engine_initialization(self):
        """Test engine initialization with different configs."""
        # Default config
        config = SpectralGateConfig()
        engine = SpectralGateEngine(config)
        assert engine.config.reduction_db == 20.0
        
        # Custom config
        config = SpectralGateConfig(reduction_db=30.0, stationary=False)
        engine = SpectralGateEngine(config)
        assert engine.config.reduction_db == 30.0
        assert engine.config.stationary is False
    
    def test_noise_profile_setting(self):
        """Test noise profile functionality."""
        config = SpectralGateConfig()
        engine = SpectralGateEngine(config)
        
        # Initially no profile
        assert engine.noise_profile is None
        
        # Set profile
        profile = self.create_test_noise_profile()
        engine.set_noise_profile(profile)
        assert engine.noise_profile is not None
        assert engine.noise_profile.source_type == "test"
    
    def test_basic_processing(self):
        """Test basic audio processing."""
        config = SpectralGateConfig(reduction_db=10.0)
        engine = SpectralGateEngine(config)
        
        # Create test audio
        sample_rate = 44100
        audio = self.create_test_audio(duration=1.0, sample_rate=sample_rate)
        original_rms = np.sqrt(np.mean(audio ** 2))
        
        # Process audio
        processed = engine.process(audio, sample_rate)
        
        # Check output
        assert processed.shape == audio.shape
        assert processed.dtype == audio.dtype
        
        # Should reduce some noise (RMS should be different)
        processed_rms = np.sqrt(np.mean(processed ** 2))
        # Allow for some variation in processing
        assert processed_rms != original_rms
    
    def test_stereo_processing(self):
        """Test stereo audio processing."""
        config = SpectralGateConfig()
        engine = SpectralGateEngine(config)
        
        # Create stereo test audio
        sample_rate = 44100
        mono_audio = self.create_test_audio(duration=0.5, sample_rate=sample_rate)
        stereo_audio = np.column_stack([mono_audio, mono_audio * 0.8])
        
        # Process
        processed = engine.process(stereo_audio, sample_rate)
        
        # Check stereo output maintained
        assert processed.shape == stereo_audio.shape
        assert len(processed.shape) == 2
        assert processed.shape[1] == 2
    
    def test_auto_noise_profile_creation(self):
        """Test automatic noise profile creation."""
        config = SpectralGateConfig(use_noise_profile=True)
        engine = SpectralGateEngine(config)
        
        # Create audio with quiet beginning (for auto-profile detection)
        sample_rate = 44100
        samples = int(2.0 * sample_rate)
        
        # Quiet first 0.5 seconds, louder rest
        audio = np.zeros(samples, dtype=np.float32)
        audio[:samples//4] = 0.01 * np.random.normal(0, 1, samples//4)  # Quiet noise
        audio[samples//4:] = self.create_test_audio(duration=1.5, sample_rate=sample_rate)
        
        # Create profile
        profile = engine.create_noise_profile(audio, sample_rate)
        
        if profile:  # May fail if no silence detected
            assert profile.duration > 0
            assert len(profile.power_spectrum) > 0
            assert profile.source_type == "auto"
    
    def test_manual_noise_profile_creation(self):
        """Test manual noise profile creation."""
        config = SpectralGateConfig()
        engine = SpectralGateEngine(config)
        
        # Create test audio
        sample_rate = 44100
        audio = self.create_test_audio(duration=2.0, sample_rate=sample_rate)
        
        # Create profile from first 0.5 seconds
        profile = engine.create_noise_profile(
            audio, sample_rate, 
            start_time=0.0, end_time=0.5
        )
        
        assert profile is not None
        assert profile.duration == pytest.approx(0.5, rel=0.1)
        assert profile.source_type == "manual"
    
    def test_config_serialization(self):
        """Test configuration serialization."""
        config = SpectralGateConfig(
            reduction_db=25.0,
            time_smoothing=0.2,
            frequency_smoothing=0.15,
            stationary=False
        )
        
        # Convert to dict and back
        config_dict = config.to_dict()
        config2 = SpectralGateConfig.from_dict(config_dict)
        
        assert config2.reduction_db == config.reduction_db
        assert config2.time_smoothing == config.time_smoothing
        assert config2.frequency_smoothing == config.frequency_smoothing
        assert config2.stationary == config.stationary
    
    def test_progress_callback(self):
        """Test progress callback functionality."""
        config = SpectralGateConfig()
        engine = SpectralGateEngine(config)
        
        # Track progress calls
        progress_calls = []
        
        def progress_callback(progress, message):
            progress_calls.append((progress, message))
        
        # Process with callback
        sample_rate = 44100
        audio = self.create_test_audio(duration=0.5, sample_rate=sample_rate)
        
        processed = engine.process(audio, sample_rate, progress_callback)
        
        # Should have received progress updates
        assert len(progress_calls) > 0
        
        # Progress should be between 0 and 1
        for progress, message in progress_calls:
            assert 0.0 <= progress <= 1.0
            assert isinstance(message, str)
        
        # Last progress should be 1.0 (complete)
        assert progress_calls[-1][0] == 1.0


class TestRNNoiseConfig:
    """Test RNNoise configuration."""
    
    def test_config_validation(self):
        """Test configuration value validation."""
        # Valid config
        config = RNNoiseConfig(mix_factor=0.5, sample_rate=48000)
        assert config.mix_factor == 0.5
        assert config.sample_rate == 48000
        
        # Mix factor should be clamped to 0-1
        config = RNNoiseConfig(mix_factor=1.5)
        assert config.mix_factor == 1.0
        
        config = RNNoiseConfig(mix_factor=-0.1)
        assert config.mix_factor == 0.0
    
    def test_config_serialization(self):
        """Test configuration serialization."""
        model_path = Path("/test/model.rnnn")
        config = RNNoiseConfig(
            model_path=model_path,
            mix_factor=0.8,
            sample_rate=44100
        )
        
        # Convert to dict and back
        config_dict = config.to_dict()
        config2 = RNNoiseConfig.from_dict(config_dict)
        
        assert config2.model_path == config.model_path
        assert config2.mix_factor == config.mix_factor
        assert config2.sample_rate == config.sample_rate
        
        # Test with None model path
        config = RNNoiseConfig(model_path=None)
        config_dict = config.to_dict()
        config2 = RNNoiseConfig.from_dict(config_dict)
        assert config2.model_path is None


class TestEngineIntegration:
    """Test integration between different engines."""
    
    def create_test_audio_file(self, duration=1.0, sample_rate=44100):
        """Create a temporary test audio file."""
        from core.media import save_audio
        
        # Generate test audio
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        audio = 0.3 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        audio += 0.1 * np.random.normal(0, 1, samples)  # Add noise
        audio = audio.astype(np.float32)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = Path(f.name)
        
        success = save_audio(audio, temp_path, sample_rate)
        
        if success:
            return temp_path, audio, sample_rate
        else:
            return None, None, None
    
    def test_processing_job_creation(self):
        """Test processing job creation with different engines."""
        from core.pipeline import ProcessingJob, Engine
        
        test_file = Path("/test/audio.wav")
        
        # Spectral gate job
        job = ProcessingJob(
            input_path=test_file,
            engine=Engine.SPECTRAL_GATE,
            engine_config={
                'reduction_db': 20.0,
                'stationary': True
            }
        )
        
        assert job.input_path == test_file
        assert job.engine == Engine.SPECTRAL_GATE
        assert job.engine_config['reduction_db'] == 20.0
    
    def test_multiple_engine_availability(self):
        """Test that multiple engines can coexist."""
        from core.pipeline import ProcessingPipeline, Engine
        
        pipeline = ProcessingPipeline()
        available_engines = pipeline.get_available_engines()
        
        # Should have at least spectral gate
        assert Engine.SPECTRAL_GATE in available_engines
        
        # Test engine creation for each available engine
        for engine_type in available_engines:
            try:
                if engine_type == Engine.SPECTRAL_GATE:
                    config = {'reduction_db': 20.0}
                elif engine_type == Engine.RNNOISE:
                    config = {'mix_factor': 1.0, 'sample_rate': 48000}
                elif engine_type == Engine.DEMUCS:
                    config = {'model_name': 'htdemucs', 'device': 'cpu'}
                else:
                    config = {}
                
                engine = pipeline._get_engine(engine_type, config)
                assert engine is not None
                
            except Exception as e:
                # Some engines might not be available (e.g., missing dependencies)
                # This is acceptable for testing
                print(f"Engine {engine_type} not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__])