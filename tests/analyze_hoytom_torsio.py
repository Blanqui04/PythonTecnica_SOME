#!/usr/bin/env python3
"""
Anàlisi de les taules Hoytom i Torsió per integració
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService


def analyze_hoytom_structure():
    """Analitza l'estructura de la taula Hoytom"""
    print("\n" + "="*80)
    print("ANÀLISI TAULA HOYTOM")
    print("="*80)
    
    service = MeasurementHistoryService()
    db = service.db_connection
    
    try:
        with db.connection.cursor() as cursor:
            # Comprovar si existeix la taula
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'qualitat' 
                    AND table_name = 'mesures_hoytom'
                )
            """)
            exists_qualitat = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'mesureshoytom'
                )
            """)
            exists_public = cursor.fetchone()[0]
            
            print(f"\n✓ Taula en schema 'qualitat.mesures_hoytom': {exists_qualitat}")
            print(f"✓ Taula en schema 'public.mesureshoytom': {exists_public}")
            
            # Analitzar l'estructura
            if exists_public:
                print("\n--- Estructura de public.mesureshoytom ---")
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = 'mesureshoytom'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                
                print(f"\nColumnes trobades ({len(columns)}):")
                for col_name, data_type, nullable in columns:
                    print(f"  - {col_name:30} {data_type:20} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                
                # Comptar registres
                cursor.execute("SELECT COUNT(*) FROM public.mesureshoytom")
                count = cursor.fetchone()[0]
                print(f"\n✓ Total registres: {count:,}")
                
                # Mostrar exemples
                if count > 0:
                    cursor.execute("""
                        SELECT * FROM public.mesureshoytom LIMIT 3
                    """)
                    samples = cursor.fetchall()
                    
                    print("\n--- Exemples de dades ---")
                    for i, row in enumerate(samples, 1):
                        print(f"\nRegistre {i}:")
                        for j, col_name in enumerate([col[0] for col in columns]):
                            print(f"  {col_name}: {row[j]}")
                
                # Analitzar clients
                cursor.execute("""
                    SELECT DISTINCT client, COUNT(*) as count
                    FROM public.mesureshoytom
                    WHERE client IS NOT NULL
                    GROUP BY client
                    ORDER BY count DESC
                    LIMIT 10
                """)
                clients = cursor.fetchall()
                
                if clients:
                    print(f"\n--- Top 10 clients ({len(clients)} únics) ---")
                    for client, count in clients:
                        print(f"  {client}: {count:,} registres")
                else:
                    print("\n⚠️  No hi ha columna 'client' o està buida")
            
            if exists_qualitat:
                print("\n--- Estructura de qualitat.mesures_hoytom ---")
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'qualitat' 
                    AND table_name = 'mesures_hoytom'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                
                print(f"\nColumnes trobades ({len(columns)}):")
                for col_name, data_type, nullable in columns:
                    print(f"  - {col_name:30} {data_type:20} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                
                cursor.execute("SELECT COUNT(*) FROM qualitat.mesures_hoytom")
                count = cursor.fetchone()[0]
                print(f"\n✓ Total registres: {count:,}")
        
        service.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def analyze_torsio_structure():
    """Analitza l'estructura de la taula Torsió"""
    print("\n" + "="*80)
    print("ANÀLISI TAULA TORSIÓ")
    print("="*80)
    
    service = MeasurementHistoryService()
    db = service.db_connection
    
    try:
        with db.connection.cursor() as cursor:
            # Comprovar si existeix la taula
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'qualitat' 
                    AND table_name = 'mesures_torsio'
                )
            """)
            exists_qualitat = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'mesures_torsio'
                )
            """)
            exists_public = cursor.fetchone()[0]
            
            print(f"\n✓ Taula en schema 'qualitat.mesures_torsio': {exists_qualitat}")
            print(f"✓ Taula en schema 'public.mesures_torsio': {exists_public}")
            
            # Analitzar l'estructura
            if exists_public:
                print("\n--- Estructura de public.mesures_torsio ---")
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = 'mesures_torsio'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                
                print(f"\nColumnes trobades ({len(columns)}):")
                for col_name, data_type, nullable in columns:
                    print(f"  - {col_name:30} {data_type:20} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                
                # Comptar registres
                cursor.execute("SELECT COUNT(*) FROM public.mesures_torsio")
                count = cursor.fetchone()[0]
                print(f"\n✓ Total registres: {count:,}")
                
                # Mostrar exemples
                if count > 0:
                    cursor.execute("""
                        SELECT * FROM public.mesures_torsio LIMIT 3
                    """)
                    samples = cursor.fetchall()
                    
                    print("\n--- Exemples de dades ---")
                    for i, row in enumerate(samples, 1):
                        print(f"\nRegistre {i}:")
                        for j, col_name in enumerate([col[0] for col in columns]):
                            print(f"  {col_name}: {row[j]}")
                
                # Analitzar clients
                cursor.execute("""
                    SELECT DISTINCT client, COUNT(*) as count
                    FROM public.mesures_torsio
                    WHERE client IS NOT NULL
                    GROUP BY client
                    ORDER BY count DESC
                    LIMIT 10
                """)
                clients = cursor.fetchall()
                
                if clients:
                    print(f"\n--- Top 10 clients ({len(clients)} únics) ---")
                    for client, count in clients:
                        print(f"  {client}: {count:,} registres")
                else:
                    print("\n⚠️  No hi ha columna 'client' o està buida")
            
            if exists_qualitat:
                print("\n--- Estructura de qualitat.mesures_torsio ---")
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'qualitat' 
                    AND table_name = 'mesures_torsio'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                
                print(f"\nColumnes trobades ({len(columns)}):")
                for col_name, data_type, nullable in columns:
                    print(f"  - {col_name:30} {data_type:20} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                
                cursor.execute("SELECT COUNT(*) FROM qualitat.mesures_torsio")
                count = cursor.fetchone()[0]
                print(f"\n✓ Total registres: {count:,}")
        
        service.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Executar anàlisi de totes les màquines"""
    analyze_hoytom_structure()
    analyze_torsio_structure()
    
    print("\n" + "="*80)
    print("ANÀLISI COMPLETADA")
    print("="*80)


if __name__ == "__main__":
    main()
