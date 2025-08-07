#!/usr/bin/env python3
"""
Script per investigar les dades de la base de dades
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.measurement_history_service import MeasurementHistoryService

def investigate_database():
    """Investigar el contingut de la base de dades"""
    try:
        print("=== INVESTIGACIÓ BASE DE DADES ===")
        
        service = MeasurementHistoryService()
        
        # Consulta directa per veure l'estructura
        query = """
        SELECT element, pieza, datum, property, COUNT(*) as count,
               MAX(data_hora) as latest_date,
               COUNT(CASE WHEN actual IS NOT NULL THEN 1 END) as actual_count,
               COUNT(CASE WHEN nominal IS NOT NULL THEN 1 END) as nominal_count
        FROM mesuresqualitat 
        WHERE client = %s AND id_referencia_client = %s
        GROUP BY element, pieza, datum, property
        ORDER BY count DESC
        LIMIT 10
        """
        
        results = service.db_connection.fetchall(query, ("ZF", "A027Y915"))
        
        print("Top 10 elements amb més mesures:")
        print("Element | Pieza | Datum | Property | Count | Latest Date | Actual Count | Nominal Count")
        print("-" * 100)
        
        for row in results:
            element, pieza, datum, property_name, count, latest_date, actual_count, nominal_count = row
            print(f"{element} | {pieza} | {datum} | {property_name} | {count} | {latest_date} | {actual_count} | {nominal_count}")
        
        # Provar amb un element que té dades
        if results:
            first = results[0]
            element_id = f"{first[0]}|{first[1]}|{first[2]}|{first[3]}"
            print(f"\nProvant element amb més dades: {element_id}")
            
            # Consulta directa per veure les dades
            detail_query = """
            SELECT actual, nominal, tolerancia_negativa, tolerancia_positiva, data_hora, cavitat
            FROM mesuresqualitat 
            WHERE client = %s AND id_referencia_client = %s
            AND element = %s AND pieza = %s AND datum = %s AND property = %s
            ORDER BY data_hora DESC
            LIMIT 3
            """
            
            detail_results = service.db_connection.fetchall(detail_query, 
                ("ZF", "A027Y915", first[0], first[1], first[2], first[3]))
            
            print("Primeres 3 mesures:")
            for i, row in enumerate(detail_results):
                actual, nominal, tol_neg, tol_pos, data_hora, cavitat = row
                print(f"  {i+1}. Actual: {actual}, Nominal: {nominal}, Tol: {tol_neg}/{tol_pos}, Data: {data_hora}, Cavitat: {cavitat}")
            
            # Provar amb el servei
            print("\nProvant amb el servei get_element_measurement_history:")
            measurements = service.get_element_measurement_history("ZF", "A027Y915", element_id, limit=3)
            print(f"Mesures obtingudes: {len(measurements)}")
            
            for i, measurement in enumerate(measurements):
                print(f"  {i+1}. {measurement}")
        
        service.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_database()
