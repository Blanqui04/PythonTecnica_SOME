#!/usr/bin/env python3
"""
Test de cerca a Hoytom amb referències
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.measurement_history_service import MeasurementHistoryService


def test_hoytom_search():
    """Test cerca amb Hoytom"""
    
    print("\n" + "="*80)
    print("TEST CERCA AMB HOYTOM")
    print("="*80)
    
    # Obtenir referències disponibles a Hoytom
    print("\n--- Obtenint referències a Hoytom ---")
    
    service = MeasurementHistoryService(machine='hoytom')
    db = service.db_connection
    
    try:
        with db.connection.cursor() as cursor:
            # Obtenir referències més comunes
            cursor.execute("""
                SELECT ref_some, ref_client, COUNT(*) as count
                FROM public.mesureshoytom
                WHERE ref_some IS NOT NULL
                GROUP BY ref_some, ref_client
                ORDER BY count DESC
                LIMIT 10
            """)
            references = cursor.fetchall()
            
            print(f"\nTop 10 referències:")
            for ref_some, ref_client, count in references:
                print(f"  {ref_some} (client: {ref_client}): {count} registres")
            
            # Provar cerca amb primera referència
            if references:
                test_ref = references[0][0]
                print(f"\n--- Test cerca amb referència: {test_ref} ---")
                
                # Comptar registres amb aquesta referència
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM public.mesureshoytom
                    WHERE UPPER(ref_some) LIKE UPPER(%s)
                """, (f'%{test_ref}%',))
                
                count = cursor.fetchone()[0]
                print(f"✓ Registres trobats: {count}")
                
                # Obtenir tipus d'assaigs
                cursor.execute("""
                    SELECT DISTINCT tipo_ensayo, COUNT(*) as count
                    FROM public.mesureshoytom
                    WHERE UPPER(ref_some) LIKE UPPER(%s)
                    GROUP BY tipo_ensayo
                    ORDER BY count DESC
                """, (f'%{test_ref}%',))
                
                tipos = cursor.fetchall()
                print(f"\n✓ Tipus d'assaigs:")
                for tipo, count in tipos:
                    print(f"  - {tipo}: {count} assaigs")
                
                # Obtenir mostres
                cursor.execute("""
                    SELECT ensayo, ref_some, tipo_ensayo, fuerza_maxima_fm, fecha_ensayo
                    FROM public.mesureshoytom
                    WHERE UPPER(ref_some) LIKE UPPER(%s)
                    LIMIT 5
                """, (f'%{test_ref}%',))
                
                samples = cursor.fetchall()
                print(f"\n✓ Mostres (primers 5):")
                for ensayo, ref, tipo, fuerza, fecha in samples:
                    print(f"  Assaig {ensayo}: {tipo} - Força: {fuerza} N - Data: {fecha}")
        
        service.close()
        print("\n✅ Test completat correctament")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_hoytom_vs_gompc():
    """Comparativa Hoytom vs GOMPC"""
    
    print("\n" + "="*80)
    print("COMPARATIVA HOYTOM VS GOMPC")
    print("="*80)
    
    machines = ['hoytom', 'gompc_projectes']
    
    for machine in machines:
        print(f"\n--- Màquina: {machine} ---")
        
        service = MeasurementHistoryService(machine=machine)
        print(f"  Nom: {service.get_current_machine()}")
        print(f"  Taules: {', '.join(service.measurement_tables)}")
        
        db = service.db_connection
        
        try:
            with db.connection.cursor() as cursor:
                # Comptar registres totals
                table = service.measurement_tables[0]
                schema = 'public' if machine == 'hoytom' else service.schema
                
                cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                count = cursor.fetchone()[0]
                print(f"  Total registres: {count:,}")
                
                # Mostrar estructura diferent
                if machine == 'hoytom':
                    cursor.execute("""
                        SELECT DISTINCT tipo_ensayo 
                        FROM public.mesureshoytom 
                        WHERE tipo_ensayo IS NOT NULL
                        LIMIT 10
                    """)
                    tipos = cursor.fetchall()
                    print(f"  Tipus d'assaigs: {len(tipos)}")
                    for (tipo,) in tipos[:5]:
                        print(f"    - {tipo}")
                else:
                    cursor.execute(f"""
                        SELECT DISTINCT client 
                        FROM {schema}.{table}
                        WHERE client IS NOT NULL
                        LIMIT 10
                    """)
                    clients = cursor.fetchall()
                    print(f"  Clients: {len(clients)}")
                    for (client,) in clients[:5]:
                        print(f"    - {client}")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        finally:
            service.close()
    
    print("\n✅ Comparativa completada")


if __name__ == "__main__":
    test_hoytom_search()
    test_hoytom_vs_gompc()
