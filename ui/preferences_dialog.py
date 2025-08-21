"""Preferences dialog for application settings."""

from pathlib import Path
from typing import Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QPushButton, QGroupBox, QLabel, QLineEdit, QSpinBox,
    QDoubleSpinBox, QCheckBox, QComboBox, QFileDialog,
    QDialogButtonBox, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QSettings, QTimer

from utils.logging_setup import get_logger
from utils.validators import validate_ffmpeg

logger = get_logger("preferences")


class PreferencesDialog(QDialog):
    """Dialog for editing application preferences."""
    
    def __init__(self, parent=None, config_dir: Path = Path("config")):
        super().__init__(parent)
        
        self.config_dir = config_dir
        self.settings = QSettings(
            str(config_dir / "settings.ini"),
            QSettings.IniFormat
        )
        
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(600, 500)
        
        self._setup_ui()
        self._load_settings()
        
        logger.debug("Preferences dialog initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Tab widget for different categories
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # General tab
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "General")
        
        # Processing tab
        processing_tab = self._create_processing_tab()
        tab_widget.addTab(processing_tab, "Processing")
        
        # Paths tab
        paths_tab = self._create_paths_tab()
        tab_widget.addTab(paths_tab, "Paths")
        
        # Advanced tab
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        """Create general preferences tab."""
        from PySide6.QtWidgets import QWidget
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Application settings
        app_group = QGroupBox("Application")
        app_layout = QFormLayout(app_group)
        
        self.check_updates_check = QCheckBox("Check for updates on startup")
        app_layout.addRow(self.check_updates_check)
        
        self.minimize_to_tray_check = QCheckBox("Minimize to system tray")
        app_layout.addRow(self.minimize_to_tray_check)
        
        self.confirm_exit_check = QCheckBox("Confirm before exiting")
        self.confirm_exit_check.setChecked(True)
        app_layout.addRow(self.confirm_exit_check)
        
        layout.addWidget(app_group)
        
        # UI settings
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout(ui_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("System Default", "system")
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        ui_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setSuffix(" pt")
        ui_layout.addRow("Font Size:", self.font_size_spin)
        
        self.auto_save_check = QCheckBox("Auto-save settings on change")
        self.auto_save_check.setChecked(True)
        ui_layout.addRow(self.auto_save_check)
        
        layout.addWidget(ui_group)
        
        layout.addStretch()
        return widget
    
    def _create_processing_tab(self) -> QWidget:
        """Create processing preferences tab."""
        from PySide6.QtWidgets import QWidget
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Performance settings
        perf_group = QGroupBox("Performance")
        perf_layout = QFormLayout(perf_group)
        
        self.max_parallel_spin = QSpinBox()
        self.max_parallel_spin.setRange(1, 8)
        self.max_parallel_spin.setValue(2)
        perf_layout.addRow("Max Parallel Jobs:", self.max_parallel_spin)
        
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(512, 8192)
        self.memory_limit_spin.setValue(2048)
        self.memory_limit_spin.setSuffix(" MB")
        perf_layout.addRow("Memory Limit:", self.memory_limit_spin)
        
        self.temp_dir_edit = QLineEdit()
        temp_browse_button = QPushButton("Browse...")
        temp_browse_button.clicked.connect(self._browse_temp_dir)
        
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temp_dir_edit)
        temp_layout.addWidget(temp_browse_button)
        perf_layout.addRow("Temp Directory:", temp_layout)
        
        layout.addWidget(perf_group)
        
        # Default settings
        defaults_group = QGroupBox("Default Settings")
        defaults_layout = QFormLayout(defaults_group)
        
        self.default_engine_combo = QComboBox()
        self.default_engine_combo.addItem("Spectral Gate", "spectral_gate")
        self.default_engine_combo.addItem("RNNoise", "rnnoise")
        self.default_engine_combo.addItem("Demucs", "demucs")
        defaults_layout.addRow("Default Engine:", self.default_engine_combo)
        
        self.default_format_combo = QComboBox()
        self.default_format_combo.addItem("WAV", "wav")
        self.default_format_combo.addItem("FLAC", "flac")
        self.default_format_combo.addItem("MP3", "mp3")
        defaults_layout.addRow("Default Format:", self.default_format_combo)
        
        self.preserve_original_check = QCheckBox("Preserve original files")
        self.preserve_original_check.setChecked(True)
        defaults_layout.addRow(self.preserve_original_check)
        
        layout.addWidget(defaults_group)
        
        layout.addStretch()
        return widget
    
    def _create_paths_tab(self) -> QWidget:
        """Create paths preferences tab."""
        from PySide6.QtWidgets import QWidget
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # External tools
        tools_group = QGroupBox("External Tools")
        tools_layout = QFormLayout(tools_group)
        
        # FFmpeg path
        self.ffmpeg_path_edit = QLineEdit()
        ffmpeg_browse_button = QPushButton("Browse...")
        ffmpeg_browse_button.clicked.connect(self._browse_ffmpeg)
        ffmpeg_test_button = QPushButton("Test")
        ffmpeg_test_button.clicked.connect(self._test_ffmpeg)
        
        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.addWidget(self.ffmpeg_path_edit)
        ffmpeg_layout.addWidget(ffmpeg_browse_button)
        ffmpeg_layout.addWidget(ffmpeg_test_button)
        tools_layout.addRow("FFmpeg Path:", ffmpeg_layout)
        
        self.ffmpeg_status_label = QLabel()
        self.ffmpeg_status_label.setStyleSheet("color: gray; font-style: italic;")
        tools_layout.addRow("", self.ffmpeg_status_label)
        
        layout.addWidget(tools_group)
        
        # Output paths
        output_group = QGroupBox("Output Paths")
        output_layout = QFormLayout(output_group)
        
        self.output_pattern_edit = QLineEdit()
        self.output_pattern_edit.setPlaceholderText("{parent}/clean/{name}_clean{ext}")
        output_layout.addRow("Output Pattern:", self.output_pattern_edit)
        
        pattern_help = QLabel(
            "Available placeholders:\n"
            "{parent} - Parent directory\n"
            "{name} - Filename without extension\n"
            "{ext} - File extension\n"
            "{stem} - Full filename with extension"
        )
        pattern_help.setStyleSheet("color: gray; font-size: 9px;")
        pattern_help.setWordWrap(True)
        output_layout.addRow("", pattern_help)
        
        self.default_output_dir_edit = QLineEdit()
        output_browse_button = QPushButton("Browse...")
        output_browse_button.clicked.connect(self._browse_output_dir)
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.default_output_dir_edit)
        output_dir_layout.addWidget(output_browse_button)
        output_layout.addRow("Default Output Dir:", output_dir_layout)
        
        layout.addWidget(output_group)
        
        # Model paths
        models_group = QGroupBox("Model Paths")
        models_layout = QFormLayout(models_group)
        
        self.rnnoise_models_edit = QLineEdit()
        models_browse_button = QPushButton("Browse...")
        models_browse_button.clicked.connect(self._browse_models_dir)
        
        models_dir_layout = QHBoxLayout()
        models_dir_layout.addWidget(self.rnnoise_models_edit)
        models_dir_layout.addWidget(models_browse_button)
        models_layout.addRow("RNNoise Models:", models_dir_layout)
        
        layout.addWidget(models_group)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced preferences tab."""
        from PySide6.QtWidgets import QWidget
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Logging settings
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("DEBUG", "DEBUG")
        self.log_level_combo.addItem("INFO", "INFO")
        self.log_level_combo.addItem("WARNING", "WARNING")
        self.log_level_combo.addItem("ERROR", "ERROR")
        self.log_level_combo.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        self.max_log_files_spin = QSpinBox()
        self.max_log_files_spin.setRange(1, 30)
        self.max_log_files_spin.setValue(7)
        logging_layout.addRow("Max Log Files:", self.max_log_files_spin)
        
        self.log_to_file_check = QCheckBox("Log to file")
        self.log_to_file_check.setChecked(True)
        logging_layout.addRow(self.log_to_file_check)
        
        layout.addWidget(logging_group)
        
        # Debug settings
        debug_group = QGroupBox("Debug")
        debug_layout = QFormLayout(debug_group)
        
        self.enable_debug_check = QCheckBox("Enable debug mode")
        debug_layout.addRow(self.enable_debug_check)
        
        self.keep_temp_files_check = QCheckBox("Keep temporary files")
        debug_layout.addRow(self.keep_temp_files_check)
        
        self.verbose_ffmpeg_check = QCheckBox("Verbose FFmpeg output")
        debug_layout.addRow(self.verbose_ffmpeg_check)
        
        layout.addWidget(debug_group)
        
        # Reset section
        reset_group = QGroupBox("Reset")
        reset_layout = QVBoxLayout(reset_group)
        
        reset_button = QPushButton("Reset All Settings to Defaults")
        reset_button.clicked.connect(self._reset_settings)
        reset_layout.addWidget(reset_button)
        
        layout.addWidget(reset_group)
        
        layout.addStretch()
        return widget
    
    def _browse_temp_dir(self) -> None:
        """Browse for temporary directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Temporary Directory"
        )
        if directory:
            self.temp_dir_edit.setText(directory)
    
    def _browse_ffmpeg(self) -> None:
        """Browse for FFmpeg executable."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select FFmpeg Executable", "",
            "Executable Files (*.exe);;All Files (*.*)"
        )
        if filename:
            self.ffmpeg_path_edit.setText(filename)
    
    def _test_ffmpeg(self) -> None:
        """Test FFmpeg installation."""
        ffmpeg_path = self.ffmpeg_path_edit.text() or "ffmpeg"
        
        # Test FFmpeg
        result = validate_ffmpeg()
        
        if result.is_valid:
            self.ffmpeg_status_label.setText("✓ FFmpeg is working")
            self.ffmpeg_status_label.setStyleSheet("color: green;")
        else:
            self.ffmpeg_status_label.setText(f"✗ {result.message}")
            self.ffmpeg_status_label.setStyleSheet("color: red;")
            
            if result.suggestions:
                QMessageBox.information(
                    self, "FFmpeg Test",
                    f"FFmpeg test failed: {result.message}\n\nSuggestions:\n" +
                    "\n".join(f"• {s}" for s in result.suggestions)
                )
    
    def _browse_output_dir(self) -> None:
        """Browse for default output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Output Directory"
        )
        if directory:
            self.default_output_dir_edit.setText(directory)
    
    def _browse_models_dir(self) -> None:
        """Browse for RNNoise models directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select RNNoise Models Directory"
        )
        if directory:
            self.rnnoise_models_edit.setText(directory)
    
    def _reset_settings(self) -> None:
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings.clear()
            self._load_settings()
            QMessageBox.information(
                self, "Settings Reset",
                "All settings have been reset to their default values."
            )
    
    def _load_settings(self) -> None:
        """Load settings from configuration."""
        # General settings
        self.check_updates_check.setChecked(
            self.settings.value("general/check_updates", False, type=bool)
        )
        self.minimize_to_tray_check.setChecked(
            self.settings.value("general/minimize_to_tray", False, type=bool)
        )
        self.confirm_exit_check.setChecked(
            self.settings.value("general/confirm_exit", True, type=bool)
        )
        
        # UI settings
        theme = self.settings.value("ui/theme", "system")
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        self.font_size_spin.setValue(
            self.settings.value("ui/font_size", 10, type=int)
        )
        self.auto_save_check.setChecked(
            self.settings.value("ui/auto_save", True, type=bool)
        )
        
        # Processing settings
        self.max_parallel_spin.setValue(
            self.settings.value("processing/max_parallel", 2, type=int)
        )
        self.memory_limit_spin.setValue(
            self.settings.value("processing/memory_limit", 2048, type=int)
        )
        self.temp_dir_edit.setText(
            self.settings.value("processing/temp_dir", "")
        )
        
        # Default settings
        engine = self.settings.value("defaults/engine", "spectral_gate")
        index = self.default_engine_combo.findData(engine)
        if index >= 0:
            self.default_engine_combo.setCurrentIndex(index)
        
        format = self.settings.value("defaults/format", "wav")
        index = self.default_format_combo.findData(format)
        if index >= 0:
            self.default_format_combo.setCurrentIndex(index)
        
        self.preserve_original_check.setChecked(
            self.settings.value("defaults/preserve_original", True, type=bool)
        )
        
        # Paths
        self.ffmpeg_path_edit.setText(
            self.settings.value("paths/ffmpeg", "")
        )
        self.output_pattern_edit.setText(
            self.settings.value("paths/output_pattern", "{parent}/clean/{name}_clean{ext}")
        )
        self.default_output_dir_edit.setText(
            self.settings.value("paths/default_output_dir", "")
        )
        self.rnnoise_models_edit.setText(
            self.settings.value("paths/rnnoise_models", "models")
        )
        
        # Advanced settings
        log_level = self.settings.value("advanced/log_level", "INFO")
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        
        self.max_log_files_spin.setValue(
            self.settings.value("advanced/max_log_files", 7, type=int)
        )
        self.log_to_file_check.setChecked(
            self.settings.value("advanced/log_to_file", True, type=bool)
        )
        self.enable_debug_check.setChecked(
            self.settings.value("advanced/enable_debug", False, type=bool)
        )
        self.keep_temp_files_check.setChecked(
            self.settings.value("advanced/keep_temp_files", False, type=bool)
        )
        self.verbose_ffmpeg_check.setChecked(
            self.settings.value("advanced/verbose_ffmpeg", False, type=bool)
        )
        
        # Test FFmpeg on load
        QTimer.singleShot(100, self._test_ffmpeg)
    
    def _save_settings(self) -> None:
        """Save current settings."""
        # General settings
        self.settings.setValue("general/check_updates", self.check_updates_check.isChecked())
        self.settings.setValue("general/minimize_to_tray", self.minimize_to_tray_check.isChecked())
        self.settings.setValue("general/confirm_exit", self.confirm_exit_check.isChecked())
        
        # UI settings
        self.settings.setValue("ui/theme", self.theme_combo.currentData())
        self.settings.setValue("ui/font_size", self.font_size_spin.value())
        self.settings.setValue("ui/auto_save", self.auto_save_check.isChecked())
        
        # Processing settings
        self.settings.setValue("processing/max_parallel", self.max_parallel_spin.value())
        self.settings.setValue("processing/memory_limit", self.memory_limit_spin.value())
        self.settings.setValue("processing/temp_dir", self.temp_dir_edit.text())
        
        # Default settings
        self.settings.setValue("defaults/engine", self.default_engine_combo.currentData())
        self.settings.setValue("defaults/format", self.default_format_combo.currentData())
        self.settings.setValue("defaults/preserve_original", self.preserve_original_check.isChecked())
        
        # Paths
        self.settings.setValue("paths/ffmpeg", self.ffmpeg_path_edit.text())
        self.settings.setValue("paths/output_pattern", self.output_pattern_edit.text())
        self.settings.setValue("paths/default_output_dir", self.default_output_dir_edit.text())
        self.settings.setValue("paths/rnnoise_models", self.rnnoise_models_edit.text())
        
        # Advanced settings
        self.settings.setValue("advanced/log_level", self.log_level_combo.currentText())
        self.settings.setValue("advanced/max_log_files", self.max_log_files_spin.value())
        self.settings.setValue("advanced/log_to_file", self.log_to_file_check.isChecked())
        self.settings.setValue("advanced/enable_debug", self.enable_debug_check.isChecked())
        self.settings.setValue("advanced/keep_temp_files", self.keep_temp_files_check.isChecked())
        self.settings.setValue("advanced/verbose_ffmpeg", self.verbose_ffmpeg_check.isChecked())
        
        self.settings.sync()
        logger.info("Preferences saved")
    
    def _apply_settings(self) -> None:
        """Apply current settings without closing dialog."""
        self._save_settings()
        QMessageBox.information(self, "Settings Applied", "Settings have been applied successfully.")
    
    def accept(self) -> None:
        """Accept dialog and save settings."""
        self._save_settings()
        super().accept()
    
    def reject(self) -> None:
        """Reject dialog without saving."""
        super().reject()