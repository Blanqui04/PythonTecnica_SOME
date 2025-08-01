#!/usr/bin/env python3
"""
Script per monitoritzar el progrés de la còpia de dades
"""
import json
import psycopg2
import time
from datetime import datetime

def connect_to_db(config):
    """Connecta a una base de dades"""
    try:
        connection = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            client_encoding='utf8'
        )
        return connection
    except Exception:
        return None

def monitor_progress():
    """Monitoritza el progrés de la còpia"""
    
    # Carregar configuració
    try:
        db_config_path = r"C:\Github\PythonTecnica_SOME\PythonTecnica_SOME\config\database\db_config.json"
        with open(db_config_path, 'r') as f:
            full_config = json.load(f)
        
        source_config = full_config['secondary']  # airflow_db
        target_config = full_config['primary']    # documentacio_tecnica
        
    except Exception as e:
        print(f"❌ Error carregant configuració: {e}")
        return
    
    print("🔍 MONITORITZACIÓ DE LA CÒPIA DE DADES")
    print("=" * 50)
    print("Premeu Ctrl+C per aturar la monitorització")
    print("=" * 50)
    
    last_count = 0
    #start_time = datetime.now()
    
    try:
        while True:
            # Connectar
            source_conn = connect_to_db(source_config)
            target_conn = connect_to_db(target_config)
            
            if source_conn and target_conn:
                try:
                    # Comptar registres
                    with source_conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                        total_origen = cursor.fetchone()[0]
                    
                    with target_conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM mesuresqualitat")
                        total_desti = cursor.fetchone()[0]
                    
                    # Calcular progrés
                    percentatge = (total_desti / total_origen) * 100 if total_origen > 0 else 0
                    pendents = total_origen - total_desti
                    
                    # Calcular velocitat
                    if last_count > 0:
                        records_per_minute = (total_desti - last_count) * 12  # 5 segons * 12 = 1 minut
                        if records_per_minute > 0:
                            temps_restant = pendents / records_per_minute
                            temps_restant_str = f"{temps_restant:.1f} minuts"
                        else:
                            temps_restant_str = "N/A"
                    else:
                        records_per_minute = 0
                        temps_restant_str = "Calculant..."
                    
                    # Mostrar informació
                    current_time = datetime.now().strftime("%H:%M:%S")
                    print(f"\r[{current_time}] "
                          f"📊 {total_desti:,}/{total_origen:,} ({percentatge:.1f}%) "
                          f"⏱️ {records_per_minute:,.0f} reg/min "
                          f"⏳ ETA: {temps_restant_str}", end="", flush=True)
                    
                    last_count = total_desti
                    
                    # Si està completat
                    if total_desti >= total_origen:
                        print("\n\n🎉 CÒPIA COMPLETADA!")
                        break
                        
                except Exception as e:
                    print(f"\r❌ Error llegint dades: {e}", end="", flush=True)
                
                finally:
                    try:
                        source_conn.close()
                        target_conn.close()
                    except Exception:
                        pass
            else:
                print("\r❌ Error de connexió", end="", flush=True)
            
            time.sleep(5)  # Actualitzar cada 5 segons
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitorització aturada per l'usuari")
    except Exception as e:
        print(f"\n❌ Error durant la monitorització: {e}")

if __name__ == "__main__":
    monitor_progress()
