import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from kop_csv import main as l_kop, ref_project, client
from csv_func import main as l_csv
from to_sql import main as act_bbdd

dir_images = os.path.join(os.path.dirname(__file__), "ui_images")

class DatabaseUI(QWidget):
    
    def accio_dimensional(self):
        print("Has premut Estudi Dimensional")

    def accio_capacitat(self):
        print("Has premut Estudi de capacitat")

    def accio_planol(self):
        print("Has premut Veure Planol")

    def accio_matriu(self):
        print("Has premut Veure Matriu")
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database UI")
        self.setup_window()
        self.init_ui()

    def setup_window(self):
        # Detect screen size and set window size to half the area, centered
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry() # type: ignore
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()
        # Calculate half area (sqrt(0.5) ≈ 0.707 for each dimension)
        factor = 0.707
        win_width = int(screen_width * factor)
        win_height = int(screen_height * factor)
        self.resize(win_width, win_height)
        # Center the window
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        self.move(x, y)
        # Set default font (easy to change here)
        default_font = QFont("Segoe UI", 12)  # Change font family and size here
        QApplication.instance().setFont(default_font) # type: ignore

    def init_ui(self):
        # Top layout
        logo = QLabel()
        logo_path = os.path.join(dir_images, "logo_some.png")
        logo_pixmap = QPixmap(logo_path)
        logo.setPixmap(logo_pixmap.scaledToHeight(48, Qt.SmoothTransformation)) # type: ignore

        num_oferta = QLineEdit()
        num_oferta.setPlaceholderText("Num_Oferta")
        ref_client = QLineEdit()
        ref_client.setPlaceholderText("Ref_Client")
        search_button = QPushButton("Cerca")
        client_name = QLabel("Nom_Client")  # <-- Aquí pots posar el nom real del client
        projecte = QLabel("Ref_projecte")

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo)
        top_layout.addStretch()
        top_layout.addWidget(num_oferta)
        top_layout.addWidget(ref_client)
        top_layout.addWidget(search_button)
        top_layout.addStretch()
        top_layout.addWidget(client_name)  # Afegeix el nom del client al costat de projecte
        top_layout.addStretch()
        top_layout.addWidget(projecte)

        # Side buttons
        left_buttons = QVBoxLayout()
        # ...dins de init_ui, crea i connecta cada botó així:
        btn = QPushButton("Estudi Dimensional")
        btn.setMinimumHeight(60)
        btn.clicked.connect(self.accio_dimensional)
        left_buttons.addWidget(btn)

        btn = QPushButton("Estudi de capacitat")
        btn.setMinimumHeight(60)
        btn.clicked.connect(self.accio_capacitat)
        left_buttons.addWidget(btn)

        btn = QPushButton("Veure Planol")
        btn.setMinimumHeight(60)
        btn.clicked.connect(self.accio_planol)
        left_buttons.addWidget(btn)

        btn = QPushButton("Veure Matriu")
        btn.setMinimumHeight(60)
        btn.clicked.connect(self.accio_matriu)
        left_buttons.addWidget(btn)

        btn = QPushButton("Llegir KOP")
        btn.setMinimumHeight(60)
        btn.clicked.connect(l_kop) # type: ignore
        left_buttons.addWidget(btn)
        
        btn = QPushButton("Processar CSV")
        btn.setMinimumHeight(60)
        btn.clicked.connect(l_csv) # type: ignore
        left_buttons.addWidget(btn)
        
        btn = QPushButton("Actualitzar B.B.D.D.")
        btn.setMinimumHeight(60)
        btn.clicked.connect(act_bbdd)
        left_buttons.addWidget(btn)
        
        for _ in range(1):
            btn = QPushButton("Executar XXXX")
            btn.setMinimumHeight(60)
            btn.clicked.connect(self.placeholder_action)
            left_buttons.addWidget(btn)

        right_buttons = QVBoxLayout()
        for label in ["Editar Dimensional", "Editar Estudi.", "Obrir Plànol", "Obrir Carpeta"]:
            btn = QPushButton(label)
            btn.setMinimumHeight(60)
            btn.clicked.connect(self.placeholder_action)
            right_buttons.addWidget(btn)
        for _ in range(3):
            btn = QPushButton("Executar XXXX")
            btn.setMinimumHeight(60)
            btn.clicked.connect(self.placeholder_action)
            right_buttons.addWidget(btn)

        # Center visualizer
        visualizer = QLabel("Visualizer Area")  # Crea un QLabel que actuarà com a àrea central de visualització
        visualizer.setStyleSheet("background-color: lightgray;")  # Fons gris clar per destacar l'àrea
        visualizer.setMinimumSize(300, 650)  # Mida mínima (amplada, alçada) perquè mai sigui massa petit
        visualizer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Permet que creixi tant com pugui dins el layout
        visualizer.setAlignment(Qt.AlignCenter)  # type: ignore # Centra el text dins del QLabel

        # Layout central vertical per centrar el visualitzador
        center_vbox = QVBoxLayout()  # Layout vertical per centrar el visualitzador dins l'espai central
        center_vbox.addStretch(1)    # Afegeix espai flexible a dalt (per centrat vertical)
        center_vbox.addWidget(visualizer)  # Afegeix el visualitzador al layout
        center_vbox.addStretch(1)    # Afegeix espai flexible a baix (per centrat vertical)

        # Layout horitzontal amb botons laterals i el visualitzador gran al centre
        center_layout = QHBoxLayout()  # Layout horitzontal principal del centre de la finestra
        center_layout.addLayout(left_buttons, stretch=1)  # Afegeix els botons de l'esquerra
        center_layout.addSpacing(5)           # Espai entre botons esquerra i visualitzador
        center_layout.addLayout(center_vbox, stretch=3)  # Afegeix el visualitzador centrat, amb més pes (més gran)
        center_layout.addSpacing(5)           # Espai entre visualitzador i botons dreta
        center_layout.addLayout(right_buttons, stretch=1) # Afegeix els botons de la dreta

        # Main layout
        main_layout = QVBoxLayout()  # Layout vertical principal de tota la finestra
        main_layout.addLayout(top_layout)     # Afegeix la barra superior (logo, cerca, etc.)
        main_layout.addLayout(center_layout)  # Afegeix el centre (botons + visualitzador)

        self.setLayout(main_layout)  # Assigna el layout principal a la finestra

    def placeholder_action(self):
        print("Button clicked - placeholder action")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseUI()
    window.show()
    sys.exit(app.exec_())
