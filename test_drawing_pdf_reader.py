"""
Test per al Drawing PDF Reader

Aquest test verifica la funcionalitat de cerca i guardada de PDFs de dibuixos.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.drawing_pdf_reader import DrawingPDFReader


def test_drawing_info():
    """Test per obtenir informació sobre dibuixos disponibles"""
    print("=== Test d'Informació de Dibuixos ===")
    
    # Usar l'exemple de l'usuari
    client_name = "AUTOLIV"
    project_id = "658061600"
    
    reader = DrawingPDFReader(client_name, project_id)
    info = reader.get_drawings_info()
    
    print(f"Client: {client_name}")
    print(f"Projecte: {project_id}")
    print(f"Path de dibuixos: {info.get('drawings_path', 'N/A')}")
    print()
    
    if info['success']:
        print(f"✓ Èxit! Trobats {info['total_count']} PDFs de dibuixos:")
        print()
        
        for pdf in info['pdfs_found']:
            print(f"📄 {pdf['filename']}")
            print(f"   Número de dibuix: {pdf['drawing_number']}")
            print(f"   Versió: {pdf['version']}")
            print(f"   Mida: {pdf['file_size']:,} bytes")
            print()
    else:
        print(f"✗ Error: {info['error']}")
    
    return info


def test_read_and_save():
    """Test per llegir i guardar dibuixos (només si el servidor és accessible)"""
    print("\n" + "=" * 50)
    print("=== Test de Lectura i Guardada ===")
    
    client_name = "AUTOLIV"
    project_id = "658061600"
    
    reader = DrawingPDFReader(client_name, project_id)
    
    # Primer comprovar si el servidor és accessible
    if not reader._validate_server_connection():
        print("❌ Servidor no accessible - Salt de test de guardada")
        return
    
    print("🔍 Servidor accessible, procedint amb la lectura i guardada...")
    
    result = reader.read_and_save_drawings()
    
    if result['success']:
        print(f"✓ Èxit!")
        print(f"  PDFs trobats: {result['pdfs_found']}")
        print(f"  PDFs guardats: {result['pdfs_saved']}")
        print(f"  Missatge: {result['message']}")
        
        if result.get('pdf_list'):
            print("  Fitxers processats:")
            for pdf_name in result['pdf_list']:
                print(f"    • {pdf_name}")
    else:
        print(f"✗ Error: {result['error']}")
        print(f"  PDFs trobats: {result['pdfs_found']}")
        print(f"  PDFs guardats: {result['pdfs_saved']}")


def test_filename_pattern():
    """Test del patró de noms de fitxers"""
    print("\n" + "=" * 50)
    print("=== Test de Patró de Noms ===")
    
    import re
    
    # Exemples de noms de fitxers
    test_files = [
        "6580615_005.pdf",  # Vàlid
        "658061_003.pdf",   # Vàlid
        "658_001.pdf",      # Vàlid
        "abc123_002.pdf",   # No vàlid (no comença amb 658)
        "6580615.pdf",      # No vàlid (no té versió)
        "6580615_abc.pdf",  # No vàlid (versió no numèrica)
    ]
    
    project_id = "658061600"
    project_prefix = project_id[:3]  # "658"
    
    print(f"Project ID: {project_id}")
    print(f"Prefix esperat: {project_prefix}")
    print()
    
    # Patró del reader
    filename_pattern = re.compile(rf"({re.escape(project_prefix)}\d*)_(\d+)\.pdf$", re.IGNORECASE)
    
    for filename in test_files:
        match = filename_pattern.match(filename)
        if match:
            drawing_number = match.group(1)
            version = int(match.group(2))
            print(f"✓ {filename} → Dibuix: {drawing_number}, Versió: {version}")
        else:
            print(f"✗ {filename} → No coincideix amb el patró")


def main():
    """Executar tots els tests"""
    print("Iniciant tests del Drawing PDF Reader...")
    print("=" * 50)
    
    # Test 1: Patró de noms
    test_filename_pattern()
    
    # Test 2: Informació de dibuixos
    info = test_drawing_info()
    
    # Test 3: Lectura i guardada (només si el servidor és accessible)
    if info.get('success') or input("\nVols forçar el test de guardada? (y/N): ").lower() == 'y':
        test_read_and_save()
    
    print("\n" + "=" * 50)
    print("Tests completats!")


if __name__ == "__main__":
    main()
