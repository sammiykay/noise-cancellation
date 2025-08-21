"""Modern icon provider with SVG icons and visual effects."""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtSvg import QSvgRenderer
from io import BytesIO


class ModernIconProvider:
    """Provider for modern gradient and animated icons."""
    
    @staticmethod
    def create_gradient_icon(size: QSize, colors: list, shape: str = "circle") -> QIcon:
        """Create a gradient icon with specified colors and shape."""
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(0, 0, size.width(), size.height())
        for i, color in enumerate(colors):
            gradient.setColorAt(i / (len(colors) - 1), QColor(color))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        
        if shape == "circle":
            painter.drawEllipse(0, 0, size.width(), size.height())
        elif shape == "rounded_rect":
            painter.drawRoundedRect(0, 0, size.width(), size.height(), 
                                   size.width() * 0.2, size.height() * 0.2)
        elif shape == "rect":
            painter.drawRect(0, 0, size.width(), size.height())
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_svg_icon(svg_content: str, size: QSize, color: str = None) -> QIcon:
        """Create an icon from SVG content with optional color override."""
        if color:
            svg_content = svg_content.replace("currentColor", color)
        
        svg_bytes = BytesIO(svg_content.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes.getvalue())
        
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    
    @staticmethod
    def create_play_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create modern play icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 5V19L19 12L8 5Z" fill="currentColor"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#57f287")
    
    @staticmethod
    def create_pause_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create modern pause icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 4H10V20H6V4ZM14 4H18V20H14V4Z" fill="currentColor"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#5865f2")
    
    @staticmethod
    def create_stop_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create modern stop icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="4" width="16" height="16" rx="2" fill="currentColor"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#ed4245")
    
    @staticmethod
    def create_add_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create modern add/plus icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 4V20M20 12H4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#5865f2")
    
    @staticmethod
    def create_settings_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create modern settings/gear icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12.22 2L13.75 5.08C14.27 5.35 14.76 5.68 15.21 6.07L18.5 5.5L19.5 7.5L16.93 9.89C16.98 10.26 16.98 10.64 16.93 11L19.5 13.41L18.5 15.41L15.21 14.84C14.76 15.23 14.27 15.56 13.75 15.83L12.22 18.91H9.78L8.25 15.83C7.73 15.56 7.24 15.23 6.79 14.84L3.5 15.41L2.5 13.41L5.07 11C5.02 10.64 5.02 10.26 5.07 9.89L2.5 7.5L3.5 5.5L6.79 6.07C7.24 5.68 7.73 5.35 8.25 5.08L9.78 2H12.22ZM12 8C10.34 8 9 9.34 9 11S10.34 14 12 14S15 12.66 15 11S13.66 8 12 8Z" fill="currentColor"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#a0a8b7")
    
    @staticmethod
    def create_folder_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create modern folder icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 4C4 2.89543 4.89543 2 6 2H9.58579C10.1163 2 10.6249 2.21071 11 2.58579L12.4142 4H18C19.1046 4 20 4.89543 20 6V18C20 19.1046 19.1046 20 18 20H6C4.89543 20 4 19.1046 4 18V4Z" fill="currentColor"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#fee75c")
    
    @staticmethod
    def create_file_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create modern file icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13 2L20 9V22H4V2H13ZM13 2V9H20" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#a0a8b7")
    
    @staticmethod
    def create_audio_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create modern audio/music icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 3V13.55C11.41 13.21 10.73 13 10 13C7.79 13 6 14.79 6 17S7.79 21 10 21S14 19.21 14 17V7H18V3H12Z" fill="currentColor"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#5865f2")
    
    @staticmethod
    def create_video_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create modern video icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 10.5V7C17 6.45 16.55 6 16 6H4C3.45 6 3 6.45 3 7V17C3 17.55 3.45 18 4 18H16C16.55 18 17 17.55 17 17V13.5L21 17.5V6.5L17 10.5Z" fill="currentColor"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#ed4245")
    
    @staticmethod
    def create_waveform_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create waveform visualization icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="10" width="2" height="4" rx="1" fill="currentColor"/>
            <rect x="6" y="8" width="2" height="8" rx="1" fill="currentColor"/>
            <rect x="9" y="6" width="2" height="12" rx="1" fill="currentColor"/>
            <rect x="12" y="4" width="2" height="16" rx="1" fill="currentColor"/>
            <rect x="15" y="7" width="2" height="10" rx="1" fill="currentColor"/>
            <rect x="18" y="9" width="2" height="6" rx="1" fill="currentColor"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#6574ff")
    
    @staticmethod
    def create_success_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create success checkmark icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.2"/>
            <path d="M8 12L11 15L16 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#57f287")
    
    @staticmethod
    def create_error_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create error X icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.2"/>
            <path d="M15 9L9 15M9 9L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#ed4245")
    
    @staticmethod
    def create_warning_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create warning triangle icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L22 20H2L12 2Z" fill="currentColor" opacity="0.2"/>
            <path d="M12 8V13M12 16H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#fee75c")
    
    @staticmethod
    def create_info_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create info circle icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.2"/>
            <path d="M12 8H12.01M12 12V16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#5865f2")
    
    @staticmethod
    def create_delete_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create delete trash icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 6H5H21M8 6V4C8 3.45 8.45 3 9 3H15C15.55 3 16 3.45 16 4V6M19 6V20C19 20.55 18.55 21 18 21H6C5.45 21 5 20.55 5 20V6H19ZM10 11V17M14 11V17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#ed4245")
    
    @staticmethod
    def create_clear_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create clear/remove icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/>
            <path d="M15 9L9 15M9 9L15 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#a0a8b7")
    
    @staticmethod
    def create_minimize_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create minimize icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 12H18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#a0a8b7")
    
    @staticmethod
    def create_maximize_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create maximize icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2" fill="none"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#a0a8b7")
    
    @staticmethod
    def create_close_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create close X icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#ed4245")
    
    @staticmethod
    def create_download_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create download arrow icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15V19C21 19.55 20.55 20 20 20H4C3.45 20 3 19.55 3 19V15M7 10L12 15L17 10M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#57f287")
    
    @staticmethod
    def create_upload_icon(size: QSize = QSize(24, 24)) -> QIcon:
        """Create upload arrow icon."""
        svg = """
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15V19C21 19.55 20.55 20 20 20H4C3.45 20 3 19.55 3 19V15M17 8L12 3L7 8M12 3V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
        return ModernIconProvider.create_svg_icon(svg, size, "#5865f2")


def get_icon_theme():
    """Get a dictionary of all available modern icons."""
    return {
        'play': ModernIconProvider.create_play_icon(),
        'pause': ModernIconProvider.create_pause_icon(),
        'stop': ModernIconProvider.create_stop_icon(),
        'add': ModernIconProvider.create_add_icon(),
        'settings': ModernIconProvider.create_settings_icon(),
        'folder': ModernIconProvider.create_folder_icon(),
        'file': ModernIconProvider.create_file_icon(),
        'audio': ModernIconProvider.create_audio_icon(),
        'video': ModernIconProvider.create_video_icon(),
        'waveform': ModernIconProvider.create_waveform_icon(),
        'success': ModernIconProvider.create_success_icon(),
        'error': ModernIconProvider.create_error_icon(),
        'warning': ModernIconProvider.create_warning_icon(),
        'info': ModernIconProvider.create_info_icon(),
        'delete': ModernIconProvider.create_delete_icon(),
        'clear': ModernIconProvider.create_clear_icon(),
        'minimize': ModernIconProvider.create_minimize_icon(),
        'maximize': ModernIconProvider.create_maximize_icon(),
        'close': ModernIconProvider.create_close_icon(),
        'download': ModernIconProvider.create_download_icon(),
        'upload': ModernIconProvider.create_upload_icon(),
    }