"""Modern stylesheet definitions with dark theme and glassmorphism effects."""

MODERN_DARK_STYLE = """
/* Global Application Style */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0a0e27, stop:0.5 #151932, stop:1 #1e2139);
}

/* Central Widget with subtle gradient */
QWidget {
    background-color: transparent;
    color: #e4e7eb;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 14px;
}

/* Tab Widget with glassmorphism effect */
QTabWidget::pane {
    background: rgba(20, 25, 40, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    margin-top: -1px;
    padding: 8px;
}

QTabBar::tab {
    background: rgba(30, 35, 50, 0.6);
    color: #a0a8b7;
    padding: 8px 16px;
    margin: 0 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
    min-width: 80px;
    font-size: 13px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(88, 101, 242, 0.4), stop:1 rgba(88, 101, 242, 0.2));
    color: #ffffff;
    border: 1px solid rgba(88, 101, 242, 0.6);
    border-bottom: none;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background: rgba(88, 101, 242, 0.15);
    color: #d0d5dd;
}

/* Modern Buttons with gradient and animations */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #5865f2, stop:1 #4752c4);
    color: white;
    border: none;
    padding: 4px 10px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 11px;
    min-height: 12px;
    max-height: 26px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6574ff, stop:1 #5865f2);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #4752c4, stop:1 #3c45a5);
}

QPushButton:disabled {
    background: rgba(88, 101, 242, 0.3);
    color: rgba(255, 255, 255, 0.5);
}

/* Secondary Button Style */
QPushButton[class="secondary"] {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

QPushButton[class="secondary"]:hover {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
}

/* Danger Button Style */
QPushButton[class="danger"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #ed4245, stop:1 #c93639);
}

QPushButton[class="danger"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f04747, stop:1 #ed4245);
}

/* Modern Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit {
    background: rgba(10, 15, 30, 0.6);
    border: 1px solid rgba(88, 101, 242, 0.3);
    border-radius: 4px;
    padding: 4px 8px;
    color: #e4e7eb;
    font-size: 11px;
    selection-background-color: #5865f2;
    max-height: 24px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #5865f2;
    background: rgba(10, 15, 30, 0.8);
    outline: none;
}

/* Modern ComboBox */
QComboBox {
    background: rgba(30, 35, 50, 0.8);
    border: 1px solid rgba(88, 101, 242, 0.3);
    border-radius: 4px;
    padding: 4px 8px;
    color: #e4e7eb;
    min-height: 14px;
    max-height: 24px;
    font-size: 11px;
}

QComboBox:hover {
    border: 2px solid rgba(88, 101, 242, 0.5);
    background: rgba(30, 35, 50, 0.9);
}

QComboBox:focus {
    border: 2px solid #5865f2;
    background: rgba(30, 35, 50, 1);
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 8px solid #a0a8b7;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background: rgba(20, 25, 40, 0.95);
    border: 1px solid rgba(88, 101, 242, 0.3);
    border-radius: 8px;
    selection-background-color: #5865f2;
    padding: 4px;
}

/* Modern Slider */
QSlider::groove:horizontal {
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #6574ff, stop:1 #5865f2);
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
    border: 2px solid rgba(255, 255, 255, 0.2);
}

QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #7584ff, stop:1 #6574ff);
    border: 2px solid rgba(255, 255, 255, 0.3);
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4752c4, stop:1 #5865f2);
    border-radius: 3px;
}

/* Modern Spin Box */
QSpinBox, QDoubleSpinBox {
    background: rgba(30, 35, 50, 0.8);
    border: 1px solid rgba(88, 101, 242, 0.3);
    border-radius: 4px;
    padding: 4px 8px;
    padding-right: 20px;
    color: #e4e7eb;
    font-size: 11px;
    max-height: 24px;
    selection-background-color: #5865f2;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #5865f2;
    background: rgba(30, 35, 50, 1);
    outline: none;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border: 1px solid rgba(88, 101, 242, 0.5);
    background: rgba(30, 35, 50, 0.9);
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background: rgba(88, 101, 242, 0.2);
    border: none;
    border-left: 1px solid rgba(88, 101, 242, 0.3);
    border-bottom: 1px solid rgba(88, 101, 242, 0.3);
    width: 18px;
    border-top-right-radius: 4px;
    margin-right: 1px;
    margin-top: 1px;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: rgba(88, 101, 242, 0.2);
    border: none;
    border-left: 1px solid rgba(88, 101, 242, 0.3);
    border-top: 1px solid rgba(88, 101, 242, 0.3);
    width: 18px;
    border-bottom-right-radius: 4px;
    margin-right: 1px;
    margin-bottom: 1px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background: rgba(88, 101, 242, 0.4);
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: rgba(88, 101, 242, 0.4);
}

QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {
    background: rgba(88, 101, 242, 0.6);
}

QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
    background: rgba(88, 101, 242, 0.6);
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 6px solid #e4e7eb;
    width: 0;
    height: 0;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #e4e7eb;
    width: 0;
    height: 0;
}

QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {
    border-bottom: 6px solid #ffffff;
}

QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {
    border-top: 6px solid #ffffff;
}

QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled {
    border-bottom: 6px solid #666;
}

QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled {
    border-top: 6px solid #666;
}

/* Ensure spinbox text area doesn't overlap buttons */
QSpinBox {
    padding-right: 20px;
}

QDoubleSpinBox {
    padding-right: 20px;
}

/* Make sure buttons are always visible */
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
}

/* Modern Group Box */
QGroupBox {
    background: rgba(20, 25, 40, 0.4);
    border: 1px solid rgba(88, 101, 242, 0.2);
    border-radius: 6px;
    margin-top: 6px;
    padding-top: 8px;
    font-weight: 600;
    font-size: 11px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #a0a8b7;
    background: transparent;
    font-size: 11px;
}

/* Modern Check Box and Radio Button */
QCheckBox, QRadioButton {
    color: #e4e7eb;
    spacing: 4px;
    font-size: 11px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 14px;
    height: 14px;
    background: rgba(30, 35, 50, 0.8);
    border: 1px solid rgba(88, 101, 242, 0.3);
}

QCheckBox::indicator {
    border-radius: 3px;
}

QRadioButton::indicator {
    border-radius: 8px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border: 2px solid rgba(88, 101, 242, 0.5);
    background: rgba(88, 101, 242, 0.1);
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #5865f2, stop:1 #4752c4);
    border: 2px solid #5865f2;
}

QCheckBox::indicator:checked {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwLjUgM0w0LjUgOUwxLjUgNiIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
}

QRadioButton::indicator:checked {
    image: none;
}

QRadioButton::indicator:checked::after {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 4px;
    background: white;
    position: absolute;
    left: 6px;
    top: 6px;
}

/* Modern List Widget */
QListWidget, QTreeWidget, QTableWidget {
    background: rgba(10, 15, 30, 0.6);
    border: 1px solid rgba(88, 101, 242, 0.2);
    border-radius: 6px;
    padding: 6px;
    outline: none;
    color: #e4e7eb;
}

QListWidget::item, QTreeWidget::item, QTableWidget::item {
    padding: 4px;
    border-radius: 3px;
    margin: 1px 0;
    min-height: 16px;
    font-size: 11px;
}

QListWidget::item:hover, QTreeWidget::item:hover, QTableWidget::item:hover {
    background: rgba(88, 101, 242, 0.15);
}

QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {
    background: rgba(88, 101, 242, 0.3);
    color: white;
}

/* Modern Scroll Bar */
QScrollBar:vertical {
    background: rgba(255, 255, 255, 0.05);
    width: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: rgba(88, 101, 242, 0.5);
    min-height: 30px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(88, 101, 242, 0.7);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}

QScrollBar:horizontal {
    background: rgba(255, 255, 255, 0.05);
    height: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: rgba(88, 101, 242, 0.5);
    min-width: 30px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal:hover {
    background: rgba(88, 101, 242, 0.7);
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: none;
}

/* Modern Progress Bar */
QProgressBar {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: 10px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4752c4, stop:0.5 #5865f2, stop:1 #6574ff);
    border-radius: 6px;
}

/* Modern Tool Tip */
QToolTip {
    background: rgba(20, 25, 40, 0.95);
    border: 1px solid rgba(88, 101, 242, 0.3);
    border-radius: 8px;
    padding: 8px 12px;
    color: #e4e7eb;
    font-size: 13px;
}

/* Modern Menu Bar */
QMenuBar {
    background: rgba(15, 20, 35, 0.95);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 2px;
    spacing: 2px;
    font-size: 13px;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    color: #a0a8b7;
    font-size: 13px;
}

QMenuBar::item:selected {
    background: rgba(88, 101, 242, 0.2);
    color: white;
}

QMenuBar::item:pressed {
    background: rgba(88, 101, 242, 0.3);
}

/* Modern Menu */
QMenu {
    background: rgba(20, 25, 40, 0.95);
    border: 1px solid rgba(88, 101, 242, 0.2);
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 16px 8px 12px;
    border-radius: 4px;
    margin: 1px 2px;
    color: #e4e7eb;
    font-size: 13px;
}

QMenu::item:selected {
    background: rgba(88, 101, 242, 0.3);
    color: white;
}

QMenu::separator {
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: 6px 0;
}

/* Modern Status Bar */
QStatusBar {
    background: rgba(15, 20, 35, 0.95);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    color: #a0a8b7;
    font-size: 13px;
    padding: 4px;
}

/* Modern Splitter */
QSplitter::handle {
    background: rgba(88, 101, 242, 0.3);
    border-radius: 2px;
}

QSplitter::handle:horizontal {
    width: 3px;
    min-width: 3px;
    max-width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
    min-height: 3px;
    max-height: 3px;
}

QSplitter::handle:hover {
    background: rgba(88, 101, 242, 0.4);
}

/* Modern Label */
QLabel {
    color: #e4e7eb;
    background: transparent;
    font-size: 11px;
    padding: 1px;
}

QLabel[class="heading"] {
    font-size: 14px;
    font-weight: bold;
    color: white;
    margin: 4px 0 2px 0;
}

QLabel[class="subheading"] {
    font-size: 12px;
    font-weight: 600;
    color: #a0a8b7;
    margin: 2px 0;
}

/* Glass Card Effect */
QFrame[class="glass-card"] {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 6px;
}

/* Animated Glow Effect */
QPushButton[class="glow"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #5865f2, stop:1 #4752c4);
}

/* Success Style */
QLabel[class="success"] {
    color: #57f287;
    font-weight: 600;
}

/* Warning Style */
QLabel[class="warning"] {
    color: #fee75c;
    font-weight: 600;
}

/* Error Style */
QLabel[class="error"] {
    color: #ed4245;
    font-weight: 600;
}

/* Info Style */
QLabel[class="info"] {
    color: #5865f2;
    font-weight: 600;
}
"""

def apply_modern_style(app):
    """Apply modern dark style to the application."""
    app.setStyleSheet(MODERN_DARK_STYLE)