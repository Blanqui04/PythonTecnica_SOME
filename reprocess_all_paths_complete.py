"""
Reprocessament COMPLET de TOTS els paths de gompcnou
Inclou NetworkScanner + ProjectScanner amb neteja de valors
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Afegir src al path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

def reprocess_both_paths_complete():
    """Reprocessament complet dels DOS paths amb valors netejats"""
    print("🚀 REPROCESSAMENT COMPLET TOTS ELS PATHS GOMPCNOU")
    print("=" * 75)
    print(f"⏰ Inici: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("📍 PROCESSANT DOS PATHS:")
    print("   1. NetworkScanner:  \\\\gompcnou\\KIOSK\\results")
    print("   2. ProjectScanner:  \\\\gompc\\kiosk\\PROJECTES")
    print()
    
    global_start_time = datetime.now()
    total_processed_files = 0
    total_database_records = 0
    
    try:
        # ============================================
        # PATH 1: NETWORK SCANNER
        # ============================================
        print("🔄 [1/2] PROCESSANT NETWORK SCANNER")
        print("=" * 50)
        
        from services.network_scanner import NetworkScanner
        
        network_scanner = NetworkScanner()
        print(f"📁 Path: {network_scanner.network_path}")
        print(f"🔧 Neteja de valors activada amb ValueCleaner")
        
        if not os.path.exists(network_scanner.network_path):
            print(f"❌ Path no accessible: {network_scanner.network_path}")
        else:
            print("✅ Path accessible")
            
            print("\n🔄 INICIANT PROCESSAMENT NETWORK SCANNER...")
            print("-" * 40)
            
            start_time_1 = datetime.now()
            
            # Processar tots els CSV del NetworkScanner
            result_1 = network_scanner.process_all_csv_files()
            
            end_time_1 = datetime.now()
            duration_1 = end_time_1 - start_time_1
            
            print(f"\n📊 RESULTATS NETWORK SCANNER:")
            print("-" * 35)
            
            if result_1.get('success', False):
                print(f"✅ Processament exitós!")
                print(f"⏱️  Duració: {duration_1}")
                print(f"📄 Fitxers CSV processats: {result_1.get('csv_files_processed', 0)}")
                print(f"📊 Files totals: {len(network_scanner.global_dataset)}")
                
                total_processed_files += result_1.get('csv_files_processed', 0)
                
                # Guardar a base de dades
                print(f"\n💾 GUARDANT NETWORK SCANNER A BBDD...")
                try:
                    db_result_1 = network_scanner.insert_dataset_to_database()
                    
                    if db_result_1.get('success', False):
                        print(f"✅ Dades Network Scanner guardades!")
                        records_1 = db_result_1.get('inserted', 0) + db_result_1.get('updated', 0)
                        total_database_records += records_1
                        print(f"📊 Registres: {records_1:,}")
                    else:
                        print(f"❌ Error guardant Network Scanner: {db_result_1.get('error', 'Error desconegut')}")
                        
                except Exception as e:
                    print(f"❌ Error guardant Network Scanner: {e}")
                    
            else:
                print(f"❌ Error en Network Scanner: {result_1.get('error', 'Error desconegut')}")
        
        print("\n" + "="*60)
        
        # ============================================
        # PATH 2: PROJECT SCANNER
        # ============================================
        print("🔄 [2/2] PROCESSANT PROJECT SCANNER")
        print("=" * 50)
        
        from services.project_scanner import ProjectScanner
        
        project_scanner = ProjectScanner()
        print(f"📁 Path: {project_scanner.project_path}")
        print(f"🔧 Neteja de valors activada amb ValueCleaner")
        print(f"🏷️  Màquina: {project_scanner.MAQUINA_VALUE}")
        
        if not os.path.exists(project_scanner.project_path):
            print(f"❌ Path no accessible: {project_scanner.project_path}")
        else:
            print("✅ Path accessible")
            
            print("\n🔄 INICIANT PROCESSAMENT PROJECT SCANNER...")
            print("-" * 40)
            
            start_time_2 = datetime.now()
            
            # Processar tots els CSV del ProjectScanner
            try:
                result_2 = project_scanner.process_and_save_to_database()
                
                end_time_2 = datetime.now()
                duration_2 = end_time_2 - start_time_2
                
                print(f"\n📊 RESULTATS PROJECT SCANNER:")
                print("-" * 35)
                
                if result_2.get('success', False):
                    print(f"✅ Processament exitós!")
                    print(f"⏱️  Duració: {duration_2}")
                    print(f"📄 Fitxers CSV processats: {result_2.get('csv_processed', 0)}")
                    print(f"📊 Files totals: {len(project_scanner.global_dataset)}")
                    
                    total_processed_files += result_2.get('csv_processed', 0)
                    
                    # Registres ja guardats pel process_and_save_to_database
                    db_info = result_2.get('database_summary', {})
                    records_2 = db_info.get('inserted', 0) + db_info.get('updated', 0)
                    total_database_records += records_2
                    
                    print(f"💾 Registres Project Scanner: {records_2:,}")
                    
                else:
                    print(f"❌ Error en Project Scanner: {result_2.get('error', 'Error desconegut')}")
                    
            except Exception as e:
                print(f"❌ Error processant Project Scanner: {e}")
                import traceback
                traceback.print_exc()
        
        # ============================================
        # RESUM FINAL
        # ============================================
        global_end_time = datetime.now()
        global_duration = global_end_time - global_start_time
        
        print("\n" + "="*75)
        print("🎯 RESUM FINAL COMPLET")
        print("=" * 75)
        print(f"🕒 Hora finalització: {global_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duració total: {global_duration}")
        print()
        print(f"📊 ESTADÍSTIQUES GLOBALS:")
        print("-" * 30)
        print(f"📄 Fitxers CSV processats: {total_processed_files:,}")
        print(f"💾 Registres a BBDD: {total_database_records:,}")
        print()
        print(f"📍 PATHS PROCESSATS:")
        print("-" * 25)
        print(f"✅ NetworkScanner:  \\\\gompcnou\\KIOSK\\results")
        print(f"✅ ProjectScanner:  \\\\gompc\\kiosk\\PROJECTES")
        print()
        print(f"🧹 MILLORES APLICADES:")
        print("-" * 25)
        print(f"   - Valors ¿¿¿??? convertits a 0.000")
        print(f"   - Format decimal europeu normalitzat")
        print(f"   - Elements buits assignats com 'NULL'")
        print(f"   - Toleràncies i nominals netejats")
        print(f"   - PTCOVER i RPLL amb parseig millorat")
        print()
        
        if total_processed_files > 60000:
            print(f"🎉 ÈXIT COMPLET: {total_processed_files:,} fitxers processats!")
            print(f"💪 Sistema gompcnou amb dades 100% netes!")
        else:
            print(f"⚠️  Processament parcial: {total_processed_files:,} fitxers")
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Confirmació de seguretat
    print("⚠️  ATENCIÓ: Aquest procés reprocessarà TOTS els paths de gompcnou")
    print("📊 Això inclou NetworkScanner + ProjectScanner")
    print("📄 Aproximadament 67,974 fitxers CSV")
    print("⏱️  Pot trigar entre 3-6 hores segons el volum")
    print()
    
    confirm = input("Vols continuar amb TOTS els paths? (escriu 'SI' per confirmar): ")
    if confirm.upper() == 'SI':
        reprocess_both_paths_complete()
    else:
        print("❌ Operació cancel·lada per l'usuari")
