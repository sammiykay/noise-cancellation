"""Main application entry point for the noise cancellation GUI."""

import sys
import argparse
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow
from ui.modern_styles import apply_modern_style
from utils.logging_setup import setup_logging, get_logger
from utils.validators import validate_system_requirements


def setup_application() -> QApplication:
    """Set up the Qt application with proper configuration."""
    app = QApplication(sys.argv)
    app.setApplicationName("Noise Cancellation Studio")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Modern Audio Tools")
    app.setApplicationDisplayName("✨ Noise Cancellation Studio")
    
    # Apply modern dark theme
    apply_modern_style(app)
    
    # Set application icon if available
    icon_path = Path("ui/resources/app_icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Enable high DPI scaling (Note: These are deprecated in newer Qt versions but kept for compatibility)
    try:
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # These attributes might not exist in newer Qt versions
        pass
    
    return app


def check_system_requirements() -> bool:
    """Check and validate system requirements."""
    logger = get_logger("startup")
    
    logger.info("Checking system requirements...")
    results = validate_system_requirements()
    
    issues = []
    critical_issues = []
    
    for component, result in results.items():
        if not result.is_valid:
            if component == "ffmpeg":
                critical_issues.append(result.message)
                critical_issues.extend(result.suggestions)
            else:
                issues.append(result.message)
                issues.extend(result.suggestions)
    
    if critical_issues:
        logger.error("Critical system requirements not met")
        
        # Show critical error dialog
        app = QApplication.instance()
        if app:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("System Requirements Not Met")
            msg.setText("Critical components are missing or not working properly:")
            msg.setDetailedText("\n".join(critical_issues))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
        
        return False
    
    if issues:
        logger.warning("Some optional components have issues")
        
        # Show warning dialog
        app = QApplication.instance()
        if app:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Optional Components Issues")
            msg.setText("Some optional features may not work properly:")
            msg.setDetailedText("\n".join(issues))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
    
    logger.info("System requirements check completed")
    return True


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Professional desktop application for removing background noise from audio and video files"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("logs"),
        help="Directory for log files (default: logs/)"
    )
    
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("config"),
        help="Directory for configuration files (default: config/)"
    )
    
    parser.add_argument(
        "--no-system-check",
        action="store_true",
        help="Skip system requirements check (not recommended)"
    )
    
    parser.add_argument(
        "files",
        nargs="*",
        help="Audio or video files to open in the application"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main application entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Set up logging
        log_level = getattr(__import__('logging'), args.log_level)
        logger = setup_logging(
            log_dir=args.log_dir,
            log_level=log_level
        )
        
        logger.info("Starting Noise Cancellation Studio v2.0 with Modern UI")
        logger.info(f"Command line arguments: {vars(args)}")
        
        # Create application
        app = setup_application()
        
        # Check system requirements
        if not args.no_system_check:
            if not check_system_requirements():
                logger.error("System requirements check failed, exiting")
                return 1
        else:
            logger.warning("Skipping system requirements check")
        
        # Create and show main window
        logger.info("Creating modern main window with animations...")
        main_window = MainWindow(
            config_dir=args.config_dir,
            initial_files=[Path(f) for f in args.files] if args.files else None
        )
        
        # Enable modern window styling (keep window controls)
        # main_window.setAttribute(Qt.WA_TranslucentBackground, True)  # Disabled to prevent issues
        
        # Show with fade-in animation
        main_window.show()
        
        # Center window on screen
        screen = app.primaryScreen().geometry()
        window_geometry = main_window.geometry()
        main_window.move(
            (screen.width() - window_geometry.width()) // 2,
            (screen.height() - window_geometry.height()) // 2
        )
        
        # Start fade-in animation
        main_window.fade_animation.start()
        
        logger.info("Modern GUI application started successfully with animations and effects")
        
        # Run application
        return app.exec()
        
    except Exception as e:
        # Fallback error handling
        try:
            logger = get_logger("main")
            logger.critical(f"Fatal error in main: {e}", exc_info=True)
        except:
            print(f"Fatal error: {e}", file=sys.stderr)
        
        # Show error dialog if possible
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Fatal Error")
            msg.setText(f"A fatal error occurred:\n\n{str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
        except:
            pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())