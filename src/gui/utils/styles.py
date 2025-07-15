def global_style():
    return """
        QWidget {
            background-color: #f8f9fa;
            color: #212529;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px;
            color: #495057;
        }
        QScrollArea {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
        }
        QLabel {
            color: #495057;
        }
    """

def header_style():
    return ""