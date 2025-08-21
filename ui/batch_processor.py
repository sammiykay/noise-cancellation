"""Batch processing widget with threading support."""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar,
    QLabel, QGroupBox, QSpinBox, QCheckBox, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject, QMutex, QMutexLocker
from PySide6.QtGui import QFont, QIcon

from utils.logging_setup import get_logger
from core.pipeline import ProcessingPipeline, ProcessingJob, Engine, ProcessingStage

logger = get_logger("batch_processor")


class BatchWorker(QObject):
    """Worker object for batch processing in separate thread."""
    
    # Signals
    job_started = Signal(object)  # ProcessingJob
    job_progress = Signal(object)  # ProcessingJob
    job_completed = Signal(object)  # ProcessingJob
    batch_finished = Signal()
    
    def __init__(self):
        super().__init__()
        self.pipeline = ProcessingPipeline()
        self.jobs: List[ProcessingJob] = []
        self.current_job_index = 0
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.mutex = QMutex()
    
    def process_all_jobs(self) -> None:
        """Process all jobs - this runs in the worker thread."""
        self.is_running = True
        self.should_stop = False
        self.current_job_index = 0
        
        while self.current_job_index < len(self.jobs) and not self.should_stop:
            if self.is_paused:
                # Sleep briefly and check again
                import time
                time.sleep(0.1)
                continue
            
            current_job = self.jobs[self.current_job_index]
            
            # Emit job started signal
            self.job_started.emit(current_job)
            
            def progress_callback(job: ProcessingJob) -> None:
                self.job_progress.emit(job)
            
            try:
                # Process the job (this is the heavy work)
                success = self.pipeline.process_job(current_job, progress_callback)
                
            except Exception as e:
                current_job.error_message = str(e)
                current_job.stage = ProcessingStage.ERROR
            
            # Emit job completed signal
            self.job_completed.emit(current_job)
            
            # Move to next job
            self.current_job_index += 1
        
        # All jobs finished or stopped
        self.is_running = False
        self.batch_finished.emit()
        
    def set_jobs(self, jobs: List[ProcessingJob]) -> None:
        """Set jobs to process."""
        locker = QMutexLocker(self.mutex)
        self.jobs = jobs
        self.current_job_index = 0
    
    def start_processing(self) -> None:
        """Start batch processing."""
        self.is_running = True
        self.is_paused = False
        self.should_stop = False
        
        # Start processing in worker thread
        QTimer.singleShot(0, self.process_all_jobs)
    
    def pause_processing(self) -> None:
        """Pause batch processing."""
        self.is_paused = True
    
    def resume_processing(self) -> None:
        """Resume batch processing."""
        self.is_paused = False
    
    def stop_processing(self) -> None:
        """Stop batch processing."""
        self.should_stop = True
        self.is_running = False
        self.is_paused = False
        
        # Cancel current job if running
        if hasattr(self.pipeline, 'cancel_current_job'):
            self.pipeline.cancel_current_job()


