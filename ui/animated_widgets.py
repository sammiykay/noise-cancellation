"""Custom animated widgets for modern UI."""

from PySide6.QtWidgets import QPushButton, QLabel, QFrame, QProgressBar, QWidget, QVBoxLayout
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal, Qt, QRect
from PySide6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QPen, QBrush


class AnimatedButton(QPushButton):
    """Button with hover and click animations."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)
        self.setup_animations()
    
    def setup_animations(self):
        """Set up button animations."""
        # Hover animation
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Click animation
        self.click_animation = QPropertyAnimation(self, b"geometry")
        self.click_animation.setDuration(100)
        self.click_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        self.original_geometry = None
    
    def enterEvent(self, event):
        """Handle mouse enter for hover effect."""
        super().enterEvent(event)
        if self.original_geometry is None:
            self.original_geometry = self.geometry()
        
        # Slight scale up on hover
        new_geometry = QRect(
            self.original_geometry.x() - 2,
            self.original_geometry.y() - 2,
            self.original_geometry.width() + 4,
            self.original_geometry.height() + 4
        )
        
        self.hover_animation.setStartValue(self.geometry())
        self.hover_animation.setEndValue(new_geometry)
        self.hover_animation.start()
    
    def leaveEvent(self, event):
        """Handle mouse leave to revert hover effect."""
        super().leaveEvent(event)
        if self.original_geometry:
            self.hover_animation.setStartValue(self.geometry())
            self.hover_animation.setEndValue(self.original_geometry)
            self.hover_animation.start()
    
    def mousePressEvent(self, event):
        """Handle mouse press for click animation."""
        super().mousePressEvent(event)
        if self.original_geometry:
            # Scale down slightly on click
            pressed_geometry = QRect(
                self.original_geometry.x() + 1,
                self.original_geometry.y() + 1,
                self.original_geometry.width() - 2,
                self.original_geometry.height() - 2
            )
            
            self.click_animation.setStartValue(self.geometry())
            self.click_animation.setEndValue(pressed_geometry)
            self.click_animation.start()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to restore size."""
        super().mouseReleaseEvent(event)
        if self.original_geometry:
            self.click_animation.setStartValue(self.geometry())
            self.click_animation.setEndValue(self.original_geometry)
            self.click_animation.start()


class PulsingLabel(QLabel):
    """Label with pulsing animation effect."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setup_pulse_animation()
    
    def setup_pulse_animation(self):
        """Set up pulsing animation."""
        self.pulse_animation = QPropertyAnimation(self, b"styleSheet")
        self.pulse_animation.setDuration(2000)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
        
        # Create pulsing effect by changing opacity
        base_style = self.styleSheet()
        self.pulse_animation.setKeyValueAt(0, base_style + "color: rgba(255, 255, 255, 1);")
        self.pulse_animation.setKeyValueAt(0.5, base_style + "color: rgba(255, 255, 255, 0.6);")
        self.pulse_animation.setKeyValueAt(1, base_style + "color: rgba(255, 255, 255, 1);")
    
    def start_pulsing(self):
        """Start the pulsing animation."""
        self.pulse_animation.start()
    
    def stop_pulsing(self):
        """Stop the pulsing animation."""
        self.pulse_animation.stop()


class GlowingProgressBar(QProgressBar):
    """Progress bar with glowing effect."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_glow_animation()
    
    def setup_glow_animation(self):
        """Set up glowing animation for progress bar."""
        self.glow_animation = QPropertyAnimation(self, b"styleSheet")
        self.glow_animation.setDuration(1500)
        self.glow_animation.setLoopCount(-1)
        
        base_style = """
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                height: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4752c4, stop:0.5 #5865f2, stop:1 #6574ff);
                border-radius: 10px;
            }
        """
        
        glow_style = """
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                height: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6574ff, stop:0.5 #7584ff, stop:1 #8594ff);
                border-radius: 10px;
            }
        """
        
        self.glow_animation.setKeyValueAt(0, base_style)
        self.glow_animation.setKeyValueAt(0.5, glow_style)
        self.glow_animation.setKeyValueAt(1, base_style)
    
    def start_glowing(self):
        """Start the glowing effect."""
        self.glow_animation.start()
    
    def stop_glowing(self):
        """Stop the glowing effect."""
        self.glow_animation.stop()


class FloatingCard(QFrame):
    """Card widget with floating shadow effect."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_float_animation()
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 20px;
            }
        """)
    
    def setup_float_animation(self):
        """Set up floating animation."""
        self.float_animation = QPropertyAnimation(self, b"geometry")
        self.float_animation.setDuration(3000)
        self.float_animation.setLoopCount(-1)
        self.float_animation.setEasingCurve(QEasingCurve.InOutSine)
    
    def start_floating(self):
        """Start the floating animation."""
        if self.geometry().isValid():
            original_rect = self.geometry()
            float_rect = QRect(
                original_rect.x(),
                original_rect.y() - 5,
                original_rect.width(),
                original_rect.height()
            )
            
            self.float_animation.setKeyValueAt(0, original_rect)
            self.float_animation.setKeyValueAt(0.5, float_rect)
            self.float_animation.setKeyValueAt(1, original_rect)
            self.float_animation.start()
    
    def stop_floating(self):
        """Stop the floating animation."""
        self.float_animation.stop()


