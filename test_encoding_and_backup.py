#!/usr/bin/env python3
"""
Test de la neteja d'encoding i backup scheduler
"""

import os
import sys
import pandas as pd
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.quality_measurement_adapter import QualityMeasurementDBAdapter

def test_encoding_cleanup():
    print("============================================================")
    print("TEST DE NETEJA D'ENCODING")
    print("============================================================")
    
    # Crear dades de test amb caràcters problemàtics
    test_data = {
        'Element': ['Test_Ø', 'Element_Δ', 'Part_μ'],
        'Property': ['Posición°', 'Diámetro±', 'Ángulo²'],
        'Nominal': [10.0, 20.5, 30.0],
        'Actual': [10.1, 20.3, 29.8],
        'CLIENT': ['TEST_Ñ', 'CLIENT_Ç', 'SOME_ß'],
        'REFERENCIA': ['REF_Ä', 'REF_Ö', 'REF_Ü'],
        'LOT': ['LOT_æ', 'LOT_å', 'LOT_ø'],
        'DATA_HORA': ['2025-01-01 10:00:00', '2025-01-01 11:00:00', '2025-01-01 12:00:00']
    }
    
    df = pd.DataFrame(test_data)
    print("📋 DADES ORIGINALS AMB CARÀCTERS PROBLEMÀTICS:")
    print(df.to_string())
    
    # Configuració BBDD
    db_config = {
        'host': '172.26.5.159',
        'port': 5433,
        'database': 'documentacio_tecnica',
        'user': 'administrador',
        'password': 'Some2025.!$%'
    }
    
    # Crear adaptador
    adapter = QualityMeasurementDBAdapter(db_config)
    
    print("\n🧹 APLICANT NETEJA D'ENCODING...")
    cleaned_df = adapter._clean_encoding_issues(df)
    
    print("\n📋 DADES DESPRÉS DE LA NETEJA:")
    print(cleaned_df.to_string())
    
    print("\n🔍 CANVIS REALITZATS:")
    for col in df.columns:
        if df[col].dtype == 'object':
            for i in range(len(df)):
                original = str(df.iloc[i][col])
                cleaned = str(cleaned_df.iloc[i][col])
                if original != cleaned:
                    print(f"   {col}[{i}]: '{original}' -> '{cleaned}'")
    
    print("\n✅ Test de neteja d'encoding completat!")

def test_backup_scheduler():
    print("\n============================================================")
    print("TEST DEL BACKUP SCHEDULER")
    print("============================================================")
    
    try:
        from services.gompc_backup_scheduler import GompcBackupScheduler
        
        print("📅 Creant scheduler de backup...")
        scheduler = GompcBackupScheduler()
        
        print("🕐 Configurant backup cada 24 hores...")
        scheduler.start_scheduler()
        
        next_backup = scheduler.get_next_backup_time()
        if next_backup:
            print(f"✅ Scheduler configurat correctament")
            print(f"   Propera execució: {next_backup}")
        
        print("\n🔥 Provant backup manual...")
        scheduler.force_backup_now()
        
        print("\n⏹️ Aturant scheduler...")
        scheduler.stop_scheduler()
        
        print("✅ Test del backup scheduler completat!")
        
    except Exception as e:
        print(f"❌ Error en el test del scheduler: {e}")

if __name__ == "__main__":
    test_encoding_cleanup()
    test_backup_scheduler()