class BatchProcessorWidget(QWidget):
    """Widget for batch processing control and monitoring."""
    
    # Signals
    processing_started = Signal()
    processing_finished = Signal()
    progress_updated = Signal(int, int, str)  # current, total, message
    start_worker_signal = Signal()  # Signal to start worker processing
    
    def __init__(self):
        super().__init__()
        
        self.jobs: List[ProcessingJob] = []
        self.completed_jobs = 0
        self.failed_jobs = 0
        self.processing_start_time: Optional[float] = None
        
        # Initialize with default settings
        self.current_settings = {
            'engine': 'spectral_gate',
            'engine_config': {'reduction_db': 20.0},
            'output_format': 'wav',
            'preserve_video': True,
            'normalize_loudness': False,
            'target_lufs': -23.0
        }
        
        # Worker thread
        self.worker_thread = QThread()
        self.worker = BatchWorker()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        
        # Connect worker to trigger processing in thread
        self.start_worker_signal.connect(self.worker.process_all_jobs)
        
        self._setup_ui()
        self._connect_signals()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(500)  # Update every 500ms
        
        logger.debug("Batch processor widget initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("⚙️ Batch Control")
        header_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #a0a8b7;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Progress section - compact
        progress_group = QGroupBox("📊 Progress")
        progress_group.setMaximumHeight(80)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(4, 4, 4, 4)
        progress_layout.setSpacing(2)
        
        # Overall progress - compact
        self.overall_progress = QProgressBar()
        self.overall_progress.setVisible(False)
        self.overall_progress.setMaximumHeight(14)
        progress_layout.addWidget(self.overall_progress)
        
        # Current job progress - compact
        self.job_progress = QProgressBar()
        self.job_progress.setVisible(False)
        self.job_progress.setMaximumHeight(14)
        progress_layout.addWidget(self.job_progress)
        
        # Status labels - compact
        self.status_label = QLabel("🔄 Ready")
        self.status_label.setStyleSheet("color: #57f287; font-size: 10px;")
        progress_layout.addWidget(self.status_label)
        
        self.eta_label = QLabel("")
        self.eta_label.setStyleSheet("color: #a0a8b7; font-size: 9px;")
        progress_layout.addWidget(self.eta_label)
        
        layout.addWidget(progress_group)
        
        # Settings section - compact and visible
        settings_group = QGroupBox("⚙️ Settings")
        settings_group.setMaximumHeight(120)
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(4, 4, 4, 4)
        settings_layout.setSpacing(2)
        
        # Max parallel jobs - compact
        parallel_layout = QHBoxLayout()
        parallel_layout.setSpacing(4)
        parallel_label = QLabel("Parallel:")
        parallel_label.setStyleSheet("font-size: 10px;")
        parallel_layout.addWidget(parallel_label)
        self.parallel_jobs_spin = QSpinBox()
        self.parallel_jobs_spin.setRange(1, 4)
        self.parallel_jobs_spin.setValue(1)
        self.parallel_jobs_spin.setMaximumHeight(22)
        self.parallel_jobs_spin.setMaximumWidth(55)
        self.parallel_jobs_spin.setToolTip("Number of files to process simultaneously")
        self.parallel_jobs_spin.setStyleSheet("""
            QSpinBox {
                background: rgba(30, 35, 50, 0.9);
                border: 1px solid rgba(88, 101, 242, 0.4);
                border-radius: 4px;
                padding: 2px 4px;
                padding-right: 18px;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        parallel_layout.addWidget(self.parallel_jobs_spin)
        parallel_layout.addStretch()
        settings_layout.addLayout(parallel_layout)
        
        # Continue on error - compact
        self.continue_on_error = QCheckBox("Continue on error")
        self.continue_on_error.setChecked(True)
        self.continue_on_error.setStyleSheet("font-size: 10px;")
        settings_layout.addWidget(self.continue_on_error)
        
        # Auto-clear completed - compact
        self.auto_clear_completed = QCheckBox("Auto-clear completed")
        self.auto_clear_completed.setStyleSheet("font-size: 10px;")
        settings_layout.addWidget(self.auto_clear_completed)
        
        layout.addWidget(settings_group)
        
        # Control buttons - compact
        button_layout = QHBoxLayout()
        button_layout.setSpacing(2)
        
        self.start_button = QPushButton("▶ Start")
        self.start_button.setFixedHeight(24)
        self.start_button.setStyleSheet("""
            QPushButton { 
                background-color: #57f287; 
                color: black; 
                font-weight: bold; 
                font-size: 10px;
                border-radius: 4px;
                padding: 2px 6px;
            }
        """)
        self.start_button.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("⏸ Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.setFixedHeight(24)
        self.pause_button.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        self.pause_button.clicked.connect(self.pause_processing)
        button_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.setFixedHeight(24)
        self.stop_button.setStyleSheet("""
            QPushButton { 
                background-color: #ed4245; 
                color: white; 
                font-weight: bold; 
                font-size: 10px;
                border-radius: 4px;
                padding: 2px 6px;
            }
        """)
        self.stop_button.clicked.connect(self.stop_processing)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Statistics section - expanded for better visibility
        stats_group = QGroupBox("📈 Processing Statistics")
        stats_group.setMinimumHeight(80)
        stats_group.setMaximumHeight(120)
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setContentsMargins(6, 6, 6, 6)
        stats_layout.setSpacing(4)
        
        self.stats_label = QLabel("📋 Ready - No processing activity")
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #e4e7eb;
                font-size: 11px;
                padding: 4px;
                background: rgba(88, 101, 242, 0.05);
                border-radius: 4px;
                margin: 2px 0;
            }
        """)
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        # Add detailed stats labels
        self.time_stats_label = QLabel("")
        self.time_stats_label.setStyleSheet("""
            QLabel {
                color: #a0a8b7;
                font-size: 10px;
                padding: 2px;
            }
        """)
        stats_layout.addWidget(self.time_stats_label)
        
        self.file_stats_label = QLabel("")
        self.file_stats_label.setStyleSheet("""
            QLabel {
                color: #a0a8b7;
                font-size: 10px;
                padding: 2px;
            }
        """)
        stats_layout.addWidget(self.file_stats_label)
        
        layout.addWidget(stats_group)
        
        # Remove stretch to make content visible
        # layout.addStretch()
    
    def _connect_signals(self) -> None:
        """Connect signals from worker."""
        self.worker.job_started.connect(self._on_job_started)
        self.worker.job_progress.connect(self._on_job_progress)
        self.worker.job_completed.connect(self._on_job_completed)
        self.worker.batch_finished.connect(self._on_batch_finished)
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update batch processing settings."""
        # Store settings for creating jobs
        self.current_settings = settings
        logger.debug("Batch processor settings updated")
    
    def set_files(self, file_paths: List[Path]) -> None:
        """Set files to be processed."""
        self.jobs.clear()
        
        # Create jobs from file paths
        from utils.paths import generate_output_path
        
        for file_path in file_paths:
            # Generate output path with custom directory if specified
            output_dir = self.current_settings.get('output_directory')
            output_path = generate_output_path(
                file_path,
                suffix="_clean",
                output_format=f".{self.current_settings.get('output_format', 'wav')}",
                output_directory=Path(output_dir) if output_dir else None
            )
            
            job = ProcessingJob(
                input_path=file_path,
                output_path=output_path,
                engine=Engine(self.current_settings.get('engine', 'spectral_gate')),
                engine_config=self.current_settings.get('engine_config', {}),
                output_format=self.current_settings.get('output_format', 'wav'),
                sample_rate=self.current_settings.get('output_sample_rate'),
                preserve_video=self.current_settings.get('preserve_video', True),
                normalize_loudness=self.current_settings.get('normalize_loudness', False),
                target_lufs=self.current_settings.get('target_lufs', -23.0)
            )
            self.jobs.append(job)
        
        logger.info(f"Set {len(self.jobs)} jobs for batch processing")
    
    def start_processing(self) -> None:
        """Start batch processing."""
        # Get files from the main window's file list
        main_window = self.window()
        if hasattr(main_window, 'file_list'):
            file_paths = main_window.file_list.get_all_files()
            if file_paths:
                # Get current settings
                if hasattr(main_window, 'settings_panel'):
                    self.current_settings = main_window.settings_panel.get_current_settings()
                
                # Create jobs from files
                self.set_files(file_paths)
        
        if not self.jobs:
            logger.warning("No jobs to process - please add files first")
            self.status_label.setText("No files to process - add files using File → Add Files or drag & drop")
            return
        
        # Reset counters
        self.completed_jobs = 0
        self.failed_jobs = 0
        self.processing_start_time = time.time()
        
        # Update UI
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        
        self.overall_progress.setVisible(True)
        self.job_progress.setVisible(True)
        self.overall_progress.setMaximum(len(self.jobs))
        self.overall_progress.setValue(0)
        
        # Set jobs in worker and start processing in thread
        self.worker.set_jobs(self.jobs)
        
        # Emit signal to start processing in worker thread
        self.start_worker_signal.emit()
        
        self.processing_started.emit()
        logger.info(f"Started batch processing {len(self.jobs)} jobs")
    
    def pause_processing(self) -> None:
        """Pause batch processing."""
        self.worker.pause_processing()
        
        self.start_button.setEnabled(True)
        self.start_button.setText("Resume")
        self.pause_button.setEnabled(False)
        
        self.status_label.setText("Processing paused")
        logger.info("Batch processing paused")
    
    def resume_processing(self) -> None:
        """Resume batch processing."""
        self.worker.resume_processing()
        
        self.start_button.setEnabled(False)
        self.start_button.setText("Start Processing")
        self.pause_button.setEnabled(True)
        
        logger.info("Batch processing resumed")
    
    def stop_processing(self) -> None:
        """Stop batch processing."""
        self.worker.stop_processing()
        
        self.start_button.setEnabled(True)
        self.start_button.setText("Start Processing")
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        self.overall_progress.setVisible(False)
        self.job_progress.setVisible(False)
        self.status_label.setText("Processing stopped")
        
        self.processing_finished.emit()
        logger.info("Batch processing stopped")
    
    def is_processing(self) -> bool:
        """Check if batch processing is currently running."""
        return self.worker.is_running
    
    def _on_job_started(self, job: ProcessingJob) -> None:
        """Handle job started signal."""
        self.status_label.setText(f"Processing: {job.input_path.name}")
        self.job_progress.setValue(0)
        
        # Update file list status
        main_window = self.window()
        if hasattr(main_window, 'file_list'):
            main_window.file_list.update_file_status(job.input_path, job)
        
        logger.debug(f"Job started: {job.input_path}")
    
    def _on_job_progress(self, job: ProcessingJob) -> None:
        """Handle job progress signal."""
        self.job_progress.setValue(int(job.progress * 100))
        
        # Update file list status
        main_window = self.window()
        if hasattr(main_window, 'file_list'):
            main_window.file_list.update_file_status(job.input_path, job)
        
        # Emit progress signal
        current = self.completed_jobs
        total = len(self.jobs)
        message = f"{job.input_path.name}: {job.message}"
        self.progress_updated.emit(current, total, message)
    
    def _on_job_completed(self, job: ProcessingJob) -> None:
        """Handle job completed signal."""
        if job.is_complete and job.stage.name == 'COMPLETE':
            self.completed_jobs += 1
        else:
            self.failed_jobs += 1
        
        # Update overall progress
        self.overall_progress.setValue(self.completed_jobs + self.failed_jobs)
        
        # Update file list status
        main_window = self.window()
        if hasattr(main_window, 'file_list'):
            main_window.file_list.update_file_status(job.input_path, job)
        
        logger.info(f"Job completed: {job.input_path} -> {job.stage.name}")
    
    def _on_batch_finished(self) -> None:
        """Handle batch processing finished."""
        self.start_button.setEnabled(True)
        self.start_button.setText("Start Processing")
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        self.overall_progress.setVisible(False)
        self.job_progress.setVisible(False)
        
        # Final status with detailed stats
        processing_time = time.time() - self.processing_start_time if self.processing_start_time else 0
        total_files = self.completed_jobs + self.failed_jobs
        success_rate = (self.completed_jobs / total_files) * 100 if total_files > 0 else 0
        avg_time = processing_time / total_files if total_files > 0 else 0
        
        self.stats_label.setText(
            f"🎉 Batch Complete! {total_files} files processed\n"
            f"✅ Success: {self.completed_jobs} | ❌ Failed: {self.failed_jobs} | 📈 Rate: {success_rate:.1f}%"
        )
        
        time_str = f"{int(processing_time // 60)}m {int(processing_time % 60)}s" if processing_time > 60 else f"{int(processing_time)}s"
        self.time_stats_label.setText(f"🕰️ Total time: {time_str}")
        self.file_stats_label.setText(f"📈 Average per file: {avg_time:.1f}s")
        
        self.processing_finished.emit()
        
        # Auto-clear if enabled
        if self.auto_clear_completed.isChecked():
            self._auto_clear_completed()
        
        logger.info(f"Batch processing finished: {self.completed_jobs} successful, {self.failed_jobs} failed")
    
    def _update_display(self) -> None:
        """Update display with current statistics."""
        if not self.processing_start_time:
            self.stats_label.setText("📋 Ready - Add files to start batch processing")
            self.time_stats_label.setText("")
            self.file_stats_label.setText("")
            return
        
        elapsed = time.time() - self.processing_start_time
        processed = self.completed_jobs + self.failed_jobs
        total = len(self.jobs)
        
        # Update main stats
        if total > 0:
            progress_percent = (processed / total) * 100
            success_rate = (self.completed_jobs / processed) * 100 if processed > 0 else 0
            
            self.stats_label.setText(
                f"⚡ Processing: {processed}/{total} files ({progress_percent:.1f}%)\n"
                f"✅ Success: {self.completed_jobs} | ❌ Failed: {self.failed_jobs} | 📈 Rate: {success_rate:.1f}%"
            )
        
        # Update timing stats
        if processed > 0:
            avg_time = elapsed / processed
            remaining = total - processed
            eta = remaining * avg_time
            
            eta_str = f"{int(eta // 60)}m {int(eta % 60)}s" if eta > 60 else f"{int(eta)}s"
            elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed > 60 else f"{int(elapsed)}s"
            
            self.time_stats_label.setText(f"🕰️ Elapsed: {elapsed_str} | ETA: {eta_str}")
            self.file_stats_label.setText(f"📈 Avg per file: {avg_time:.1f}s | Remaining: {remaining} files")
        else:
            elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed > 60 else f"{int(elapsed)}s"
            self.time_stats_label.setText(f"🕰️ Elapsed: {elapsed_str} | Initializing...")
            self.file_stats_label.setText("📈 Preparing files for processing...")
        
        # Statistics
        stats_parts = []
        if processed > 0:
            stats_parts.append(f"Processed: {processed}/{total}")
        if self.completed_jobs > 0:
            stats_parts.append(f"Successful: {self.completed_jobs}")
        if self.failed_jobs > 0:
            stats_parts.append(f"Failed: {self.failed_jobs}")
        if elapsed > 0:
            stats_parts.append(f"Time: {int(elapsed // 60)}m {int(elapsed % 60)}s")
        
        self.stats_label.setText(" | ".join(stats_parts) if stats_parts else "Processing...")
    
    def _auto_clear_completed(self) -> None:
        """Auto-clear completed files from the list."""
        main_window = self.window()
        if hasattr(main_window, 'file_list'):
            # Remove completed items
            for job in self.jobs:
                if job.is_complete and job.stage.name == 'COMPLETE':
                    # Find and remove from file list
                    for i in range(main_window.file_list.list_widget.count()):
                        item = main_window.file_list.list_widget.item(i)
                        if hasattr(item, 'file_path') and item.file_path == job.input_path:
                            main_window.file_list.list_widget.takeItem(i)
                            break
            
            main_window.file_list.files_changed.emit(main_window.file_list.list_widget.count())
            logger.info("Auto-cleared completed files from list")
    
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        if self.is_processing():
            self.stop_processing()
        
        # Clean up worker thread
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(3000)  # Wait up to 3 seconds
        
        event.accept()