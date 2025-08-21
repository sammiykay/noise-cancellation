"""Path utilities for file handling and naming conventions."""

import re
from pathlib import Path
from typing import Optional, Dict, Any


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to be safe for filesystem use.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    # Ensure it's not empty
    if not filename:
        filename = "untitled"
    return filename


def generate_output_path(
    input_path: Path,
    pattern: str = "{parent}/clean/{name}_clean{ext}",
    suffix: str = "_clean",
    output_format: Optional[str] = None,
    output_directory: Optional[Path] = None
) -> Path:
    """
    Generate output file path based on input path and pattern.
    
    Args:
        input_path: Original input file path
        pattern: Path pattern with placeholders
        suffix: Default suffix for filename
        output_format: Target format extension (e.g., '.wav', '.mp3')
        output_directory: Custom output directory (overrides pattern parent)
        
    Returns:
        Generated output path
        
    Pattern placeholders:
        {parent} - Parent directory of input file
        {name} - Filename without extension
        {ext} - Original file extension
        {stem} - Full filename with extension
    """
    parent = input_path.parent
    name = input_path.stem
    ext = output_format if output_format else input_path.suffix
    stem = input_path.name
    
    # Ensure extension starts with dot
    if ext and not ext.startswith('.'):
        ext = f'.{ext}'
    
    # If custom output directory is specified, use simple naming
    if output_directory:
        output_directory = Path(output_directory)
        output_filename = f"{sanitize_filename(name)}_clean{ext}"
        output_path = output_directory / output_filename
    else:
        # Create substitution dictionary
        subs = {
            'parent': str(parent),
            'name': sanitize_filename(name),
            'ext': ext,
            'stem': sanitize_filename(stem)
        }
        
        # Apply pattern
        output_str = pattern.format(**subs)
        output_path = Path(output_str)
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    return output_path


def get_unique_path(path: Path) -> Path:
    """
    Get a unique file path by adding numbers if file exists.
    
    Args:
        path: Desired file path
        
    Returns:
        Unique file path (may be the same if no conflict)
    """
    if not path.exists():
        return path
    
    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def is_audio_file(path: Path) -> bool:
    """Check if file is a supported audio format."""
    audio_extensions = {
        '.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.aiff'
    }
    return path.suffix.lower() in audio_extensions


def is_video_file(path: Path) -> bool:
    """Check if file is a supported video format."""
    video_extensions = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'
    }
    return path.suffix.lower() in video_extensions


def is_media_file(path: Path) -> bool:
    """Check if file is a supported media format (audio or video)."""
    return is_audio_file(path) or is_video_file(path)


def get_temp_path(original_path: Path, suffix: str = "_temp") -> Path:
    """
    Generate a temporary file path based on original path.
    
    Args:
        original_path: Original file path
        suffix: Suffix to add to temporary file
        
    Returns:
        Temporary file path
    """
    parent = original_path.parent
    stem = original_path.stem
    ext = original_path.suffix
    
    return parent / f"{stem}{suffix}{ext}"


class PathTemplate:
    """Class for managing path templates with validation."""
    
    def __init__(self, template: str):
        """
        Initialize path template.
        
        Args:
            template: Path template string with placeholders
        """
        self.template = template
        self.validate()
    
    def validate(self) -> None:
        """Validate template format."""
        valid_placeholders = {'parent', 'name', 'ext', 'stem'}
        
        # Extract placeholders from template
        placeholders = re.findall(r'\{(\w+)\}', self.template)
        
        invalid = set(placeholders) - valid_placeholders
        if invalid:
            raise ValueError(f"Invalid placeholders: {invalid}")
    
    def apply(self, input_path: Path, **kwargs: Any) -> Path:
        """Apply template to generate output path."""
        return generate_output_path(input_path, self.template, **kwargs)