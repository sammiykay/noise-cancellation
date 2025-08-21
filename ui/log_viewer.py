"""Log viewer widget for displaying application logs."""

import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QComboBox, QLabel, QCheckBox, QGroupBox, QFileDialog,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QTimer, QFileSystemWatcher
from PySide6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

from utils.logging_setup import get_logger

logger = get_logger("log_viewer")


class LogViewer(QWidget):
    """Widget for viewing and filtering application logs."""
    
    def __init__(self):
        super().__init__()
        
        self.log_file_path: Optional[Path] = None
        self.last_position = 0
        self.max_lines = 1000
        self.auto_scroll = True
        
        # File watcher for real-time updates
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self._on_file_changed)
        
        self._setup_ui()
        self._setup_log_monitoring()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_logs)
        self.update_timer.start(2000)  # Update every 2 seconds
        
        logger.debug("Log viewer initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Application Logs")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Controls
        controls_group = QGroupBox("Log Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItem("All", "")
        self.level_combo.addItem("DEBUG", "DEBUG")
        self.level_combo.addItem("INFO", "INFO")
        self.level_combo.addItem("WARNING", "WARNING")
        self.level_combo.addItem("ERROR", "ERROR")
        self.level_combo.addItem("CRITICAL", "CRITICAL")
        self.level_combo.setCurrentText("All")
        self.level_combo.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.level_combo)
        
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter log messages...")
        self.search_input.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        controls_layout.addLayout(filter_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.auto_scroll_check = QCheckBox("Auto-scroll to bottom")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.toggled.connect(self._toggle_auto_scroll)
        options_layout.addWidget(self.auto_scroll_check)
        
        self.word_wrap_check = QCheckBox("Word wrap")
        self.word_wrap_check.setChecked(True)
        self.word_wrap_check.toggled.connect(self._toggle_word_wrap)
        options_layout.addWidget(self.word_wrap_check)
        
        options_layout.addStretch()
        controls_layout.addLayout(options_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_logs)
        button_layout.addWidget(self.clear_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_logs)
        button_layout.addWidget(self.refresh_button)
        
        self.save_button = QPushButton("Save Logs...")
        self.save_button.clicked.connect(self._save_logs)
        button_layout.addWidget(self.save_button)
        
        self.open_folder_button = QPushButton("Open Logs Folder")
        self.open_folder_button.clicked.connect(self._open_logs_folder)
        button_layout.addWidget(self.open_folder_button)
        
        button_layout.addStretch()
        controls_layout.addLayout(button_layout)
        
        layout.addWidget(controls_group)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        layout.addWidget(self.log_text)
        
        # Status
        self.status_label = QLabel("Loading logs...")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)
    
    def _setup_log_monitoring(self) -> None:
        """Set up log file monitoring."""
        # Find the current log file
        logs_dir = Path("logs")
        if logs_dir.exists():
            today = datetime.now().strftime("%Y%m%d")
            log_pattern = f"noise_cancellation-{today}.log"
            
            for log_file in logs_dir.glob("noise_cancellation-*.log"):
                if log_file.name.startswith(f"noise_cancellation-{today}"):
                    self.log_file_path = log_file
                    break
            else:
                # Use the most recent log file
                log_files = list(logs_dir.glob("noise_cancellation-*.log"))
                if log_files:
                    self.log_file_path = max(log_files, key=lambda f: f.stat().st_mtime)
        
        if self.log_file_path and self.log_file_path.exists():
            self.file_watcher.addPath(str(self.log_file_path))
            self.status_label.setText(f"Monitoring: {self.log_file_path.name}")
            self._load_initial_logs()
        else:
            self.status_label.setText("No log file found")
    
    def _load_initial_logs(self) -> None:
        """Load initial log content."""
        if not self.log_file_path or not self.log_file_path.exists():
            return
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # Keep only the last max_lines
                if len(lines) > self.max_lines:
                    lines = lines[-self.max_lines:]
                
                content = ''.join(lines)
                self.log_text.setPlainText(content)
                self.last_position = self.log_file_path.stat().st_size
                
                if self.auto_scroll:
                    self._scroll_to_bottom()
                
                self._apply_filters()
                
        except Exception as e:
            logger.error(f"Error loading initial logs: {e}")
            self.status_label.setText("Error loading logs")
    
    def _on_file_changed(self, path: str) -> None:
        """Handle log file changes."""
        # Schedule update on next timer cycle to avoid rapid updates
        if not self.update_timer.isActive():
            self.update_timer.start(500)
    
    def _update_logs(self) -> None:
        """Update logs with new content."""
        if not self.log_file_path or not self.log_file_path.exists():
            return
        
        try:
            current_size = self.log_file_path.stat().st_size
            
            if current_size <= self.last_position:
                return  # No new content
            
            # Read new content
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_content = f.read()
                
                if new_content.strip():
                    # Append new content
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    cursor.insertText(new_content)
                    
                    # Limit total lines
                    self._limit_text_lines()
                    
                    if self.auto_scroll:
                        self._scroll_to_bottom()
                    
                    self._apply_filters()
                
                self.last_position = current_size
                
        except Exception as e:
            logger.error(f"Error updating logs: {e}")
    
    def _limit_text_lines(self) -> None:
        """Limit text to maximum number of lines."""
        document = self.log_text.document()
        
        if document.blockCount() > self.max_lines:
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.Start)
            
            # Select excess lines
            lines_to_remove = document.blockCount() - self.max_lines
            for _ in range(lines_to_remove):
                cursor.movePosition(QTextCursor.EndOfBlock)
                cursor.movePosition(QTextCursor.NextBlock)
            
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
    
    def _apply_filters(self) -> None:
        """Apply level and search filters to log display."""
        if not self.log_text.toPlainText():
            return
        
        level_filter = self.level_combo.currentData()
        search_filter = self.search_input.text().lower()
        
        # Get all text
        full_text = self.log_text.toPlainText()
        lines = full_text.split('\n')
        
        # Apply filters
        filtered_lines = []
        for line in lines:
            # Level filter
            if level_filter and level_filter not in line:
                continue
            
            # Search filter
            if search_filter and search_filter not in line.lower():
                continue
            
            filtered_lines.append(line)
        
        # Update display with syntax highlighting
        self._display_filtered_lines(filtered_lines)
    
    def _display_filtered_lines(self, lines: List[str]) -> None:
        """Display filtered lines with syntax highlighting."""
        # Store cursor position
        was_at_end = self.log_text.textCursor().atEnd()
        
        # Clear and set new content
        self.log_text.clear()
        
        for line in lines:
            self._append_formatted_line(line)
        
        # Restore scroll position
        if was_at_end and self.auto_scroll:
            self._scroll_to_bottom()
    
    def _append_formatted_line(self, line: str) -> None:
        """Append a line with appropriate formatting."""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Create format based on log level
        format = QTextCharFormat()
        
        if " DEBUG " in line:
            format.setForeground(QColor(128, 128, 128))  # Gray
        elif " INFO " in line:
            format.setForeground(QColor(0, 0, 0))  # Black
        elif " WARNING " in line:
            format.setForeground(QColor(255, 140, 0))  # Orange
        elif " ERROR " in line:
            format.setForeground(QColor(255, 0, 0))  # Red
        elif " CRITICAL " in line:
            format.setForeground(QColor(255, 0, 0))  # Red
            format.setFontWeight(QFont.Bold)
        
        cursor.setCharFormat(format)
        cursor.insertText(line + '\n')
    
    def _scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the log display."""
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _toggle_auto_scroll(self, enabled: bool) -> None:
        """Toggle auto-scroll feature."""
        self.auto_scroll = enabled
        if enabled:
            self._scroll_to_bottom()
    
    def _toggle_word_wrap(self, enabled: bool) -> None:
        """Toggle word wrap in log display."""
        if enabled:
            self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            self.log_text.setLineWrapMode(QTextEdit.NoWrap)
    
    def _clear_logs(self) -> None:
        """Clear the log display."""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Clear the log display? This will only clear the viewer, not the log files.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.log_text.clear()
            logger.info("Log viewer cleared")
    
    def _refresh_logs(self) -> None:
        """Refresh logs from file."""
        if self.log_file_path:
            self.last_position = 0
            self._load_initial_logs()
            logger.info("Log viewer refreshed")
    
    def _save_logs(self) -> None:
        """Save current log display to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Logs",
            f"noise_cancellation_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                
                QMessageBox.information(
                    self,
                    "Logs Saved",
                    f"Logs saved to:\n{filename}"
                )
                logger.info(f"Logs saved to {filename}")
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save logs:\n{str(e)}"
                )
                logger.error(f"Failed to save logs: {e}")
    
    def _open_logs_folder(self) -> None:
        """Open the logs folder in system file explorer."""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
        
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", str(logs_dir)])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(logs_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(logs_dir)])
                
            logger.info("Opened logs folder")
            
        except Exception as e:
            logger.error(f"Failed to open logs folder: {e}")
            QMessageBox.information(
                self,
                "Logs Folder",
                f"Logs folder location:\n{logs_dir.absolute()}"
            )
    
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        # Stop file watching
        if self.file_watcher:
            self.file_watcher.removePaths(self.file_watcher.files())
        
        # Stop timer
        if self.update_timer:
            self.update_timer.stop()
        
        event.accept()