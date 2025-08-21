"""Gradient background widget with particle effects and animations."""

import math
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt
from PySide6.QtGui import QPainter, QLinearGradient, QRadialGradient, QColor, QBrush, QPainterPath


class Particle:
    """A single particle for background animation."""
    
    def __init__(self, x, y, vx, vy, size, color, lifetime=5000):
        self.x = x
        self.y = y
        self.vx = vx  # velocity x
        self.vy = vy  # velocity y
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.age = 0
        self.opacity = 1.0
    
    def update(self, dt=16):
        """Update particle position and properties."""
        self.x += self.vx * dt / 1000.0
        self.y += self.vy * dt / 1000.0
        self.age += dt
        
        # Fade out as particle ages
        if self.age > self.lifetime * 0.7:
            fade_progress = (self.age - self.lifetime * 0.7) / (self.lifetime * 0.3)
            self.opacity = max(0, 1.0 - fade_progress)
        
        return self.age < self.lifetime


class GradientBackgroundWidget(QWidget):
    """Widget with animated gradient background and floating particles."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.gradient_offset = 0
        self.wave_offset = 0
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(16)  # ~60 FPS
        
        # Particle spawn timer
        self.particle_timer = QTimer()
        self.particle_timer.timeout.connect(self.spawn_particles)
        self.particle_timer.start(2000)  # Spawn particles every 2 seconds
        
        # Spawn initial particles
        self.spawn_initial_particles()
    
    def spawn_initial_particles(self):
        """Spawn initial set of particles."""
        for _ in range(20):
            self.spawn_particle()
    
    def spawn_particle(self):
        """Spawn a single particle."""
        x = random.uniform(-50, self.width() + 50)
        y = random.uniform(-50, self.height() + 50)
        vx = random.uniform(-20, 20)
        vy = random.uniform(-30, -10)  # Generally move upward
        size = random.uniform(2, 8)
        
        # Random color from purple/blue palette
        colors = [
            QColor(88, 101, 242, 80),
            QColor(101, 116, 255, 60),
            QColor(117, 132, 255, 40),
            QColor(255, 255, 255, 30)
        ]
        color = random.choice(colors)
        
        lifetime = random.uniform(8000, 15000)
        particle = Particle(x, y, vx, vy, size, color, lifetime)
        self.particles.append(particle)
    
    def spawn_particles(self):
        """Spawn new particles periodically."""
        for _ in range(2):
            self.spawn_particle()
    
    def update_animation(self):
        """Update animation state."""
        # Update particles
        self.particles = [p for p in self.particles if p.update()]
        
        # Update gradient animation
        self.gradient_offset = (self.gradient_offset + 0.5) % 360
        
        # Update wave animation
        self.wave_offset = (self.wave_offset + 1) % 1000
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the gradient background and particles."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw animated gradient background
        self.draw_gradient_background(painter)
        
        # Draw floating particles
        self.draw_particles(painter)
        
        # Draw subtle wave overlay
        self.draw_wave_overlay(painter)
    
    def draw_gradient_background(self, painter):
        """Draw the main gradient background."""
        # Create animated gradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        
        # Calculate animated colors based on offset
        base_hue = (self.gradient_offset * 0.5) % 360
        
        # Create smooth color transitions
        color1 = QColor.fromHsv(int(base_hue % 360), 80, 40)  # Dark base
        color2 = QColor.fromHsv(int((base_hue + 30) % 360), 90, 35)  # Mid tone
        color3 = QColor.fromHsv(int((base_hue + 60) % 360), 70, 45)  # Accent
        
        gradient.setColorAt(0, color1)
        gradient.setColorAt(0.5, color2)
        gradient.setColorAt(1, color3)
        
        painter.fillRect(self.rect(), QBrush(gradient))
        
        # Add radial gradient overlay for depth
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = max(self.width(), self.height()) * 0.8
        
        radial_gradient = QRadialGradient(center_x, center_y, radius)
        radial_gradient.setColorAt(0, QColor(255, 255, 255, 15))
        radial_gradient.setColorAt(0.7, QColor(255, 255, 255, 5))
        radial_gradient.setColorAt(1, QColor(0, 0, 0, 20))
        
        painter.fillRect(self.rect(), QBrush(radial_gradient))
    
    def draw_particles(self, painter):
        """Draw floating particles."""
        for particle in self.particles:
            # Set particle opacity
            color = QColor(particle.color)
            color.setAlphaF(particle.opacity)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            # Draw particle as a circle
            painter.drawEllipse(
                int(particle.x - particle.size / 2),
                int(particle.y - particle.size / 2),
                int(particle.size),
                int(particle.size)
            )
    
    def draw_wave_overlay(self, painter):
        """Draw subtle wave overlay effect."""
        painter.setPen(Qt.NoPen)
        
        # Create wave path
        wave_path = QPainterPath()
        wave_height = 30
        wave_length = self.width() / 3
        
        # Start the wave
        wave_path.moveTo(0, self.height() / 2 + wave_height)
        
        # Create smooth wave using sine function
        for x in range(0, self.width() + 10, 10):
            wave_x = x
            wave_y = self.height() / 2 + wave_height * math.sin(
                (x + self.wave_offset) * 2 * math.pi / wave_length
            )
            wave_path.lineTo(wave_x, wave_y)
        
        # Close the path at bottom
        wave_path.lineTo(self.width(), self.height())
        wave_path.lineTo(0, self.height())
        wave_path.closeSubpath()
        
        # Fill with subtle gradient
        wave_gradient = QLinearGradient(0, self.height() / 2, 0, self.height())
        wave_gradient.setColorAt(0, QColor(88, 101, 242, 10))
        wave_gradient.setColorAt(1, QColor(88, 101, 242, 30))
        
        painter.fillPath(wave_path, QBrush(wave_gradient))
        
        # Add another wave with different properties
        wave_path2 = QPainterPath()
        wave_path2.moveTo(0, self.height() / 3)
        
        for x in range(0, self.width() + 10, 10):
            wave_x = x
            wave_y = self.height() / 3 + (wave_height * 0.5) * math.sin(
                (x - self.wave_offset * 1.5) * 2 * math.pi / (wave_length * 1.5)
            )
            wave_path2.lineTo(wave_x, wave_y)
        
        wave_path2.lineTo(self.width(), 0)
        wave_path2.lineTo(0, 0)
        wave_path2.closeSubpath()
        
        wave_gradient2 = QLinearGradient(0, 0, 0, self.height() / 3)
        wave_gradient2.setColorAt(0, QColor(117, 132, 255, 15))
        wave_gradient2.setColorAt(1, QColor(117, 132, 255, 5))
        
        painter.fillPath(wave_path2, QBrush(wave_gradient2))
    
    def resizeEvent(self, event):
        """Handle widget resize."""
        super().resizeEvent(event)
        # Remove particles that are now outside the widget
        self.particles = [
            p for p in self.particles 
            if -100 < p.x < self.width() + 100 and -100 < p.y < self.height() + 100
        ]
    
    def start_animation(self):
        """Start the background animation."""
        self.animation_timer.start(16)
        self.particle_timer.start(2000)
    
    def stop_animation(self):
        """Stop the background animation."""
        self.animation_timer.stop()
        self.particle_timer.stop()


class FloatingOrb(QWidget):
    """A single floating orb widget that can be placed anywhere."""
    
    def __init__(self, size=50, color=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.size = size
        self.color = color or QColor(88, 101, 242, 100)
        self.glow_intensity = 0.5
        
        # Floating animation
        self.float_animation = QPropertyAnimation(self, b"pos")
        self.float_animation.setDuration(4000)
        self.float_animation.setLoopCount(-1)
        self.float_animation.setEasingCurve(QEasingCurve.InOutSine)
        
        # Glow animation
        self.glow_timer = QTimer()
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(50)
        self.glow_direction = 1
    
    def paintEvent(self, event):
        """Paint the floating orb."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        radius = self.size // 2 - 5
        
        # Create radial gradient for glow effect
        gradient = QRadialGradient(center, radius)
        
        # Animate glow intensity
        inner_alpha = int(150 * self.glow_intensity)
        outer_alpha = int(30 * self.glow_intensity)
        
        inner_color = QColor(self.color)
        inner_color.setAlpha(inner_alpha)
        
        outer_color = QColor(self.color)
        outer_color.setAlpha(outer_alpha)
        
        gradient.setColorAt(0, inner_color)
        gradient.setColorAt(0.7, outer_color)
        gradient.setColorAt(1, QColor(self.color.red(), self.color.green(), self.color.blue(), 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius, radius)
    
    def update_glow(self):
        """Update glow intensity."""
        self.glow_intensity += 0.02 * self.glow_direction
        
        if self.glow_intensity >= 1.0:
            self.glow_intensity = 1.0
            self.glow_direction = -1
        elif self.glow_intensity <= 0.3:
            self.glow_intensity = 0.3
            self.glow_direction = 1
        
        self.update()
    
    def start_floating(self):
        """Start the floating animation."""
        if self.parent():
            parent_rect = self.parent().rect()
            start_pos = self.pos()
            
            # Calculate random floating destination
            end_x = max(0, min(parent_rect.width() - self.width(),
                              start_pos.x() + random.randint(-50, 50)))
            end_y = max(0, min(parent_rect.height() - self.height(),
                              start_pos.y() + random.randint(-30, 30)))
            
            self.float_animation.setStartValue(start_pos)
            self.float_animation.setEndValue(self.parent().mapToGlobal(self.pos().__class__(end_x, end_y)))
            self.float_animation.start()
    
    def stop_floating(self):
        """Stop the floating animation."""
        self.float_animation.stop()
        self.glow_timer.stop()


class GlassmorphismOverlay(QWidget):
    """Glassmorphism overlay effect widget."""
    
    def __init__(self, parent=None, blur_radius=20, opacity=0.1):
        super().__init__(parent)
        self.blur_radius = blur_radius
        self.opacity = opacity
        self.setAutoFillBackground(False)
        
        # Style with glassmorphism effect
        self.setStyleSheet(f"""
            QWidget {{
                background: rgba(255, 255, 255, {opacity * 255});
                border: 1px solid rgba(255, 255, 255, {opacity * 100});
                border-radius: 16px;
                backdrop-filter: blur({blur_radius}px);
            }}
        """)
    
    def paintEvent(self, event):
        """Paint the glassmorphism effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create subtle gradient overlay
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, int(50 * self.opacity)))
        gradient.setColorAt(0.5, QColor(255, 255, 255, int(20 * self.opacity)))
        gradient.setColorAt(1, QColor(255, 255, 255, int(10 * self.opacity)))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 16, 16)