"""Preview panel with waveform visualization and processing preview."""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QSpinBox, QGroupBox, QProgressBar, QTextEdit,
    QSplitter, QFrame, QScrollArea, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QFont

from utils.logging_setup import get_logger
from core.media import load_audio, get_audio_duration
from core.pipeline import ProcessingPipeline, ProcessingJob, Engine

logger = get_logger("preview_panel")


class PreviewWorker(QObject):
    """Worker for background audio processing."""
    
    # Signals
    processing_started = Signal()
    processing_progress = Signal(float, str)  # progress, message
    processing_finished = Signal(object)  # processed audio array
    processing_failed = Signal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.should_cancel = False
        
    def process_audio(self, audio: np.ndarray, sample_rate: int, settings: Dict[str, Any]) -> None:
        """Process audio with given settings."""
        try:
            self.should_cancel = False
            self.processing_started.emit()
            
            # Create processing job
            from tempfile import NamedTemporaryFile
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            job = ProcessingJob(
                input_path=temp_path,
                engine=Engine(settings.get('engine', 'spectral_gate')),
                engine_config=settings.get('engine_config', {}),
                output_format='wav',
                sample_rate=None,
                preserve_video=False,
                normalize_loudness=settings.get('normalize_loudness', False),
                target_lufs=settings.get('target_lufs', -23.0)
            )
            
            # Create pipeline
            pipeline = ProcessingPipeline()
            
            def progress_callback(current_job: ProcessingJob) -> None:
                if self.should_cancel:
                    raise RuntimeError("Processing cancelled")
                self.processing_progress.emit(current_job.progress, current_job.message)
            
            # Set audio data directly
            job._audio_data = audio
            job._sample_rate = sample_rate
            
            # Apply noise reduction
            engine_config = settings.get('engine_config', {})
            engine = pipeline._get_engine(Engine(settings['engine']), engine_config)
            
            processed_audio = engine.process(
                audio, sample_rate, progress_callback=lambda p, m: progress_callback(job)
            )
            
            if not self.should_cancel:
                self.processing_finished.emit(processed_audio)
            
        except Exception as e:
            if not self.should_cancel:
                self.processing_failed.emit(str(e))
                logger.error(f"Preview processing failed: {e}")
    
    def cancel_processing(self) -> None:
        """Cancel current processing."""
        self.should_cancel = True


class WaveformWidget(QWidget):
    """Widget for displaying audio waveform."""
    
    def __init__(self):
        super().__init__()
        
        self.audio_data: Optional[np.ndarray] = None
        self.sample_rate: Optional[int] = None
        self.start_sample = 0
        self.zoom_factor = 1.0
        
        self.setMinimumHeight(100)
        self.setStyleSheet("background-color: black; border: 1px solid gray;")
    
    def set_audio(self, audio: np.ndarray, sample_rate: int) -> None:
        """Set audio data for visualization."""
        self.audio_data = audio
        self.sample_rate = sample_rate
        self.start_sample = 0
        self.zoom_factor = 1.0
        self.update()
    
    def set_zoom(self, zoom_factor: float) -> None:
        """Set zoom factor."""
        self.zoom_factor = max(0.1, min(10.0, zoom_factor))
        self.update()
    
    def set_position(self, start_sample: int) -> None:
        """Set start position."""
        if self.audio_data is not None:
            max_start = max(0, len(self.audio_data) - int(self.width() * self.zoom_factor))
            self.start_sample = max(0, min(start_sample, max_start))
            self.update()
    
    def paintEvent(self, event) -> None:
        """Paint the waveform."""
        if self.audio_data is None:
            super().paintEvent(event)
            return
        
        from PySide6.QtGui import QPainter, QPen, QColor
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_y = height // 2
        
        # Convert stereo to mono for display
        if len(self.audio_data.shape) > 1:
            display_audio = np.mean(self.audio_data, axis=1)
        else:
            display_audio = self.audio_data
        
        # Calculate samples per pixel
        samples_per_pixel = max(1, int(len(display_audio) / (width * self.zoom_factor)))
        
        # Draw waveform
        painter.setPen(QPen(QColor(0, 255, 0), 1))
        
        for x in range(width):
            start_idx = self.start_sample + x * samples_per_pixel
            end_idx = min(start_idx + samples_per_pixel, len(display_audio))
            
            if start_idx >= len(display_audio):
                break
            
            # Get min/max for this pixel column
            segment = display_audio[start_idx:end_idx]
            if len(segment) > 0:
                min_val = np.min(segment)
                max_val = np.max(segment)
                
                # Scale to widget height
                min_y = center_y - int(min_val * center_y)
                max_y = center_y - int(max_val * center_y)
                
                # Draw vertical line
                painter.drawLine(x, min_y, x, max_y)
        
        painter.end()
    
    def wheelEvent(self, event) -> None:
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.set_zoom(self.zoom_factor * 1.2)
        else:
            self.set_zoom(self.zoom_factor / 1.2)
        
        event.accept()


