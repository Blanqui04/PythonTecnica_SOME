# src/gui/utils/element_input_styles.py


def get_element_input_styles():
    return """
    QWidget {
        background-color: #f5f6fa;
        color: #2c3e50;
        font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif;
    }

    QGroupBox {
        background-color: #ffffff;
        border: 2px solid #ecf0f1;
        border-radius: 12px;
        padding: 30px 20px 20px 20px;
        margin: 15px 0;
        font-weight: 600;
        font-size: 12px;
        color: #34495e;
    }

    QLabel {
        font-size: 11px;
        font-weight: 500;
        color: #2c3e50;
    }

    QLineEdit, QComboBox {
        padding: 6px 10px;
        border: 1px solid #bdc3c7;
        border-radius: 6px;
        font-size: 11px;
    }

    QLineEdit:focus, QComboBox:focus {
        border: 1px solid #3498db;
    }

    QPushButton {
        padding: 8px 16px;
        border: none;
        border-radius: 8px;
        background-color: #2980b9;
        color: white;
        font-weight: bold;
        font-size: 12px;
    }

    QPushButton:hover {
        background-color: #3498db;
    }

    QPushButton:pressed {
        background-color: #2471a3;
    }
    """


def get_message_box_style(box_type="info"):
    base_style = """
    QMessageBox {
        background-color: #f5f6fa;
        border: 2px solid #bdc3c7;
        border-radius: 10px;
        font-family: "Segoe UI", sans-serif;
        color: #2c3e50;
    }

    QLabel {
        font-size: 12px;
    }
    """

    button_styles = {
        "error": """
        QPushButton {
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
        }

        QPushButton:hover {
            background-color: #c0392b;
        }
        """,
        "warning": """
        QPushButton {
            background-color: #f1c40f;
            color: #2c3e50;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
        }

        QPushButton:hover {
            background-color: #d4ac0d;
        }
        """,
        "question": """
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }
        """,
        "info": """
        QPushButton {
            background-color: #2ecc71;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
        }

        QPushButton:hover {
            background-color: #27ae60;
        }
        """,
    }

    return base_style + button_styles.get(box_type, button_styles["info"])
