#!/usr/bin/env python3
"""
Test de la interfície amb selector de màquines
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from src.gui.widgets.element_input_widget import ElementInputWidget


def main():
    """Test the ElementInputWidget with machine selection"""
    
    app = QApplication(sys.argv)
    
    # Create widget with test data
    widget = ElementInputWidget(
        client='AUTOLIV',
        project_reference='663962200',
        batch_lot='PRJ1229836',
        machine='all'  # Start with all machines
    )
    
    widget.setWindowTitle("Test - Element Input Widget amb Selector de Màquines")
    widget.resize(1400, 900)
    widget.show()
    
    print("\n" + "="*80)
    print("TEST INTERFÍCIE AMB SELECTOR DE MÀQUINES")
    print("="*80)
    print("\nInstructions:")
    print("1. Verifica que es mostra el selector de màquines")
    print("2. Canvia entre 'GOMPC Projectes', 'GOMPC Nou' i 'Totes les màquines'")
    print("3. Selecciona 'Load from Database' mode")
    print("4. Clica 'Load Elements' per carregar elements amb la màquina seleccionada")
    print("5. Comprova que els elements carregats són correctes per la màquina")
    print("\nClient: AUTOLIV")
    print("Referència: 663962200")
    print("LOT: PRJ1229836")
    print("="*80 + "\n")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