class PreviewPanel(QWidget):
    """Panel for previewing audio and processing results."""
    
    def __init__(self):
        super().__init__()
        
        self.current_file: Optional[Path] = None
        self.original_audio: Optional[np.ndarray] = None
        self.processed_audio: Optional[np.ndarray] = None
        self.sample_rate: Optional[int] = None
        self.preview_start = 0.0
        self.preview_duration = 10.0
        
        # Preview worker
        self.worker_thread = QThread()
        self.worker = PreviewWorker()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        
        self._setup_ui()
        self._connect_signals()
        
        logger.debug("Preview panel initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Header - compact
        header_layout = QHBoxLayout()
        header_label = QLabel("👁️ Audio Preview")
        header_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #a0a8b7;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # File info - compact
        self.file_info_label = QLabel("🎧 No file selected")
        self.file_info_label.setStyleSheet("color: #a0a8b7; font-size: 9px; padding: 2px;")
        layout.addWidget(self.file_info_label)
        
        # Preview controls - compact
        controls_group = QGroupBox("⚙️ Settings")
        controls_group.setMaximumHeight(80)
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(4, 4, 4, 4)
        controls_layout.setSpacing(2)
        
        # Time range selection - compact
        range_layout = QHBoxLayout()
        range_layout.setSpacing(4)
        
        start_label = QLabel("Start:")
        start_label.setStyleSheet("font-size: 10px;")
        range_layout.addWidget(start_label)
        
        self.start_time_spin = QSpinBox()
        self.start_time_spin.setRange(0, 3600)
        self.start_time_spin.setSuffix("s")
        self.start_time_spin.setMaximumHeight(22)
        self.start_time_spin.setMaximumWidth(65)
        self.start_time_spin.valueChanged.connect(self._update_preview_range)
        self.start_time_spin.setStyleSheet("""
            QSpinBox {
                background: rgba(30, 35, 50, 0.9);
                border: 1px solid rgba(88, 101, 242, 0.4);
                border-radius: 4px;
                padding: 2px 4px;
                padding-right: 18px;
                font-size: 10px;
                font-weight: 600;
            }
        """)
        range_layout.addWidget(self.start_time_spin)
        
        dur_label = QLabel("Duration:")
        dur_label.setStyleSheet("font-size: 10px;")
        range_layout.addWidget(dur_label)
        
        self.duration_combo = QComboBox()
        self.duration_combo.addItem("5s", 5.0)
        self.duration_combo.addItem("10s", 10.0)
        self.duration_combo.addItem("15s", 15.0)
        self.duration_combo.addItem("30s", 30.0)
        self.duration_combo.setCurrentIndex(1)  # 10 seconds default
        self.duration_combo.setMaximumHeight(22)
        self.duration_combo.setMaximumWidth(60)
        self.duration_combo.currentTextChanged.connect(self._update_preview_range)
        range_layout.addWidget(self.duration_combo)
        
        range_layout.addStretch()
        controls_layout.addLayout(range_layout)
        
        # Preview buttons - compact
        button_layout = QHBoxLayout()
        button_layout.setSpacing(2)
        
        self.preview_button = QPushButton("▶ Preview")
        self.preview_button.setEnabled(False)
        self.preview_button.setFixedHeight(22)
        self.preview_button.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        self.preview_button.clicked.connect(self._start_preview)
        button_layout.addWidget(self.preview_button)
        
        self.play_original_button = QPushButton("🔊 Orig")
        self.play_original_button.setEnabled(False)
        self.play_original_button.setFixedHeight(22)
        self.play_original_button.setStyleSheet("font-size: 10px; padding: 2px 4px;")
        self.play_original_button.clicked.connect(self._play_original)
        button_layout.addWidget(self.play_original_button)
        
        self.play_processed_button = QPushButton("🔊 Clean")
        self.play_processed_button.setEnabled(False)
        self.play_processed_button.setFixedHeight(22)
        self.play_processed_button.setStyleSheet("font-size: 10px; padding: 2px 4px;")
        self.play_processed_button.clicked.connect(self._play_processed)
        button_layout.addWidget(self.play_processed_button)
        
        button_layout.addStretch()
        controls_layout.addLayout(button_layout)
        
        layout.addWidget(controls_group)
        
        # Progress bar - compact
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(16)
        layout.addWidget(self.progress_bar)
        
        # Waveform display - compact
        waveform_group = QGroupBox("🎦 Waveform")
        waveform_group.setMaximumHeight(120)
        waveform_layout = QVBoxLayout(waveform_group)
        waveform_layout.setContentsMargins(4, 4, 4, 4)
        waveform_layout.setSpacing(2)
        
        # Original waveform - compact
        original_label = QLabel("🔵 Original")
        original_label.setStyleSheet("font-weight: bold; color: #5865f2; font-size: 10px;")
        waveform_layout.addWidget(original_label)
        
        self.original_waveform = WaveformWidget()
        self.original_waveform.setMaximumHeight(40)
        waveform_layout.addWidget(self.original_waveform)
        
        # Processed waveform - compact
        processed_label = QLabel("🟢 Processed")
        processed_label.setStyleSheet("font-weight: bold; color: #57f287; font-size: 10px;")
        waveform_layout.addWidget(processed_label)
        
        self.processed_waveform = WaveformWidget()
        self.processed_waveform.setMaximumHeight(40)
        waveform_layout.addWidget(self.processed_waveform)
        
        layout.addWidget(waveform_group)
        
        # Status/info area - compact
        info_group = QGroupBox("📈 Analysis")
        info_group.setMaximumHeight(80)
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(4, 4, 4, 4)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setMaximumHeight(60)
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(10, 15, 30, 0.3);
                color: #e4e7eb;
                font-family: 'Consolas', monospace;
                font-size: 9px;
                border: 1px solid rgba(88, 101, 242, 0.2);
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.analysis_text.setPlainText("📋 Ready for audio analysis...")
        info_layout.addWidget(self.analysis_text)
        
        layout.addWidget(info_group)
        
        # Remove stretch to make content visible
        # layout.addStretch()
    
    def _connect_signals(self) -> None:
        """Connect worker signals."""
        self.worker.processing_started.connect(self._on_processing_started)
        self.worker.processing_progress.connect(self._on_processing_progress)
        self.worker.processing_finished.connect(self._on_processing_finished)
        self.worker.processing_failed.connect(self._on_processing_failed)
    
    def load_file(self, file_path: Path) -> None:
        """Load audio file for preview."""
        try:
            self.current_file = file_path
            
            # Update file info
            duration = get_audio_duration(file_path)
            if duration:
                self.file_info_label.setText(
                    f"File: {file_path.name} ({duration:.1f}s)"
                )
                self.start_time_spin.setMaximum(int(duration))
            else:
                self.file_info_label.setText(f"File: {file_path.name}")
            
            # Load audio segment for preview
            self._load_preview_segment()
            
        except Exception as e:
            logger.error(f"Error loading file for preview: {e}")
            self.file_info_label.setText(f"Error loading: {file_path.name}")
    
    def _load_preview_segment(self) -> None:
        """Load the selected preview segment."""
        if not self.current_file:
            return
        
        try:
            # Get preview range
            start_time = self.start_time_spin.value()
            duration = self.duration_combo.currentData()
            
            # Load audio segment
            result = load_audio(
                self.current_file,
                sample_rate=None,
                mono=False,
                start_time=start_time,
                duration=duration
            )
            
            if result is None:
                logger.error("Failed to load audio segment")
                return
            
            self.original_audio, self.sample_rate = result
            self.processed_audio = None
            
            # Update waveform display
            self.original_waveform.set_audio(self.original_audio, self.sample_rate)
            self.processed_waveform.set_audio(
                np.zeros_like(self.original_audio), self.sample_rate
            )
            
            # Enable preview controls
            self.preview_button.setEnabled(True)
            self.play_original_button.setEnabled(True)
            self.play_processed_button.setEnabled(False)
            
            # Update analysis
            self._update_analysis()
            
            logger.debug(f"Loaded preview segment: {start_time}s - {start_time + duration}s")
            
        except Exception as e:
            logger.error(f"Error loading preview segment: {e}")
    
    def _update_preview_range(self) -> None:
        """Update preview range when controls change."""
        if self.current_file:
            QTimer.singleShot(100, self._load_preview_segment)
    
    def preview_processing(self, file_path: Path, settings: Dict[str, Any]) -> None:
        """Preview processing with given settings."""
        if file_path != self.current_file:
            self.load_file(file_path)
        
        if self.original_audio is None:
            return
        
        # Store settings for processing
        self.current_settings = settings
        
        # Start preview processing
        self._start_preview()
    
    def _start_preview(self) -> None:
        """Start preview processing."""
        if self.original_audio is None:
            return
        
        # Get current settings from main window
        main_window = self.window()
        if hasattr(main_window, 'settings_panel'):
            settings = main_window.settings_panel.get_current_settings()
        else:
            # Fallback settings
            settings = {
                'engine': 'spectral_gate',
                'engine_config': {'reduction_db': 20.0}
            }
        
        # Start processing in worker thread
        QTimer.singleShot(0, lambda: self.worker.process_audio(
            self.original_audio, self.sample_rate, settings
        ))
    
    def _play_original(self) -> None:
        """Play original audio segment."""
        if self.original_audio is not None:
            self._play_audio(self.original_audio)
    
    def _play_processed(self) -> None:
        """Play processed audio segment."""
        if self.processed_audio is not None:
            self._play_audio(self.processed_audio)
    
    def _play_audio(self, audio: np.ndarray) -> None:
        """Play audio using system default player."""
        try:
            import tempfile
            import subprocess
            import platform
            from core.media import save_audio
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            if save_audio(audio, temp_path, self.sample_rate):
                # Play with system default
                system = platform.system()
                if system == "Windows":
                    subprocess.run(["start", str(temp_path)], shell=True, check=False)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", str(temp_path)], check=False)
                else:  # Linux
                    subprocess.run(["xdg-open", str(temp_path)], check=False)
                
                logger.info("Playing audio segment")
            else:
                logger.error("Failed to save temporary audio file")
                
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def _on_processing_started(self) -> None:
        """Handle processing start."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.preview_button.setEnabled(False)
        self.preview_button.setText("Processing...")
    
    def _on_processing_progress(self, progress: float, message: str) -> None:
        """Handle processing progress."""
        self.progress_bar.setValue(int(progress * 100))
    
    def _on_processing_finished(self, processed_audio: np.ndarray) -> None:
        """Handle processing completion."""
        self.processed_audio = processed_audio
        
        # Update processed waveform
        self.processed_waveform.set_audio(processed_audio, self.sample_rate)
        
        # Enable controls
        self.progress_bar.setVisible(False)
        self.preview_button.setEnabled(True)
        self.preview_button.setText("Preview Processing")
        self.play_processed_button.setEnabled(True)
        
        # Update analysis
        self._update_analysis()
        
        logger.info("Preview processing completed")
    
    def _on_processing_failed(self, error_message: str) -> None:
        """Handle processing failure."""
        self.progress_bar.setVisible(False)
        self.preview_button.setEnabled(True)
        self.preview_button.setText("Preview Processing")
        
        self.analysis_text.setText(f"Processing failed: {error_message}")
        logger.error(f"Preview processing failed: {error_message}")
    
    def _update_analysis(self) -> None:
        """Update analysis information."""
        if self.original_audio is None:
            self.analysis_text.clear()
            return
        
        analysis_lines = []
        
        # Original audio stats
        original_rms = np.sqrt(np.mean(self.original_audio ** 2))
        original_peak = np.max(np.abs(self.original_audio))
        
        analysis_lines.append("=== ORIGINAL ===")
        analysis_lines.append(f"RMS: {20 * np.log10(original_rms + 1e-10):.2f} dB")
        analysis_lines.append(f"Peak: {20 * np.log10(original_peak + 1e-10):.2f} dB")
        analysis_lines.append(f"Duration: {len(self.original_audio) / self.sample_rate:.2f}s")
        analysis_lines.append(f"Channels: {1 if len(self.original_audio.shape) == 1 else self.original_audio.shape[1]}")
        
        # Processed audio stats
        if self.processed_audio is not None:
            processed_rms = np.sqrt(np.mean(self.processed_audio ** 2))
            processed_peak = np.max(np.abs(self.processed_audio))
            
            analysis_lines.append("")
            analysis_lines.append("=== PROCESSED ===")
            analysis_lines.append(f"RMS: {20 * np.log10(processed_rms + 1e-10):.2f} dB")
            analysis_lines.append(f"Peak: {20 * np.log10(processed_peak + 1e-10):.2f} dB")
            
            # Noise reduction estimate
            if original_rms > 0 and processed_rms > 0:
                reduction_db = 20 * np.log10(original_rms / processed_rms)
                analysis_lines.append(f"RMS Change: {reduction_db:.2f} dB")
        
        self.analysis_text.setText("\n".join(analysis_lines))
    
    def clear(self) -> None:
        """Clear preview panel."""
        self.current_file = None
        self.original_audio = None
        self.processed_audio = None
        self.sample_rate = None
        
        self.file_info_label.setText("No file loaded")
        self.analysis_text.clear()
        
        # Reset waveforms
        dummy_audio = np.zeros(1000)
        self.original_waveform.set_audio(dummy_audio, 44100)
        self.processed_waveform.set_audio(dummy_audio, 44100)
        
        # Disable controls
        self.preview_button.setEnabled(False)
        self.play_original_button.setEnabled(False)
        self.play_processed_button.setEnabled(False)
    
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        # Cancel any running processing
        if self.worker:
            self.worker.cancel_processing()
        
        # Clean up worker thread
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(3000)
        
        event.accept()