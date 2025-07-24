#!/usr/bin/env python3
"""
Script per executar manualment la sincronització de dades GOMPC

Aquest script permet executar la sincronització de forma manual
sense haver d'esperar al cicle automàtic de 24 hores.
"""

import sys
import os
from pathlib import Path

# Afegir src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.services.gompc_sync_service import GompcSyncService

def sync_gompc_data_manual():
    """Executa la sincronització manual de dades GOMPC"""
    print("\n" + "=" * 60)
    print("SINCRONITZACIÓ MANUAL DE DADES GOMPC")
    print("=" * 60)
    
    try:
        sync_service = GompcSyncService()
        result = sync_service.sync_data_on_startup()
        
        if result['success']:
            print(f"✅ Sincronització completada:")
            print(f"   📋 Fitxers processats: {result['csv_files_processed']}")
            print(f"   💾 Registres inserits: {result['records_inserted']}")
            print(f"   ⏱️ Temps: {result['duration_seconds']:.2f}s")
        else:
            print(f"❌ Error en la sincronització: {result['message']}")
            if result['errors']:
                for error in result['errors'][:3]:
                    print(f"   - {error}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error crític durant la sincronització: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Punt d'entrada per la sincronització manual"""
    print("🔄 Executant sincronització manual...")
    
    result = sync_gompc_data_manual()
    
    if result['success']:
        print("\n✅ Procés completat amb èxit!")
    else:
        print("\n❌ Error durant el procés.")
        sys.exit(1)

if __name__ == "__main__":
    main()
