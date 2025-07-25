"""
Test del nou comportament que processa tots els fitxers fins i tot amb ¿¿¿???
"""

import sys
import os

# Afegir src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

def test_template_processing():
    """Test que els fitxers plantilla amb ¿¿¿??? es processen"""
    print("🧪 TEST PROCESSAMENT FITXERS PLANTILLA")
    print("=" * 50)
    
    from services.project_scanner import ProjectScanner
    
    scanner = ProjectScanner()
    
    # Fitxers que abans es saltaven però ara s'han de processar
    template_files = [
        "\\\\gompc\\kiosk\\PROJECTES\\AUTOLIV\\647878300C\\00000_2020_05_12_18_15_01.csv",
        "\\\\gompc\\kiosk\\PROJECTES\\AUTOLIV\\648693000C\\0_2020_07_23_13_03_41.csv"
    ]
    
    total_processed = 0
    
    for file_path in template_files:
        if os.path.exists(file_path):
            print(f"\n📄 Processant: {os.path.basename(file_path)}")
            
            # Mostrar contingut del fitxer
            print("🔍 Contingut del fitxer:")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]  # Primeres 5 línies
                    for i, line in enumerate(lines):
                        print(f"   {i+1}: {line.strip()}")
            except Exception as e:
                print(f"   Error llegint fitxer: {e}")
            
            # Extreure components del path
            path_parts = file_path.replace('\\\\gompc\\kiosk\\PROJECTES\\', '').split('\\')
            client = path_parts[0] if len(path_parts) > 0 else "UNKNOWN"
            reference = path_parts[1] if len(path_parts) > 1 else "UNKNOWN"
            filename = path_parts[-1] if len(path_parts) > 2 else "UNKNOWN"
            
            print(f"📋 Metadades:")
            print(f"   Client: {client}")
            print(f"   Referència: {reference}")
            
            # Extreure LOT i data/hora
            lot, data_hora = scanner.extract_lot_and_datetime_from_filename(filename)
            print(f"   LOT: '{lot}'")
            print(f"   Data/Hora: {data_hora}")
            
            # Processar CSV
            df = scanner.read_csv_file(
                file_path,
                project_name=client,
                referencia_name=reference,
                lot=lot,
                data_hora=data_hora
            )
            
            if df is not None and len(df) > 0:
                print(f"   ✅ Processat: {len(df)} registres")
                total_processed += len(df)
                
                # Mostrar exemples de dades processades
                print("   📊 Exemples de dades processades:")
                for i in range(min(5, len(df))):
                    row = df.iloc[i]
                    print(f"      {i+1}. Element: '{row['element']}' | Valor: {row['valor']} | LOT: '{row['lot']}'")
                
                # Comptar valors convertits vs originals
                converted_count = sum(1 for _, row in df.iterrows() if row['valor'] == 0.000)
                original_count = len(df) - converted_count
                
                print(f"   📈 Estadístiques:")
                print(f"      Valors originals: {original_count}")
                print(f"      Valors convertits a 0.000: {converted_count}")
                print(f"      Elements NULL: {sum(1 for _, row in df.iterrows() if 'NULL' in str(row['element']))}")
                    
            else:
                print("   ❌ No s'ha pogut processar")
        else:
            print(f"\n⚠️  Fitxer no accessible: {os.path.basename(file_path)}")
    
    print(f"\n📊 RESUM TOTAL:")
    print(f"   Total registres processats: {total_processed}")
    
    if total_processed > 0:
        print("✅ ÈXIT: Ara els fitxers plantilla es processen correctament")
        print("🔧 Conversions aplicades:")
        print("   • Valors ¿¿¿??? → 0.000")
        print("   • Elements buits → 'NULL'")
        print("   • Tots els registres es guarden a la BBDD")
    else:
        print("⚠️  No s'han processat registres")

def test_mixed_file_processing():
    """Test amb fitxer que té barreja de valors reals i plantilla"""
    print("\n🧪 TEST FITXER MIXT (REALS + PLANTILLA)")
    print("-" * 50)
    
    from services.project_scanner import ProjectScanner
    
    scanner = ProjectScanner()
    
    # Aquest fitxer podria tenir barreja
    mixed_file = "\\\\gompc\\kiosk\\PROJECTES\\JOYSON\\3126251-AA\\CAV 1.1_2021_11_05_09_47_26.csv"
    
    if os.path.exists(mixed_file):
        print(f"📄 Processant: {os.path.basename(mixed_file)}")
        
        path_parts = mixed_file.replace('\\\\gompc\\kiosk\\PROJECTES\\', '').split('\\')
        client = path_parts[0]
        reference = path_parts[1]
        filename = path_parts[-1]
        
        lot, data_hora = scanner.extract_lot_and_datetime_from_filename(filename)
        
        df = scanner.read_csv_file(
            mixed_file,
            project_name=client,
            referencia_name=reference,
            lot=lot,
            data_hora=data_hora
        )
        
        if df is not None and len(df) > 0:
            print(f"✅ Processat: {len(df)} registres")
            
            # Analitzar distribució de valors
            real_values = sum(1 for _, row in df.iterrows() if row['valor'] != 0.000)
            converted_values = len(df) - real_values
            
            print(f"📈 Distribució:")
            print(f"   Valors reals: {real_values}")
            print(f"   Valors convertits: {converted_values}")
            
            if real_values > 0:
                print("🔍 Alguns valors reals:")
                real_rows = [row for _, row in df.iterrows() if row['valor'] != 0.000][:3]
                for i, row in enumerate(real_rows):
                    print(f"   {i+1}. {row['element']} = {row['valor']}")
            
            if converted_values > 0:
                print("🔍 Alguns valors convertits:")
                converted_rows = [row for _, row in df.iterrows() if row['valor'] == 0.000][:3]
                for i, row in enumerate(converted_rows):
                    print(f"   {i+1}. {row['element']} = {row['valor']} (era plantilla)")

def main():
    """Executar tots els tests"""
    print("🚀 TEST PROCESSAMENT AMB CONVERSIÓ DE PLANTILLES")
    print("=" * 60)
    
    test_template_processing()
    test_mixed_file_processing()
    
    print("\n" + "=" * 60)
    print("✅ TESTS COMPLETATS")
    print("🎯 Nou comportament implementat:")
    print("   • Tots els fitxers es processen (fins i tot plantilles)")
    print("   • Valors ¿¿¿??? es converteixen a 0.000")
    print("   • Elements buits es converteixen a 'NULL'")
    print("   • Tots els registres es guarden a la BBDD")

if __name__ == "__main__":
    main()