class WaveformVisualizer(QWidget):
    """Animated waveform visualization widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 100)
        self.bars = []
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_bars)
        self.current_frame = 0
        
        # Generate initial bar heights
        import random
        self.bars = [random.randint(10, 80) for _ in range(50)]
        
        self.setStyleSheet("""
            QWidget {
                background: rgba(10, 15, 30, 0.4);
                border: 2px solid rgba(88, 101, 242, 0.2);
                border-radius: 12px;
            }
        """)
    
    def paintEvent(self, event):
        """Paint the waveform bars."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create gradient for bars
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(88, 101, 242, 200))
        gradient.setColorAt(0.5, QColor(101, 116, 255, 255))
        gradient.setColorAt(1, QColor(117, 132, 255, 150))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        
        bar_width = self.width() / len(self.bars)
        
        for i, height in enumerate(self.bars):
            x = i * bar_width
            y = self.height() - height
            rect = QRect(int(x + 2), int(y), int(bar_width - 4), int(height))
            painter.drawRoundedRect(rect, 2, 2)
    
    def update_bars(self):
        """Update bar heights for animation."""
        import random
        import math
        
        # Create wave-like animation
        self.current_frame += 0.2
        for i in range(len(self.bars)):
            wave = math.sin(self.current_frame + i * 0.3) * 30
            base_height = 20 + random.randint(0, 20)
            self.bars[i] = max(10, min(80, base_height + wave))
        
        self.update()
    
    def start_animation(self):
        """Start the waveform animation."""
        self.animation_timer.start(50)  # Update every 50ms
    
    def stop_animation(self):
        """Stop the waveform animation."""
        self.animation_timer.stop()


class StatusIndicator(QWidget):
    """Animated status indicator with different states."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.status = "idle"  # idle, processing, success, error
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        self.rotation = 0
    
    def paintEvent(self, event):
        """Paint the status indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        radius = 8
        
        if self.status == "idle":
            # Gray circle
            painter.setBrush(QBrush(QColor(160, 168, 183, 100)))
            painter.setPen(QPen(QColor(160, 168, 183), 2))
            painter.drawEllipse(center, radius, radius)
        
        elif self.status == "processing":
            # Spinning gradient circle
            painter.translate(center)
            painter.rotate(self.rotation)
            
            gradient = QLinearGradient(-radius, -radius, radius, radius)
            gradient.setColorAt(0, QColor(88, 101, 242, 255))
            gradient.setColorAt(0.5, QColor(88, 101, 242, 100))
            gradient.setColorAt(1, QColor(88, 101, 242, 50))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(-radius, -radius, radius * 2, radius * 2)
        
        elif self.status == "success":
            # Green checkmark
            painter.setBrush(QBrush(QColor(87, 242, 135, 200)))
            painter.setPen(QPen(QColor(87, 242, 135), 2))
            painter.drawEllipse(center, radius, radius)
            
            # Draw checkmark
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(center.x() - 3, center.y(), center.x() - 1, center.y() + 2)
            painter.drawLine(center.x() - 1, center.y() + 2, center.x() + 3, center.y() - 2)
        
        elif self.status == "error":
            # Red X
            painter.setBrush(QBrush(QColor(237, 66, 69, 200)))
            painter.setPen(QPen(QColor(237, 66, 69), 2))
            painter.drawEllipse(center, radius, radius)
            
            # Draw X
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(center.x() - 3, center.y() - 3, center.x() + 3, center.y() + 3)
            painter.drawLine(center.x() - 3, center.y() + 3, center.x() + 3, center.y() - 3)
    
    def set_status(self, status):
        """Set the status and update animation."""
        self.status = status
        
        if status == "processing":
            self.animation_timer.start(50)
        else:
            self.animation_timer.stop()
            self.rotation = 0
        
        self.update()
    
    def update_rotation(self):
        """Update rotation for processing animation."""
        self.rotation = (self.rotation + 10) % 360
        self.update()
    
    def start_animation(self):
        """Start the animation."""
        if self.status == "processing":
            self.animation_timer.timeout.connect(self.update_rotation)
            self.animation_timer.start(50)
    
    def stop_animation(self):
        """Stop the animation."""
        self.animation_timer.stop()


class LoadingSpinner(QWidget):
    """Modern loading spinner widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_rotation)
        self.rotation = 0
        
    def paintEvent(self, event):
        """Paint the loading spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        painter.translate(center)
        painter.rotate(self.rotation)
        
        # Draw multiple circles in a circle
        for i in range(8):
            angle = i * 45
            painter.save()
            painter.rotate(angle)
            
            # Fade effect
            alpha = int(255 * (i + 1) / 8)
            color = QColor(88, 101, 242, alpha)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            painter.drawEllipse(15, -3, 6, 6)
            painter.restore()
    
    def update_rotation(self):
        """Update rotation angle."""
        self.rotation = (self.rotation + 45) % 360
        self.update()
    
    def start_spinning(self):
        """Start the spinning animation."""
        self.animation_timer.start(200)  # Rotate every 200ms
    
    def stop_spinning(self):
        """Stop the spinning animation."""
        self.animation_timer.stop()