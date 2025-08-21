"""Validation utilities for application components."""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil

from utils.logging_setup import get_logger

logger = get_logger("validators")


class ValidationResult:
    """Result of a validation check."""
    
    def __init__(self, is_valid: bool, message: str, suggestions: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.message = message
        self.suggestions = suggestions or []


def validate_ffmpeg() -> ValidationResult:
    """
    Validate FFmpeg installation and accessibility.
    
    Returns:
        ValidationResult with FFmpeg status and suggestions
    """
    try:
        # Check if ffmpeg is in PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            return ValidationResult(
                False,
                "FFmpeg not found in system PATH",
                [
                    "Install FFmpeg from https://ffmpeg.org/download.html",
                    "Add FFmpeg to your system PATH",
                    "On Windows: Download from https://www.gyan.dev/ffmpeg/builds/",
                    "On macOS: Install with 'brew install ffmpeg'",
                    "On Linux: Install with your package manager (e.g., 'apt install ffmpeg')"
                ]
            )
        
        # Test FFmpeg functionality
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return ValidationResult(
                False,
                f"FFmpeg found but not working properly: {result.stderr}",
                ["Reinstall FFmpeg", "Check file permissions"]
            )
        
        # Extract version info
        version_line = result.stdout.split('\n')[0]
        logger.info(f"FFmpeg validation successful: {version_line}")
        
        return ValidationResult(
            True,
            f"FFmpeg is working properly: {version_line}"
        )
        
    except subprocess.TimeoutExpired:
        return ValidationResult(
            False,
            "FFmpeg validation timed out",
            ["Check if FFmpeg is responding", "Restart the application"]
        )
    except Exception as e:
        return ValidationResult(
            False,
            f"Error validating FFmpeg: {str(e)}",
            ["Reinstall FFmpeg", "Check system configuration"]
        )


def validate_file_permissions(path: Path) -> ValidationResult:
    """
    Validate file/directory permissions.
    
    Args:
        path: Path to validate
        
    Returns:
        ValidationResult with permission status
    """
    if not path.exists():
        return ValidationResult(
            False,
            f"Path does not exist: {path}",
            [f"Create the path: {path}"]
        )
    
    if path.is_file():
        if not path.is_file():
            return ValidationResult(False, f"Cannot read file: {path}")
        
        # Check write permission by attempting to create a test file in the same directory
        try:
            test_file = path.parent / ".test_permission"
            test_file.touch()
            test_file.unlink()
            return ValidationResult(True, f"File permissions OK: {path}")
        except PermissionError:
            return ValidationResult(
                False,
                f"No write permission in directory: {path.parent}",
                ["Check file/directory permissions", "Run as administrator if necessary"]
            )
    
    elif path.is_dir():
        if not path.is_dir():
            return ValidationResult(False, f"Cannot read directory: {path}")
        
        try:
            test_file = path / ".test_permission"
            test_file.touch()
            test_file.unlink()
            return ValidationResult(True, f"Directory permissions OK: {path}")
        except PermissionError:
            return ValidationResult(
                False,
                f"No write permission in directory: {path}",
                ["Check directory permissions", "Run as administrator if necessary"]
            )
    
    return ValidationResult(True, f"Permissions OK: {path}")


def validate_output_directory(output_dir: Path) -> ValidationResult:
    """
    Validate and prepare output directory.
    
    Args:
        output_dir: Output directory path
        
    Returns:
        ValidationResult with directory status
    """
    try:
        # Create directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write permission
        test_file = output_dir / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        
        return ValidationResult(True, f"Output directory ready: {output_dir}")
        
    except PermissionError:
        return ValidationResult(
            False,
            f"Cannot write to output directory: {output_dir}",
            [
                "Choose a different output directory",
                "Check directory permissions",
                "Run as administrator if necessary"
            ]
        )
    except Exception as e:
        return ValidationResult(
            False,
            f"Error preparing output directory: {str(e)}",
            ["Check disk space", "Choose a different location"]
        )


def validate_disk_space(path: Path, required_mb: float = 100) -> ValidationResult:
    """
    Validate available disk space.
    
    Args:
        path: Path to check disk space for
        required_mb: Required space in megabytes
        
    Returns:
        ValidationResult with disk space status
    """
    try:
        stat = shutil.disk_usage(path)
        available_mb = stat.free / (1024 * 1024)
        
        if available_mb < required_mb:
            return ValidationResult(
                False,
                f"Insufficient disk space. Available: {available_mb:.1f}MB, Required: {required_mb:.1f}MB",
                [
                    "Free up disk space",
                    "Choose a different output location",
                    "Move files to external storage"
                ]
            )
        
        return ValidationResult(
            True,
            f"Sufficient disk space available: {available_mb:.1f}MB"
        )
        
    except Exception as e:
        return ValidationResult(
            False,
            f"Error checking disk space: {str(e)}",
            ["Check if path is accessible"]
        )


def validate_rnnoise_models(models_dir: Path) -> ValidationResult:
    """
    Validate RNNoise model files.
    
    Args:
        models_dir: Directory containing RNNoise models
        
    Returns:
        ValidationResult with model validation status
    """
    expected_models = ["bd.rnnn", "cb.rnnn", "mp.rnnn", "sh.rnnn"]
    missing_models = []
    
    if not models_dir.exists():
        return ValidationResult(
            False,
            f"Models directory not found: {models_dir}",
            [
                "Run 'make download-models' to download RNNoise models",
                f"Create directory: {models_dir}"
            ]
        )
    
    for model in expected_models:
        model_path = models_dir / model
        if not model_path.exists():
            missing_models.append(model)
    
    if missing_models:
        return ValidationResult(
            False,
            f"Missing RNNoise models: {', '.join(missing_models)}",
            [
                "Run 'make download-models' to download missing models",
                "Download models manually from https://github.com/xiph/rnnoise-models"
            ]
        )
    
    return ValidationResult(True, "All RNNoise models are available")


def validate_system_requirements() -> Dict[str, ValidationResult]:
    """
    Validate all system requirements.
    
    Returns:
        Dictionary of validation results by component
    """
    results = {}
    
    # Validate FFmpeg
    results["ffmpeg"] = validate_ffmpeg()
    
    # Validate models
    models_dir = Path("models")
    results["rnnoise_models"] = validate_rnnoise_models(models_dir)
    
    # Validate logs directory
    logs_dir = Path("logs")
    results["logs_dir"] = validate_output_directory(logs_dir)
    
    # Check disk space
    results["disk_space"] = validate_disk_space(Path("."), 500)  # 500MB
    
    return results


def get_system_status() -> Tuple[bool, List[str]]:
    """
    Get overall system status and issues.
    
    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    results = validate_system_requirements()
    issues = []
    
    for component, result in results.items():
        if not result.is_valid:
            issues.append(f"{component}: {result.message}")
    
    return len(issues) == 0, issues