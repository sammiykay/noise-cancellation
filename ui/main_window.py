"""Main application window with tabbed interface."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QMenuBar, QStatusBar, QProgressBar, QLabel,
    QMessageBox, QFileDialog, QApplication, QFrame, QGroupBox,
    QGraphicsDropShadowEffect, QPushButton, QToolButton
)
from PySide6.QtCore import Qt, QTimer, Signal, QSettings, QSize, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PySide6.QtGui import QAction, QKeySequence, QIcon, QDragEnterEvent, QDropEvent, QLinearGradient, QPalette, QColor

from ui.file_list import FileListWidget
from ui.settings_panel import SettingsPanel
from ui.preview_panel import PreviewPanel
from ui.batch_processor import BatchProcessorWidget
from ui.preferences_dialog import PreferencesDialog
from ui.log_viewer import LogViewer
from ui.modern_styles import apply_modern_style
from utils.logging_setup import get_logger
from utils.paths import is_media_file
from core.pipeline import ProcessingJob, Engine

logger = get_logger("main_window")


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    files_added = Signal(list)  # List of Path objects
    processing_started = Signal()
    processing_stopped = Signal()
    
    def __init__(self, config_dir: Path = Path("config"), initial_files: Optional[List[Path]] = None):
        """
        Initialize main window.
        
        Args:
            config_dir: Directory for configuration files
            initial_files: Optional list of files to load on startup
        """
        super().__init__()
        
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)
        
        # Load settings
        self.settings = QSettings(
            str(self.config_dir / "settings.ini"),
            QSettings.IniFormat
        )
        
        # Initialize components first
        self._create_components()
        
        # Initialize UI
        self._setup_ui()
        self._setup_menus()
        self._setup_status_bar()
        self._connect_signals()
        self._restore_window_state()
        
        # Load initial files if provided
        if initial_files:
            QTimer.singleShot(100, lambda: self._add_files(initial_files))
        
        logger.info("Main window initialized")
    
    def _create_components(self) -> None:
        """Create all UI components before setting up the layout."""
        # Create file list widget
        self.file_list = FileListWidget()
        
        # Create batch processor widget
        self.batch_processor = BatchProcessorWidget()
        
        # Create settings panel
        self.settings_panel = SettingsPanel()
        
        # Create preview panel
        self.preview_panel = PreviewPanel()
        
        # Create log viewer
        self.log_viewer = LogViewer()
    
    def _setup_ui(self) -> None:
        """Set up the main user interface."""
        self.setWindowTitle("✨ Noise Cancellation Studio")
        self.setMinimumSize(800, 650)
        self.resize(950, 700)
        
        # Apply modern dark theme
        apply_modern_style(QApplication.instance())
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with minimal margins
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Header with title and quick actions
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Create main splitter with modern styling
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(8)
        main_layout.addWidget(main_splitter)
        
        # Left panel (file list and batch controls)
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel (settings, preview, logs)
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setStretchFactor(0, 1)  # Left panel
        main_splitter.setStretchFactor(1, 2)  # Right panel gets more space
        main_splitter.setSizes([300, 500])
        
        # Add animations to splitter
        self._setup_animations()
    
    def _create_header(self) -> QWidget:
        """Create compact header with title and quick actions."""
        header = QFrame()
        header.setProperty("class", "glass-card")
        header.setMaximumHeight(40)
        header.setMinimumHeight(40)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # App title - compact
        title = QLabel("🎵 Noise Cancellation Studio")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: white;
                margin: 0;
                padding: 0;
            }
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Compact action buttons
        add_files_btn = QPushButton("➕ Add")
        add_files_btn.setFixedSize(60, 26)
        add_files_btn.setProperty("class", "glow")
        add_files_btn.clicked.connect(self._add_files_dialog)
        layout.addWidget(add_files_btn)
        
        process_btn = QPushButton("▶ Process")
        process_btn.setFixedSize(70, 26)
        process_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #57f287, stop:1 #3ba55d);
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #67f297, stop:1 #4bb56d);
            }
        """)
        process_btn.clicked.connect(self._start_processing)
        layout.addWidget(process_btn)
        
        return header
    
    def _create_left_panel(self) -> QWidget:
        """Create the left panel with file list and batch controls."""
        panel = QFrame()
        panel.setProperty("class", "glass-card")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # Section title - compact
        files_title = QLabel("📁 File Queue")
        files_title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: 600;
                color: #a0a8b7;
                margin: 2px 0;
                padding: 0;
            }
        """)
        layout.addWidget(files_title)
        
        # File list widget with compact styling
        self.file_list.setStyleSheet("""
            QListWidget {
                background: rgba(10, 15, 30, 0.4);
                border: 1px solid rgba(88, 101, 242, 0.2);
                border-radius: 6px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 6px;
                margin: 1px 0;
                background: rgba(255, 255, 255, 0.03);
                border-radius: 3px;
                min-height: 14px;
                font-size: 12px;
            }
            QListWidget::item:hover {
                background: rgba(88, 101, 242, 0.15);
            }
            QListWidget::item:selected {
                background: rgba(88, 101, 242, 0.3);
            }
        """)
        layout.addWidget(self.file_list)
        
        # Batch processor controls with compact styling
        self.batch_processor.setStyleSheet("""
            QWidget {
                background: rgba(88, 101, 242, 0.08);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.batch_processor)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create the right panel with tabs for settings and preview, plus logs at bottom."""
        right_panel = QFrame()
        right_panel.setProperty("class", "glass-card")
        
        layout = QVBoxLayout(right_panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # Create tab widget with modern styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background: rgba(20, 25, 40, 0.6);
                border: 2px solid rgba(88, 101, 242, 0.2);
                border-radius: 8px;
                padding: 4px;
            }
            QTabBar::tab {
                padding: 6px 12px;
                margin: 0 1px;
                font-size: 12px;
                font-weight: 600;
                min-width: 80px;
            }
        """)
        
        # Settings tab with icon (already created)
        self.tab_widget.addTab(self.settings_panel, "⚙️ Settings")
        
        # Preview tab with icon (already created)
        self.tab_widget.addTab(self.preview_panel, "👁️ Preview")
        
        layout.addWidget(self.tab_widget, stretch=2)  # Reduce tab space
        
        # Log viewer with expanded styling for better readability
        logs_group = QGroupBox("📋 Processing Logs")
        logs_group.setMinimumHeight(150)
        logs_group.setStyleSheet("""
            QGroupBox {
                background: rgba(10, 15, 30, 0.4);
                border: 2px solid rgba(88, 101, 242, 0.2);
                border-radius: 8px;
                padding-top: 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QGroupBox::title {
                color: #a0a8b7;
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        logs_layout = QVBoxLayout(logs_group)
        logs_layout.setContentsMargins(8, 8, 8, 8)
        logs_layout.setSpacing(4)
        
        # Log viewer with expanded styling for better readability
        self.log_viewer.setMinimumHeight(120)
        self.log_viewer.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(88, 101, 242, 0.15);
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.3;
                color: #e4e7eb;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(88, 101, 242, 0.5);
                min-height: 20px;
                border-radius: 6px;
            }
        """)
        logs_layout.addWidget(self.log_viewer)
        
        layout.addWidget(logs_group, stretch=2)  # More space for logs
        
        return right_panel
    
    def _start_processing(self) -> None:
        """Start processing with error handling."""
        try:
            if hasattr(self.batch_processor, 'start_processing'):
                self.batch_processor.start_processing()
            else:
                logger.warning("Batch processor not properly initialized")
        except Exception as e:
            logger.error(f"Error starting processing: {e}")
    
    def _setup_animations(self) -> None:
        """Set up animations for UI elements."""
        # Add fade-in animation on startup
        self.setWindowOpacity(0)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.fade_animation.start()
    
    def _setup_menus(self) -> None:
        """Set up application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        add_files_action = QAction("&Add Files...", self)
        add_files_action.setShortcut(QKeySequence.Open)
        add_files_action.setStatusTip("Add audio or video files for processing")
        add_files_action.triggered.connect(self._add_files_dialog)
        file_menu.addAction(add_files_action)
        
        add_folder_action = QAction("Add &Folder...", self)
        add_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        add_folder_action.setStatusTip("Add all media files from a folder")
        add_folder_action.triggered.connect(self._add_folder_dialog)
        file_menu.addAction(add_folder_action)
        
        file_menu.addSeparator()
        
        clear_list_action = QAction("&Clear List", self)
        clear_list_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        clear_list_action.setStatusTip("Clear all files from the list")
        clear_list_action.triggered.connect(self.file_list.clear)
        file_menu.addAction(clear_list_action)
        
        file_menu.addSeparator()
        
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut(QKeySequence.Preferences)
        preferences_action.setStatusTip("Open application preferences")
        preferences_action.triggered.connect(self._show_preferences)
        file_menu.addAction(preferences_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Processing menu
        process_menu = menubar.addMenu("&Processing")
        
        start_batch_action = QAction("&Start Batch Processing", self)
        start_batch_action.setShortcut(QKeySequence("Ctrl+Return"))
        start_batch_action.setStatusTip("Start processing all files in the queue")
        start_batch_action.triggered.connect(self.batch_processor.start_processing)
        process_menu.addAction(start_batch_action)
        
        pause_batch_action = QAction("&Pause Processing", self)
        pause_batch_action.setShortcut(QKeySequence("Ctrl+P"))
        pause_batch_action.setStatusTip("Pause batch processing")
        pause_batch_action.triggered.connect(self.batch_processor.pause_processing)
        process_menu.addAction(pause_batch_action)
        
        stop_batch_action = QAction("&Stop Processing", self)
        stop_batch_action.setShortcut(QKeySequence("Ctrl+S"))
        stop_batch_action.setStatusTip("Stop batch processing")
        stop_batch_action.triggered.connect(self.batch_processor.stop_processing)
        process_menu.addAction(stop_batch_action)
        
        process_menu.addSeparator()
        
        preview_action = QAction("&Preview Current Selection", self)
        preview_action.setShortcut(QKeySequence.Print)
        preview_action.setStatusTip("Preview noise reduction on selected file")
        preview_action.triggered.connect(self._preview_current_selection)
        process_menu.addAction(preview_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        show_settings_action = QAction("&Settings Panel", self)
        show_settings_action.setShortcut(QKeySequence("Ctrl+1"))
        show_settings_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(show_settings_action)
        
        show_preview_action = QAction("&Preview Panel", self)
        show_preview_action.setShortcut(QKeySequence("Ctrl+2"))
        show_preview_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(show_preview_action)
        
        show_logs_action = QAction("&Log Panel", self)
        show_logs_action.setShortcut(QKeySequence("Ctrl+3"))
        show_logs_action.triggered.connect(lambda: self.log_viewer.setFocus())
        view_menu.addAction(show_logs_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        # Store actions for enabling/disabling
        self.start_batch_action = start_batch_action
        self.pause_batch_action = pause_batch_action
        self.stop_batch_action = stop_batch_action
        self.preview_action = preview_action
        
        # Initial state
        self.pause_batch_action.setEnabled(False)
        self.stop_batch_action.setEnabled(False)
    
    def _setup_status_bar(self) -> None:
        """Set up the status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: rgba(15, 20, 35, 0.9);
                border-top: 1px solid rgba(88, 101, 242, 0.2);
                padding: 4px;
                max-height: 28px;
            }
        """)
        
        # Main status label with icon
        self.status_label = QLabel("✅ Ready")
        self.status_label.setStyleSheet("font-size: 12px; color: #57f287; padding: 4px;")
        self.status_bar.addWidget(self.status_label, 1)
        
        # Compact progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                height: 16px;
                text-align: center;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4752c4, stop:0.5 #5865f2, stop:1 #6574ff);
                border-radius: 8px;
            }
        """)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # File count label with icon
        self.file_count_label = QLabel("📄 0 files")
        self.file_count_label.setStyleSheet("font-size: 12px; color: #a0a8b7; padding: 4px;")
        self.status_bar.addPermanentWidget(self.file_count_label)
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # File list signals
        self.file_list.files_changed.connect(self._update_file_count)
        self.file_list.selection_changed.connect(self._update_preview)
        
        # Batch processor signals
        self.batch_processor.processing_started.connect(self._on_processing_started)
        self.batch_processor.processing_finished.connect(self._on_processing_finished)
        self.batch_processor.progress_updated.connect(self._update_progress)
        
        # Settings panel signals
        self.settings_panel.settings_changed.connect(self._apply_settings)
        
        # Internal signals
        self.files_added.connect(self.file_list.add_files)
    
    def _restore_window_state(self) -> None:
        """Restore window size and position from settings."""
        self.resize(
            self.settings.value("window/width", 1200, type=int),
            self.settings.value("window/height", 800, type=int)
        )
        
        # Restore window position if available
        pos = self.settings.value("window/position")
        if pos:
            self.move(pos)
        
        # Restore window state
        state = self.settings.value("window/state")
        if state:
            self.restoreState(state)
    
    def _save_window_state(self) -> None:
        """Save window size and position to settings."""
        self.settings.setValue("window/width", self.width())
        self.settings.setValue("window/height", self.height())
        self.settings.setValue("window/position", self.pos())
        self.settings.setValue("window/state", self.saveState())
    
    def _add_files_dialog(self) -> None:
        """Show file dialog to add files."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(
            "Media Files (*.wav *.mp3 *.flac *.aac *.ogg *.m4a *.mp4 *.avi *.mkv *.mov *.wmv *.webm);;"
            "Audio Files (*.wav *.mp3 *.flac *.aac *.ogg *.m4a);;"
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.webm);;"
            "All Files (*.*)"
        )
        
        if file_dialog.exec():
            files = [Path(f) for f in file_dialog.selectedFiles()]
            self._add_files(files)
    
    def _add_folder_dialog(self) -> None:
        """Show folder dialog to add all media files from a folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder:
            folder_path = Path(folder)
            media_files = []
            
            # Find all media files in folder and subfolders
            for pattern in ["*.wav", "*.mp3", "*.flac", "*.aac", "*.ogg", "*.m4a", 
                          "*.mp4", "*.avi", "*.mkv", "*.mov", "*.wmv", "*.webm"]:
                media_files.extend(folder_path.rglob(pattern))
            
            if media_files:
                self._add_files(media_files)
                self.status_label.setText(f"Added {len(media_files)} files from {folder}")
            else:
                QMessageBox.information(
                    self,
                    "No Media Files",
                    f"No supported media files found in {folder}"
                )
    
    def _add_files(self, files: List[Path]) -> None:
        """Add files to the processing queue."""
        valid_files = [f for f in files if f.exists() and is_media_file(f)]
        
        if valid_files:
            self.files_added.emit(valid_files)
            logger.info(f"Added {len(valid_files)} files to queue")
        
        invalid_count = len(files) - len(valid_files)
        if invalid_count > 0:
            logger.warning(f"Skipped {invalid_count} invalid or unsupported files")
    
    def _update_file_count(self, count: int) -> None:
        """Update file count in status bar."""
        self.file_count_label.setText(f"📄 {count} files")
    
    def _update_preview(self, file_path: Optional[Path]) -> None:
        """Update preview panel when selection changes."""
        if file_path:
            self.preview_panel.load_file(file_path)
            self.preview_action.setEnabled(True)
        else:
            self.preview_panel.clear()
            self.preview_action.setEnabled(False)
    
    def _preview_current_selection(self) -> None:
        """Preview processing on currently selected file."""
        current_file = self.file_list.get_current_file()
        if current_file:
            settings = self.settings_panel.get_current_settings()
            self.preview_panel.preview_processing(current_file, settings)
    
    def _apply_settings(self, settings: Dict[str, Any]) -> None:
        """Apply settings changes."""
        # Update batch processor with new settings
        self.batch_processor.update_settings(settings)
        logger.debug("Settings applied")
    
    def _on_processing_started(self) -> None:
        """Handle processing start."""
        self.status_label.setText("⚡ Processing...")
        self.status_label.setStyleSheet("font-size: 14px; color: #5865f2;")
        self.progress_bar.setVisible(True)
        
        # Add pulsing animation to progress bar
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"styleSheet")
        self.progress_animation.setDuration(1000)
        self.progress_animation.setLoopCount(-1)  # Infinite loop
        self.progress_animation.setKeyValueAt(0, self.progress_bar.styleSheet())
        self.progress_animation.setKeyValueAt(0.5, self.progress_bar.styleSheet() + "opacity: 0.7;")
        self.progress_animation.setKeyValueAt(1, self.progress_bar.styleSheet())
        self.progress_animation.start()
        
        # Focus on logs to show processing activity (logs are now always visible)
        self.log_viewer.setFocus()
        
        # Update menu states
        self.start_batch_action.setEnabled(False)
        self.pause_batch_action.setEnabled(True)
        self.stop_batch_action.setEnabled(True)
        
        self.processing_started.emit()
    
    def _on_processing_finished(self) -> None:
        """Handle processing completion."""
        self.status_label.setText("✅ Processing complete")
        self.status_label.setStyleSheet("font-size: 14px; color: #57f287;")
        self.progress_bar.setVisible(False)
        
        # Stop animation if it exists
        if hasattr(self, 'progress_animation'):
            self.progress_animation.stop()
        
        # Update menu states
        self.start_batch_action.setEnabled(True)
        self.pause_batch_action.setEnabled(False)
        self.stop_batch_action.setEnabled(False)
        
        self.processing_stopped.emit()
    
    def _update_progress(self, current: int, total: int, message: str) -> None:
        """Update progress bar and status."""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.status_label.setText(f"⚡ Processing {current}/{total}: {message}")
            self.status_label.setStyleSheet("font-size: 14px; color: #5865f2;")
    
    def _show_preferences(self) -> None:
        """Show preferences dialog."""
        dialog = PreferencesDialog(self, self.config_dir)
        if dialog.exec():
            # Apply preferences
            logger.info("Preferences updated")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Noise Cancellation",
            "<h3>✨ Noise Cancellation Studio v2.0</h3>"
            "<p>A desktop application for removing background noise from audio and video files.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Multiple noise reduction engines (Spectral Gate, RNNoise, Demucs)</li>"
            "<li>Batch processing with drag-and-drop support</li>"
            "<li>Real-time preview with waveform visualization</li>"
            "<li>Video remuxing to preserve video streams</li>"
            "<li>Professional audio processing pipeline</li>"
            "</ul>"
            "<p><b>Technologies:</b> Python, PySide6, FFmpeg, librosa, numpy</p>"
        )
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events."""
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(Path(url.toLocalFile()))
        
        if files:
            self._add_files(files)
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Stop any running processing
        if self.batch_processor.is_processing():
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "Batch processing is currently running. Do you want to stop and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.batch_processor.stop_processing()
            else:
                event.ignore()
                return
        
        # Save window state
        self._save_window_state()
        
        # Save settings panel state
        self.settings_panel.save_settings()
        
        logger.info("Application closing")
        event.accept()