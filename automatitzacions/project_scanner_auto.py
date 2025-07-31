#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Script d'automatització per Scanner Projectes
Sincronització automàtica del path \\gompc\kiosk

Versió 1.0: Automatització completa del Scanner Projectes
Basat en els scripts d'automatització existents

Autor: Sistema Automàtic
Data: Desembre 2024
"""

import os
import sys
import logging
from datetime import datetime

# Afegir path del projecte
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from src.services.project_sync_service import ProjectSyncService
    import logging
except ImportError as e:
    print(f"Error important mòduls: {e}")
    sys.exit(1)

# Configurar logger
logger = logging.getLogger(__name__)

def main():
    """
    Funció principal d'automatització del Scanner Projectes
    """
    try:
        print("\n" + "="*70)
        print("🔄 AUTOMATITZACIÓ SCANNER PROJECTES")
        print("="*70)
        print(f"⏰ Inici: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Path: \\\\gompc\\kiosk")
        print(f"🖥️  Màquina: Scanner Projectes")
        print("-"*70)
        
        # Crear servei de sincronització
        sync_service = ProjectSyncService()
        
        # Executar sincronització
        logger.info("Iniciant automatització Scanner Projectes")
        result = sync_service.sync_project_data()
        
        # Mostrar resultats
        print(f"\n📊 RESULTATS:")
        print("-"*70)
        
        if result['success']:
            print(f"✅ ÈXIT: Sincronització completada")
            print(f"   📋 Fitxers CSV processats: {result.get('total_csv_processed', 0)}")
            print(f"   💾 Registres inserits a BBDD: {result.get('total_records_inserted', 0)}")
            print(f"   ⏱️  Temps d'execució: {result.get('duration_seconds', 0):.1f} segons")
            print(f"   🖥️  Valor màquina: {result.get('maquina_value', 'N/A')}")
            
            if result.get('process_result'):
                stats = result['process_result'].get('stats', {})
                print(f"\n📈 ESTADÍSTIQUES DETALLADES:")
                print(f"   🏗️  Projectes processats: {stats.get('projects_processed', 0)}")
                print(f"   📁 Referències processades: {stats.get('references_processed', 0)}")
                print(f"   📄 CSV trobats: {stats.get('csv_files_found', 0)}")
                print(f"   ✅ CSV processats correctament: {stats.get('csv_files_processed', 0)}")
                print(f"   ❌ CSV amb errors: {stats.get('csv_files_failed', 0)}")
                print(f"   📊 Total files inserides: {stats.get('total_rows', 0)}")
                
                if stats.get('projects_skipped'):
                    print(f"   ⏭️  Projectes saltats: {', '.join(stats['projects_skipped'])}")
                
                if stats.get('processing_errors'):
                    print(f"   ⚠️  Errors de processament:")
                    for error in stats['processing_errors'][:5]:  # Mostrar només els primers 5
                        print(f"      - {error}")
                    if len(stats['processing_errors']) > 5:
                        print(f"      ... i {len(stats['processing_errors']) - 5} errors més")
            
            logger.info(f"Automatització completada amb èxit: {result['total_csv_processed']} CSV, {result['total_records_inserted']} registres")
            
        else:
            print(f"❌ ERROR: {result.get('error', 'Error desconegut')}")
            logger.error(f"Automatització fallida: {result.get('error', 'Error desconegut')}")
            
            # Mostrar detalls d'error si estan disponibles
            if result.get('process_result') and not result['process_result'].get('success'):
                print(f"   📋 Error en processament: {result['process_result'].get('error', 'N/A')}")
            
            if result.get('db_result') and not result['db_result'].get('success'):
                print(f"   💾 Error en BBDD: {result['db_result'].get('error', 'N/A')}")
        
        print("-"*70)
        print(f"⏰ Fi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Exit code basat en l'èxit
        exit_code = 0 if result['success'] else 1
        
        if result['success']:
            print("🎉 Automatització Scanner Projectes finalitzada amb ÈXIT!")
        else:
            print("💥 Automatització Scanner Projectes finalitzada amb ERRORS!")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n🛑 Automatització interrompuda per l'usuari")
        logger.warning("Automatització interrompuda per l'usuari")
        return 2
        
    except Exception as e:
        error_msg = f"Error crític en automatització: {str(e)}"
        print(f"\n💥 ERROR CRÍTIC: {error_msg}")
        logger.error(error_msg, exc_info=True)
        return 3


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
