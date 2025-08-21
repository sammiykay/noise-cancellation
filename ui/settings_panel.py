"""Settings panel for configuring noise reduction parameters."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSlider, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTabWidget,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QSettings

from utils.logging_setup import get_logger
from core.pipeline import Engine
from engines.spectral_gate import SpectralGateConfig
from engines.rnnoise import RNNoiseConfig
from engines.demucs import DemucsConfig

logger = get_logger("settings_panel")


class SettingsPanel(QWidget):
    """Panel for configuring noise reduction settings."""
    
    # Signals
    settings_changed = Signal(dict)  # Settings dictionary
    
    def __init__(self):
        super().__init__()
        
        self.settings = QSettings()
        self._setup_ui()
        self._load_settings()
        self._connect_signals()
        
        logger.debug("Settings panel initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        
        # Content layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        
        # Engine selection
        engine_group = self._create_engine_group()
        content_layout.addWidget(engine_group)
        
        # Engine-specific settings (tabs)
        self.engine_tabs = QTabWidget()
        content_layout.addWidget(self.engine_tabs)
        
        # Spectral Gate tab
        spectral_tab = self._create_spectral_gate_tab()
        self.engine_tabs.addTab(spectral_tab, "Spectral Gate")
        
        # RNNoise tab
        rnnoise_tab = self._create_rnnoise_tab()
        self.engine_tabs.addTab(rnnoise_tab, "RNNoise")
        
        # Demucs tab
        demucs_tab = self._create_demucs_tab()
        self.engine_tabs.addTab(demucs_tab, "Demucs")
        
        # Output settings
        output_group = self._create_output_group()
        content_layout.addWidget(output_group)
        
        # Post-processing settings
        post_group = self._create_post_processing_group()
        content_layout.addWidget(post_group)
        
        content_layout.addStretch()
    
    def _create_engine_group(self) -> QGroupBox:
        """Create engine selection group."""
        group = QGroupBox("Noise Reduction Engine")
        layout = QFormLayout(group)
        
        # Engine selection
        self.engine_combo = QComboBox()
        self.engine_combo.addItem("Spectral Gate", Engine.SPECTRAL_GATE.value)
        self.engine_combo.addItem("RNNoise", Engine.RNNOISE.value)
        self.engine_combo.addItem("Demucs (Advanced)", Engine.DEMUCS.value)
        layout.addRow("Engine:", self.engine_combo)
        
        # Engine description
        self.engine_description = QLabel()
        self.engine_description.setWordWrap(True)
        self.engine_description.setStyleSheet("color: gray; font-style: italic;")
        layout.addRow(self.engine_description)
        
        return group
    
    def _create_spectral_gate_tab(self) -> QWidget:
        """Create spectral gating settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Basic settings
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QFormLayout(basic_group)
        
        # Reduction amount
        self.spectral_reduction_slider = QSlider(Qt.Horizontal)
        self.spectral_reduction_slider.setRange(5, 60)
        self.spectral_reduction_slider.setValue(20)
        self.spectral_reduction_spin = QSpinBox()
        self.spectral_reduction_spin.setRange(5, 60)
        self.spectral_reduction_spin.setSuffix(" dB")
        
        reduction_layout = QHBoxLayout()
        reduction_layout.addWidget(self.spectral_reduction_slider)
        reduction_layout.addWidget(self.spectral_reduction_spin)
        basic_layout.addRow("Noise Reduction:", reduction_layout)
        
        # Noise type
        self.noise_stationary_combo = QComboBox()
        self.noise_stationary_combo.addItem("Stationary (constant background)", True)
        self.noise_stationary_combo.addItem("Non-stationary (varying noise)", False)
        basic_layout.addRow("Noise Type:", self.noise_stationary_combo)
        
        layout.addWidget(basic_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        # Time smoothing
        self.time_smoothing_slider = QSlider(Qt.Horizontal)
        self.time_smoothing_slider.setRange(0, 100)
        self.time_smoothing_slider.setValue(10)
        self.time_smoothing_spin = QDoubleSpinBox()
        self.time_smoothing_spin.setRange(0.0, 1.0)
        self.time_smoothing_spin.setSingleStep(0.01)
        self.time_smoothing_spin.setDecimals(2)
        
        time_smooth_layout = QHBoxLayout()
        time_smooth_layout.addWidget(self.time_smoothing_slider)
        time_smooth_layout.addWidget(self.time_smoothing_spin)
        advanced_layout.addRow("Time Smoothing:", time_smooth_layout)
        
        # Frequency smoothing
        self.freq_smoothing_slider = QSlider(Qt.Horizontal)
        self.freq_smoothing_slider.setRange(0, 100)
        self.freq_smoothing_slider.setValue(10)
        self.freq_smoothing_spin = QDoubleSpinBox()
        self.freq_smoothing_spin.setRange(0.0, 1.0)
        self.freq_smoothing_spin.setSingleStep(0.01)
        self.freq_smoothing_spin.setDecimals(2)
        
        freq_smooth_layout = QHBoxLayout()
        freq_smooth_layout.addWidget(self.freq_smoothing_slider)
        freq_smooth_layout.addWidget(self.freq_smoothing_spin)
        advanced_layout.addRow("Frequency Smoothing:", freq_smooth_layout)
        
        # Proportion decrease
        self.prop_decrease_slider = QSlider(Qt.Horizontal)
        self.prop_decrease_slider.setRange(0, 100)
        self.prop_decrease_slider.setValue(100)
        self.prop_decrease_spin = QDoubleSpinBox()
        self.prop_decrease_spin.setRange(0.0, 1.0)
        self.prop_decrease_spin.setSingleStep(0.01)
        self.prop_decrease_spin.setDecimals(2)
        self.prop_decrease_spin.setValue(1.0)
        
        prop_layout = QHBoxLayout()
        prop_layout.addWidget(self.prop_decrease_slider)
        prop_layout.addWidget(self.prop_decrease_spin)
        advanced_layout.addRow("Noise Proportion:", prop_layout)
        
        layout.addWidget(advanced_group)
        
        # Noise profile settings
        profile_group = QGroupBox("Noise Profile")
        profile_layout = QFormLayout(profile_group)
        
        self.use_noise_profile = QCheckBox("Use noise profile estimation")
        self.use_noise_profile.setChecked(True)
        profile_layout.addRow(self.use_noise_profile)
        
        # Manual noise profile time range
        manual_group = QGroupBox("Manual Noise Region (optional)")
        manual_layout = QFormLayout(manual_group)
        
        self.noise_start_spin = QDoubleSpinBox()
        self.noise_start_spin.setRange(0.0, 3600.0)
        self.noise_start_spin.setSuffix(" s")
        self.noise_start_spin.setDecimals(2)
        manual_layout.addRow("Start Time:", self.noise_start_spin)
        
        self.noise_end_spin = QDoubleSpinBox()
        self.noise_end_spin.setRange(0.0, 3600.0)
        self.noise_end_spin.setSuffix(" s")
        self.noise_end_spin.setDecimals(2)
        manual_layout.addRow("End Time:", self.noise_end_spin)
        
        profile_layout.addRow(manual_group)
        layout.addWidget(profile_group)
        
        layout.addStretch()
        return widget
    
    def _create_rnnoise_tab(self) -> QWidget:
        """Create RNNoise settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QFormLayout(model_group)
        
        self.rnnoise_model_combo = QComboBox()
        self._populate_rnnoise_models()
        model_layout.addRow("Model:", self.rnnoise_model_combo)
        
        # Browse for custom model
        browse_layout = QHBoxLayout()
        self.custom_model_path = QLineEdit()
        self.custom_model_path.setPlaceholderText("Path to custom .rnnn model file")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_rnnoise_model)
        
        browse_layout.addWidget(self.custom_model_path)
        browse_layout.addWidget(browse_button)
        model_layout.addRow("Custom Model:", browse_layout)
        
        # Model info
        self.model_info_label = QLabel()
        self.model_info_label.setWordWrap(True)
        self.model_info_label.setStyleSheet("color: gray; font-style: italic;")
        model_layout.addRow(self.model_info_label)
        
        layout.addWidget(model_group)
        
        # Processing settings
        process_group = QGroupBox("Processing Settings")
        process_layout = QFormLayout(process_group)
        
        # Mix factor
        self.rnnoise_mix_slider = QSlider(Qt.Horizontal)
        self.rnnoise_mix_slider.setRange(0, 100)
        self.rnnoise_mix_slider.setValue(100)
        self.rnnoise_mix_spin = QDoubleSpinBox()
        self.rnnoise_mix_spin.setRange(0.0, 1.0)
        self.rnnoise_mix_spin.setSingleStep(0.01)
        self.rnnoise_mix_spin.setDecimals(2)
        self.rnnoise_mix_spin.setValue(1.0)
        
        mix_layout = QHBoxLayout()
        mix_layout.addWidget(self.rnnoise_mix_slider)
        mix_layout.addWidget(self.rnnoise_mix_spin)
        process_layout.addRow("Mix Factor:", mix_layout)
        
        # Sample rate
        self.rnnoise_sr_combo = QComboBox()
        self.rnnoise_sr_combo.addItem("48000 Hz (recommended)", 48000)
        self.rnnoise_sr_combo.addItem("44100 Hz", 44100)
        self.rnnoise_sr_combo.addItem("32000 Hz", 32000)
        process_layout.addRow("Sample Rate:", self.rnnoise_sr_combo)
        
        layout.addWidget(process_group)
        
        layout.addStretch()
        return widget
    
    def _create_demucs_tab(self) -> QWidget:
        """Create Demucs settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QFormLayout(model_group)
        
        self.demucs_model_combo = QComboBox()
        self.demucs_model_combo.addItem("htdemucs (highest quality)", "htdemucs")
        self.demucs_model_combo.addItem("hdemucs_mmi (balanced)", "hdemucs_mmi")
        self.demucs_model_combo.addItem("mdx_extra (fastest)", "mdx_extra")
        model_layout.addRow("Model:", self.demucs_model_combo)
        
        layout.addWidget(model_group)
        
        # Processing settings
        process_group = QGroupBox("Processing Settings")
        process_layout = QFormLayout(process_group)
        
        # Device selection
        self.demucs_device_combo = QComboBox()
        self.demucs_device_combo.addItem("CPU", "cpu")
        self.demucs_device_combo.addItem("CUDA (NVIDIA GPU)", "cuda")
        self.demucs_device_combo.addItem("MPS (Apple Silicon)", "mps")
        process_layout.addRow("Device:", self.demucs_device_combo)
        
        # Noise reduction strength
        self.demucs_strength_slider = QSlider(Qt.Horizontal)
        self.demucs_strength_slider.setRange(0, 100)
        self.demucs_strength_slider.setValue(80)
        self.demucs_strength_spin = QDoubleSpinBox()
        self.demucs_strength_spin.setRange(0.0, 1.0)
        self.demucs_strength_spin.setSingleStep(0.01)
        self.demucs_strength_spin.setDecimals(2)
        self.demucs_strength_spin.setValue(0.8)
        
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(self.demucs_strength_slider)
        strength_layout.addWidget(self.demucs_strength_spin)
        process_layout.addRow("Reduction Strength:", strength_layout)
        
        # Vocal enhancement
        self.vocal_enhancement = QCheckBox("Enhance vocal separation")
        self.vocal_enhancement.setChecked(True)
        process_layout.addRow(self.vocal_enhancement)
        
        # Parallel jobs
        self.demucs_jobs_spin = QSpinBox()
        self.demucs_jobs_spin.setRange(1, 8)
        self.demucs_jobs_spin.setValue(1)
        process_layout.addRow("Parallel Jobs:", self.demucs_jobs_spin)
        
        layout.addWidget(process_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        # Segment length
        self.segment_length_spin = QDoubleSpinBox()
        self.segment_length_spin.setRange(0.0, 60.0)
        self.segment_length_spin.setValue(0.0)  # 0 = automatic
        self.segment_length_spin.setSuffix(" s (0 = auto)")
        advanced_layout.addRow("Segment Length:", self.segment_length_spin)
        
        # Overlap
        self.overlap_spin = QDoubleSpinBox()
        self.overlap_spin.setRange(0.0, 0.5)
        self.overlap_spin.setSingleStep(0.05)
        self.overlap_spin.setDecimals(2)
        self.overlap_spin.setValue(0.25)
        advanced_layout.addRow("Overlap:", self.overlap_spin)
        
        layout.addWidget(advanced_group)
        
        # Warning label
        warning_label = QLabel(
            "⚠️ Demucs requires significant computational resources and may take much longer than other engines."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(warning_label)
        
        layout.addStretch()
        return widget
    
    def _create_output_group(self) -> QGroupBox:
        """Create output settings group."""
        group = QGroupBox("Output Settings")
        layout = QFormLayout(group)
        
        # Output format
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItem("WAV (Lossless)", "wav")
        self.output_format_combo.addItem("FLAC (Lossless)", "flac")
        self.output_format_combo.addItem("MP3 (Compressed)", "mp3")
        self.output_format_combo.addItem("AAC (Compressed)", "aac")
        layout.addRow("Format:", self.output_format_combo)
        
        # Sample rate
        self.output_sr_combo = QComboBox()
        self.output_sr_combo.addItem("Keep Original", None)
        self.output_sr_combo.addItem("48000 Hz", 48000)
        self.output_sr_combo.addItem("44100 Hz", 44100)
        self.output_sr_combo.addItem("32000 Hz", 32000)
        self.output_sr_combo.addItem("22050 Hz", 22050)
        layout.addRow("Sample Rate:", self.output_sr_combo)
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Leave empty to save next to original files")
        
        browse_output_button = QPushButton("Browse...")
        browse_output_button.clicked.connect(self._browse_output_dir)
        
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(browse_output_button)
        layout.addRow("Output Directory:", output_dir_layout)
        
        # Video handling
        self.preserve_video = QCheckBox("Replace audio in video files (preserve video)")
        self.preserve_video.setChecked(True)
        layout.addRow(self.preserve_video)
        
        return group
    
    def _create_post_processing_group(self) -> QGroupBox:
        """Create post-processing settings group."""
        group = QGroupBox("Post-Processing")
        layout = QFormLayout(group)
        
        # Loudness normalization
        self.normalize_loudness = QCheckBox("Normalize loudness (EBU R128)")
        layout.addRow(self.normalize_loudness)
        
        # Target LUFS
        self.target_lufs_spin = QDoubleSpinBox()
        self.target_lufs_spin.setRange(-30.0, -10.0)
        self.target_lufs_spin.setValue(-23.0)
        self.target_lufs_spin.setSuffix(" LUFS")
        self.target_lufs_spin.setDecimals(1)
        layout.addRow("Target Loudness:", self.target_lufs_spin)
        
        return group
    
    def _populate_rnnoise_models(self) -> None:
        """Populate RNNoise model dropdown."""
        self.rnnoise_model_combo.clear()
        
        models_dir = Path("models")
        if models_dir.exists():
            # Standard models
            standard_models = {
                "bd.rnnn": "Broadband (General Purpose)",
                "sh.rnnn": "Speech Heavy",
                "mp.rnnn": "Music Performance",
                "cb.rnnn": "Cassette Tape"
            }
            
            for filename, description in standard_models.items():
                model_path = models_dir / filename
                if model_path.exists():
                    self.rnnoise_model_combo.addItem(f"{description}", str(model_path))
            
            # Custom models
            for model_file in models_dir.glob("*.rnnn"):
                if model_file.name not in standard_models:
                    name = model_file.stem.replace("_", " ").title()
                    self.rnnoise_model_combo.addItem(f"{name} (Custom)", str(model_file))
        
        if self.rnnoise_model_combo.count() == 0:
            self.rnnoise_model_combo.addItem("No models found", "")
    
    def _browse_rnnoise_model(self) -> None:
        """Browse for custom RNNoise model."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select RNNoise Model",
            "",
            "RNNoise Models (*.rnnn);;All Files (*.*)"
        )
        
        if file_path:
            self.custom_model_path.setText(file_path)
    
    def _browse_output_dir(self) -> None:
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_edit.text() or ""
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Engine selection
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)
        self.engine_combo.currentTextChanged.connect(self._emit_settings_changed)
        
        # Spectral gate signals
        self.spectral_reduction_slider.valueChanged.connect(self.spectral_reduction_spin.setValue)
        self.spectral_reduction_spin.valueChanged.connect(self.spectral_reduction_slider.setValue)
        self.spectral_reduction_spin.valueChanged.connect(self._emit_settings_changed)
        
        self.time_smoothing_slider.valueChanged.connect(
            lambda v: self.time_smoothing_spin.setValue(v / 100.0)
        )
        self.time_smoothing_spin.valueChanged.connect(
            lambda v: self.time_smoothing_slider.setValue(int(v * 100))
        )
        self.time_smoothing_spin.valueChanged.connect(self._emit_settings_changed)
        
        self.freq_smoothing_slider.valueChanged.connect(
            lambda v: self.freq_smoothing_spin.setValue(v / 100.0)
        )
        self.freq_smoothing_spin.valueChanged.connect(
            lambda v: self.freq_smoothing_slider.setValue(int(v * 100))
        )
        self.freq_smoothing_spin.valueChanged.connect(self._emit_settings_changed)
        
        self.prop_decrease_slider.valueChanged.connect(
            lambda v: self.prop_decrease_spin.setValue(v / 100.0)
        )
        self.prop_decrease_spin.valueChanged.connect(
            lambda v: self.prop_decrease_slider.setValue(int(v * 100))
        )
        self.prop_decrease_spin.valueChanged.connect(self._emit_settings_changed)
        
        # RNNoise signals
        self.rnnoise_mix_slider.valueChanged.connect(
            lambda v: self.rnnoise_mix_spin.setValue(v / 100.0)
        )
        self.rnnoise_mix_spin.valueChanged.connect(
            lambda v: self.rnnoise_mix_slider.setValue(int(v * 100))
        )
        self.rnnoise_mix_spin.valueChanged.connect(self._emit_settings_changed)
        
        # Demucs signals
        self.demucs_strength_slider.valueChanged.connect(
            lambda v: self.demucs_strength_spin.setValue(v / 100.0)
        )
        self.demucs_strength_spin.valueChanged.connect(
            lambda v: self.demucs_strength_slider.setValue(int(v * 100))
        )
        self.demucs_strength_spin.valueChanged.connect(self._emit_settings_changed)
        
        # Other signals
        widgets_to_connect = [
            self.noise_stationary_combo, self.use_noise_profile, self.noise_start_spin,
            self.noise_end_spin, self.rnnoise_model_combo, self.custom_model_path,
            self.rnnoise_sr_combo, self.demucs_model_combo, self.demucs_device_combo,
            self.vocal_enhancement, self.demucs_jobs_spin, self.segment_length_spin,
            self.overlap_spin, self.output_format_combo, self.output_sr_combo,
            self.output_dir_edit, self.preserve_video, self.normalize_loudness, self.target_lufs_spin
        ]
        
        for widget in widgets_to_connect:
            if hasattr(widget, 'currentTextChanged'):
                widget.currentTextChanged.connect(self._emit_settings_changed)
            elif hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(self._emit_settings_changed)
            elif hasattr(widget, 'toggled'):
                widget.toggled.connect(self._emit_settings_changed)
            elif hasattr(widget, 'textChanged'):
                widget.textChanged.connect(self._emit_settings_changed)
    
    def _on_engine_changed(self) -> None:
        """Handle engine selection change."""
        engine_value = self.engine_combo.currentData()
        
        # Update tabs
        if engine_value == Engine.SPECTRAL_GATE.value:
            self.engine_tabs.setCurrentIndex(0)
            self.engine_description.setText(
                "Spectral gating removes noise by analyzing frequency content and suppressing "
                "regions with low signal-to-noise ratio. Best for stationary background noise."
            )
        elif engine_value == Engine.RNNOISE.value:
            self.engine_tabs.setCurrentIndex(1)
            self.engine_description.setText(
                "RNNoise uses a recurrent neural network trained on speech and noise patterns. "
                "Excellent for speech content with various noise types."
            )
        elif engine_value == Engine.DEMUCS.value:
            self.engine_tabs.setCurrentIndex(2)
            self.engine_description.setText(
                "Demucs separates audio sources using deep learning. Most advanced but requires "
                "significant computational resources and processing time."
            )
    
    def _emit_settings_changed(self) -> None:
        """Emit settings changed signal."""
        settings = self.get_current_settings()
        self.settings_changed.emit(settings)
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings as dictionary."""
        # Get selected engine
        engine_value = self.engine_combo.currentData()
        
        settings = {
            'engine': engine_value,
            'output_format': self.output_format_combo.currentData(),
            'output_sample_rate': self.output_sr_combo.currentData(),
            'output_directory': self.output_dir_edit.text() or None,
            'preserve_video': self.preserve_video.isChecked(),
            'normalize_loudness': self.normalize_loudness.isChecked(),
            'target_lufs': self.target_lufs_spin.value()
        }
        
        # Engine-specific settings
        if engine_value == Engine.SPECTRAL_GATE.value:
            settings['engine_config'] = {
                'reduction_db': self.spectral_reduction_spin.value(),
                'time_smoothing': self.time_smoothing_spin.value(),
                'frequency_smoothing': self.freq_smoothing_spin.value(),
                'stationary': self.noise_stationary_combo.currentData(),
                'prop_decrease': self.prop_decrease_spin.value(),
                'use_noise_profile': self.use_noise_profile.isChecked(),
                'noise_start_time': self.noise_start_spin.value() if self.noise_start_spin.value() > 0 else None,
                'noise_end_time': self.noise_end_spin.value() if self.noise_end_spin.value() > 0 else None
            }
        
        elif engine_value == Engine.RNNOISE.value:
            model_path = self.custom_model_path.text() or self.rnnoise_model_combo.currentData()
            settings['engine_config'] = {
                'model_path': Path(model_path) if model_path else None,
                'mix_factor': self.rnnoise_mix_spin.value(),
                'sample_rate': self.rnnoise_sr_combo.currentData()
            }
        
        elif engine_value == Engine.DEMUCS.value:
            settings['engine_config'] = {
                'model_name': self.demucs_model_combo.currentData(),
                'device': self.demucs_device_combo.currentData(),
                'noise_reduction_strength': self.demucs_strength_spin.value(),
                'vocal_enhancement': self.vocal_enhancement.isChecked(),
                'jobs': self.demucs_jobs_spin.value(),
                'segment_length': self.segment_length_spin.value() if self.segment_length_spin.value() > 0 else None,
                'overlap': self.overlap_spin.value()
            }
        
        return settings
    
    def _load_settings(self) -> None:
        """Load settings from QSettings."""
        # Engine selection
        engine = self.settings.value("engine", Engine.SPECTRAL_GATE.value)
        index = self.engine_combo.findData(engine)
        if index >= 0:
            self.engine_combo.setCurrentIndex(index)
        
        # Output settings
        output_format = self.settings.value("output_format", "wav")
        index = self.output_format_combo.findData(output_format)
        if index >= 0:
            self.output_format_combo.setCurrentIndex(index)
        
        # Load other settings with defaults
        self.output_dir_edit.setText(self.settings.value("output_directory", ""))
        self.preserve_video.setChecked(self.settings.value("preserve_video", True, type=bool))
        self.normalize_loudness.setChecked(self.settings.value("normalize_loudness", False, type=bool))
        self.target_lufs_spin.setValue(self.settings.value("target_lufs", -23.0, type=float))
        
        # Spectral gate settings
        self.spectral_reduction_spin.setValue(self.settings.value("spectral/reduction_db", 20.0, type=float))
        self.time_smoothing_spin.setValue(self.settings.value("spectral/time_smoothing", 0.1, type=float))
        self.freq_smoothing_spin.setValue(self.settings.value("spectral/frequency_smoothing", 0.1, type=float))
        
        logger.debug("Settings loaded from file")
    
    def save_settings(self) -> None:
        """Save current settings to QSettings."""
        settings = self.get_current_settings()
        
        # Save main settings
        self.settings.setValue("engine", settings['engine'])
        self.settings.setValue("output_format", settings['output_format'])
        self.settings.setValue("output_sample_rate", settings.get('output_sample_rate'))
        self.settings.setValue("output_directory", settings.get('output_directory', ''))
        self.settings.setValue("preserve_video", settings['preserve_video'])
        self.settings.setValue("normalize_loudness", settings['normalize_loudness'])
        self.settings.setValue("target_lufs", settings['target_lufs'])
        
        # Save engine-specific settings
        if 'engine_config' in settings and settings['engine'] == Engine.SPECTRAL_GATE.value:
            config = settings['engine_config']
            self.settings.setValue("spectral/reduction_db", config['reduction_db'])
            self.settings.setValue("spectral/time_smoothing", config['time_smoothing'])
            self.settings.setValue("spectral/frequency_smoothing", config['frequency_smoothing'])
            self.settings.setValue("spectral/stationary", config['stationary'])
            self.settings.setValue("spectral/prop_decrease", config['prop_decrease'])
            self.settings.setValue("spectral/use_noise_profile", config['use_noise_profile'])
        
        self.settings.sync()
        logger.debug("Settings saved to file")