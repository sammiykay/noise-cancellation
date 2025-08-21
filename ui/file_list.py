"""File list widget for managing audio/video files."""

from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QProgressBar, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QMimeData, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPixmap, QPainter, QBrush

from utils.logging_setup import get_logger
from utils.paths import is_media_file, is_video_file
from core.pipeline import ProcessingJob, ProcessingStage

logger = get_logger("file_list")


class FileStatus(Enum):
    """File processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class FileItem(QListWidgetItem):
    """Custom list item for files with status tracking."""
    
    def __init__(self, file_path: Path):
        super().__init__()
        
        self.file_path = file_path
        self.status = FileStatus.PENDING
        self.progress = 0.0
        self.message = ""
        self.error_message = ""
        self.output_path: Optional[Path] = None
        self.processing_job: Optional[ProcessingJob] = None
        
        self._update_display()
    
    def _update_display(self) -> None:
        """Update the display text and icon."""
        # Set main text
        filename = self.file_path.name
        if len(filename) > 50:
            filename = filename[:47] + "..."
        
        text = filename
        
        # Add status information
        if self.status == FileStatus.PROCESSING:
            text += f" ({self.progress:.0f}%"
            if self.message:
                text += f" - {self.message}"
            text += ")"
        elif self.status == FileStatus.COMPLETED:
            text += " ✓"
        elif self.status == FileStatus.ERROR:
            text += " ✗"
            if self.error_message:
                text += f" - {self.error_message}"
        elif self.status == FileStatus.CANCELLED:
            text += " (cancelled)"
        
        self.setText(text)
        
        # Set icon based on file type
        if is_video_file(self.file_path):
            self.setIcon(self._create_video_icon())
        else:
            self.setIcon(self._create_audio_icon())
        
        # Set tooltip
        tooltip_parts = [
            f"Path: {self.file_path}",
            f"Status: {self.status.value}"
        ]
        
        if self.output_path:
            tooltip_parts.append(f"Output: {self.output_path}")
        
        if self.error_message:
            tooltip_parts.append(f"Error: {self.error_message}")
        
        self.setToolTip("\n".join(tooltip_parts))
    
    def _create_audio_icon(self) -> QIcon:
        """Create audio file icon."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setBrush(QBrush(Qt.blue))
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        
        return QIcon(pixmap)
    
    def _create_video_icon(self) -> QIcon:
        """Create video file icon."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setBrush(QBrush(Qt.red))
        painter.drawRect(2, 2, 12, 12)
        painter.end()
        
        return QIcon(pixmap)
    
    def update_status(self, status: FileStatus, progress: float = 0.0, 
                     message: str = "", error_message: str = "") -> None:
        """Update item status and refresh display."""
        self.status = status
        self.progress = progress
        self.message = message
        self.error_message = error_message
        
        self._update_display()
    
    def update_from_job(self, job: ProcessingJob) -> None:
        """Update status from processing job."""
        self.processing_job = job
        self.output_path = job.output_path
        
        # Map job stage to status
        if job.stage == ProcessingStage.COMPLETE:
            status = FileStatus.COMPLETED
        elif job.stage == ProcessingStage.ERROR:
            status = FileStatus.ERROR
        elif job.stage == ProcessingStage.CANCELLED:
            status = FileStatus.CANCELLED
        elif job.stage == ProcessingStage.IDLE:
            status = FileStatus.PENDING
        else:
            status = FileStatus.PROCESSING
        
        self.update_status(
            status=status,
            progress=job.progress * 100,
            message=job.message,
            error_message=job.error_message
        )


class FileListWidget(QWidget):
    """Widget for managing the list of files to process."""
    
    # Signals
    files_changed = Signal(int)  # Number of files
    selection_changed = Signal(object)  # Selected file path or None
    
    def __init__(self):
        super().__init__()
        
        self._setup_ui()
        self._connect_signals()
        
        # Update timer for progress display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # Update every 100ms
        
        logger.debug("File list widget initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Files to Process")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(header_label)
        
        # File count
        self.file_count_label = QLabel("0 files")
        self.file_count_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.file_count_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # File list
        self.list_widget = QListWidget()
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragDropMode(QListWidget.DropOnly)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        layout.addWidget(self.list_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Files")
        self.add_button.clicked.connect(self._add_files_clicked)
        button_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_selected)
        self.remove_button.setEnabled(False)
        button_layout.addWidget(self.remove_button)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def _update_display(self) -> None:
        """Update display elements."""
        count = self.list_widget.count()
        self.file_count_label.setText(f"{count} files")
        
        # Update progress display for processing items
        for i in range(count):
            item = self.list_widget.item(i)
            if isinstance(item, FileItem) and item.processing_job:
                item.update_from_job(item.processing_job)
    
    def add_files(self, file_paths: List[Path]) -> None:
        """
        Add files to the list.
        
        Args:
            file_paths: List of file paths to add
        """
        added_count = 0
        
        for file_path in file_paths:
            if not file_path.exists():
                logger.warning(f"File does not exist: {file_path}")
                continue
            
            if not is_media_file(file_path):
                logger.warning(f"Unsupported file type: {file_path}")
                continue
            
            # Check if file is already in list
            if self._is_file_in_list(file_path):
                logger.debug(f"File already in list: {file_path}")
                continue
            
            # Add file item
            item = FileItem(file_path)
            self.list_widget.addItem(item)
            added_count += 1
        
        if added_count > 0:
            logger.info(f"Added {added_count} files to list")
            self.files_changed.emit(self.list_widget.count())
    
    def _is_file_in_list(self, file_path: Path) -> bool:
        """Check if file is already in the list."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if isinstance(item, FileItem) and item.file_path == file_path:
                return True
        return False
    
    def get_all_files(self) -> List[Path]:
        """Get all files in the list."""
        files = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if isinstance(item, FileItem):
                files.append(item.file_path)
        return files
    
    def get_current_file(self) -> Optional[Path]:
        """Get currently selected file."""
        current_item = self.list_widget.currentItem()
        if isinstance(current_item, FileItem):
            return current_item.file_path
        return None
    
    def get_file_items(self) -> List[FileItem]:
        """Get all file items."""
        items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if isinstance(item, FileItem):
                items.append(item)
        return items
    
    def update_file_status(self, file_path: Path, job: ProcessingJob) -> None:
        """Update status of a specific file."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if isinstance(item, FileItem) and item.file_path == file_path:
                item.update_from_job(job)
                break
    
    def clear(self) -> None:
        """Clear all files from the list."""
        if self.list_widget.count() > 0:
            reply = QMessageBox.question(
                self,
                "Clear File List",
                "Are you sure you want to remove all files from the list?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.list_widget.clear()
                self.files_changed.emit(0)
                logger.info("File list cleared")
    
    def _add_files_clicked(self) -> None:
        """Handle add files button click."""
        from .main_window import MainWindow
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window._add_files_dialog()
    
    def _remove_selected(self) -> None:
        """Remove selected files from the list."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
        
        self.files_changed.emit(self.list_widget.count())
        logger.info(f"Removed {len(selected_items)} files from list")
    
    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        current_item = self.list_widget.currentItem()
        self.remove_button.setEnabled(current_item is not None)
        
        if isinstance(current_item, FileItem):
            self.selection_changed.emit(current_item.file_path)
        else:
            self.selection_changed.emit(None)
    
    def _show_context_menu(self, position) -> None:
        """Show context menu for file list."""
        item = self.list_widget.itemAt(position)
        if not isinstance(item, FileItem):
            return
        
        menu = QMenu(self)
        
        # Remove action
        remove_action = menu.addAction("Remove from List")
        remove_action.triggered.connect(lambda: self._remove_file_item(item))
        
        # Show in explorer action
        if item.file_path.exists():
            show_action = menu.addAction("Show in File Explorer")
            show_action.triggered.connect(lambda: self._show_in_explorer(item.file_path))
        
        # Show output action
        if item.status == FileStatus.COMPLETED and item.output_path and item.output_path.exists():
            menu.addSeparator()
            show_output_action = menu.addAction("Show Output File")
            show_output_action.triggered.connect(lambda: self._show_in_explorer(item.output_path))
            
            open_output_action = menu.addAction("Open Output File")
            open_output_action.triggered.connect(lambda: self._open_file(item.output_path))
        
        # Copy path action
        menu.addSeparator()
        copy_path_action = menu.addAction("Copy Path")
        copy_path_action.triggered.connect(lambda: self._copy_path(item.file_path))
        
        if menu.actions():
            menu.exec(self.list_widget.mapToGlobal(position))
    
    def _remove_file_item(self, item: FileItem) -> None:
        """Remove a specific file item."""
        row = self.list_widget.row(item)
        self.list_widget.takeItem(row)
        self.files_changed.emit(self.list_widget.count())
    
    def _show_in_explorer(self, file_path: Path) -> None:
        """Show file in system file explorer."""
        import subprocess
        import platform
        
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", "/select,", str(file_path)])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", "-R", str(file_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(file_path.parent)])
        except Exception as e:
            logger.error(f"Failed to show file in explorer: {e}")
    
    def _open_file(self, file_path: Path) -> None:
        """Open file with system default application."""
        import subprocess
        import platform
        
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(["start", str(file_path)], shell=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(file_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(file_path)])
        except Exception as e:
            logger.error(f"Failed to open file: {e}")
    
    def _copy_path(self, file_path: Path) -> None:
        """Copy file path to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(str(file_path))
    
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle item double click."""
        if isinstance(item, FileItem):
            if item.status == FileStatus.COMPLETED and item.output_path and item.output_path.exists():
                self._open_file(item.output_path)
            else:
                self._open_file(item.file_path)
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event."""
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(Path(url.toLocalFile()))
        
        if files:
            self.add_files(files)
            event.acceptProposedAction()