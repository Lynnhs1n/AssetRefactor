# QSS constants for AssetRefactor
import sys


def get_app_stylesheet() -> str:
    return """
        QPushButton {
            padding: 6px 16px;
            border-radius: 4px;
            font-size: 11pt;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #b0b0b0;
        }
        QPushButton#primary {
            background-color: #2b7cbf;
            color: white;
            border: none;
            font-weight: bold;
        }
        QPushButton#primary:hover {
            background-color: #3182ce;
        }
        QPushButton#cancel {
            background-color: #e53e3e;
            color: white;
            border: none;
        }
        QGroupBox {
            font-size: 10pt;
            font-weight: bold;
            margin-top: 6px;
            padding-top: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }
        QLineEdit {
            padding: 4px 8px;
            border: 1px solid #cccccc;
            border-radius: 3px;
        }
        QTextEdit {
            border: 1px solid #cccccc;
            border-radius: 3px;
            font-family: Consolas, Courier New, monospace;
            font-size: 9pt;
        }
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #2b7cbf;
        }
        QLabel {
            font-size: 10pt;
        }
        QLabel#license {
            font-size: 9pt;
            color: #808080;
        }
    """
