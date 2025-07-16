from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt

class ElementInputWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.elements = []  # Llista per guardar els elements

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- Formulari d'entrada ---
        form_layout = QHBoxLayout()

        # Element ID
        self.element_id_input = QLineEdit()
        self.element_id_input.setPlaceholderText("Element ID")
        form_layout.addWidget(QLabel("Element ID:"))
        form_layout.addWidget(self.element_id_input)

        # Classe (cc/sc)
        self.class_combo = QComboBox()
        self.class_combo.addItems(["cc", "sc"])
        form_layout.addWidget(QLabel("Classe:"))
        form_layout.addWidget(self.class_combo)

        # Cavitat
        self.cavity_input = QLineEdit()
        self.cavity_input.setPlaceholderText("Cavitat")
        form_layout.addWidget(QLabel("Cavitat:"))
        form_layout.addWidget(self.cavity_input)

        # Número batch (opcional)
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("Batch (opcional)")
        form_layout.addWidget(QLabel("Batch:"))
        form_layout.addWidget(self.batch_input)

        main_layout.addLayout(form_layout)

        # --- Valor nominal i toleràncies ---
        tol_layout = QHBoxLayout()

        self.nominal_input = QLineEdit()
        self.nominal_input.setPlaceholderText("Valor Nominal (float)")
        tol_layout.addWidget(QLabel("Valor Nominal:"))
        tol_layout.addWidget(self.nominal_input)

        self.tol_minus_input = QLineEdit()
        self.tol_minus_input.setPlaceholderText("Tolerància Inferior (float)")
        tol_layout.addWidget(QLabel("Tol. -:"))
        tol_layout.addWidget(self.tol_minus_input)

        self.tol_plus_input = QLineEdit()
        self.tol_plus_input.setPlaceholderText("Tolerància Superior (float)")
        tol_layout.addWidget(QLabel("Tol. +:"))
        tol_layout.addWidget(self.tol_plus_input)

        main_layout.addLayout(tol_layout)

        # --- Valors mesurats (10 valors) ---
        self.values_inputs = []
        values_layout = QHBoxLayout()
        for i in range(10):
            inp = QLineEdit()
            inp.setPlaceholderText(f"Val {i+1}")
            inp.setFixedWidth(50)
            self.values_inputs.append(inp)
            values_layout.addWidget(inp)
        main_layout.addWidget(QLabel("10 Valors mesurats:"))
        main_layout.addLayout(values_layout)

        # --- Botó per afegir element ---
        self.add_button = QPushButton("Afegir Element")
        self.add_button.clicked.connect(self.add_element)
        main_layout.addWidget(self.add_button)

        # --- Taula per mostrar elements afegits ---
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Element ID", "Classe", "Cavitat", "Batch",
            "Nominal", "Tol. -", "Tol. +", "Valors mesurats", "Accions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        # --- Botó per iniciar estudi ---
        self.run_button = QPushButton("Iniciar Estudi de Capacitat")
        self.run_button.clicked.connect(self.run_study)
        main_layout.addWidget(self.run_button)

        self.setLayout(main_layout)

    def add_element(self):
        # Validació i agregació
        element_id = self.element_id_input.text().strip()
        element_type = self.class_combo.currentText()
        cavity = self.cavity_input.text().strip()
        batch = self.batch_input.text().strip()
        nominal = self.nominal_input.text().strip()
        tol_minus = self.tol_minus_input.text().strip()
        tol_plus = self.tol_plus_input.text().strip()
        values = [inp.text().strip() for inp in self.values_inputs]

        # Validacions bàsiques
        if not element_id:
            self._show_error("Element ID no pot estar buit.")
            return
        if not cavity:
            self._show_error("Cavitat no pot estar buit.")
            return
        try:
            nominal_f = float(nominal)
            tol_minus_f = float(tol_minus)
            tol_plus_f = float(tol_plus)
            values_f = [float(v) for v in values]
            if len(values_f) != 10:
                self._show_error("S'han d'introduir 10 valors mesurats.")
                return
        except ValueError:
            self._show_error("Els valors numèrics no són vàlids.")
            return

        # Afegim element a la llista
        element = {
            "element_id": element_id,
            "class": element_type,
            "cavity": cavity,
            "batch": batch,
            "nominal": nominal_f,
            "tol_minus": tol_minus_f,
            "tol_plus": tol_plus_f,
            "values": values_f,
        }
        self.elements.append(element)

        # Actualitzar taula
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(element_id))
        self.table.setItem(row, 1, QTableWidgetItem(element_type))
        self.table.setItem(row, 2, QTableWidgetItem(cavity))
        self.table.setItem(row, 3, QTableWidgetItem(batch))
        self.table.setItem(row, 4, QTableWidgetItem(str(nominal_f)))
        self.table.setItem(row, 5, QTableWidgetItem(str(tol_minus_f)))
        self.table.setItem(row, 6, QTableWidgetItem(str(tol_plus_f)))
        self.table.setItem(row, 7, QTableWidgetItem(", ".join(f"{v:.3f}" for v in values_f)))

        # Botó eliminar fila
        btn_delete = QPushButton("Eliminar")
        btn_delete.clicked.connect(lambda _, r=row: self._remove_element(r))
        self.table.setCellWidget(row, 8, btn_delete)

        # Netejar inputs
        self._clear_inputs()

    def _remove_element(self, row):
        # Elimina element i fila
        if 0 <= row < len(self.elements):
            del self.elements[row]
            self.table.removeRow(row)
            # Reassignem els botons eliminar perquè el índex és canviat
            for r in range(self.table.rowCount()):
                widget = self.table.cellWidget(r, 8)
                if widget:
                    widget.clicked.disconnect()
                    widget.clicked.connect(lambda _, rr=r: self._remove_element(rr))

    def _clear_inputs(self):
        self.element_id_input.clear()
        self.cavity_input.clear()
        self.batch_input.clear()
        self.nominal_input.clear()
        self.tol_minus_input.clear()
        self.tol_plus_input.clear()
        for inp in self.values_inputs:
            inp.clear()

    def _show_error(self, msg):
        QMessageBox.critical(self, "Error d'entrada", msg)

    def run_study(self):
        if not self.elements:
            self._show_error("No hi ha elements afegits per a l'estudi.")
            return

        # Aquí cridarem la funcionalitat d'estudi de capacitat (pot ser un senyal o callback)
        # Per ara simplement mostrarem la info al widget pare:
        summary = f"S'inicia estudi de capacitat amb {len(self.elements)} elements.\n"
        for e in self.elements:
            summary += f"- {e['element_id']} ({e['class']}), Cavitat {e['cavity']}, Batch {e['batch']}, Nominal {e['nominal']}, Tol- {e['tol_minus']}, Tol+ {e['tol_plus']}, Valors: {e['values']}\n"

        # Cridem un mètode del pare (MainWindow) per executar estudi
        if hasattr(self.parent(), "run_capacity_study_with_elements"):
            self.parent().run_capacity_study_with_elements(self.elements)
        else:
            QMessageBox.information(self, "Estudi", summary)
