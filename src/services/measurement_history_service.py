# src/services/measurement_history_service.py

import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from src.database.quality_measurement_adapter import QualityMeasurementDBAdapter
import json
import os

logger = logging.getLogger(__name__)

class MeasurementHistoryService:
    """Servei per obtenir l'historial de mesures de la base de dades"""
    
    def __init__(self, db_config=None):
        """Inicialitza el servei amb la configuració de la base de dades"""
        self.db_adapter = None
        self._init_database_connection(db_config)
    
    def _init_database_connection(self, db_config=None):
        """Inicialitza la connexió a la base de dades"""
        try:
            if db_config:
                # Usar configuració passada com a paràmetre
                self.db_adapter = QualityMeasurementDBAdapter(db_config)
            else:
                # Cargar configuració de la base de dades des del fitxer
                config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'database', 'db_config.json')
                
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    
                    self.db_adapter = QualityMeasurementDBAdapter(config['primary'])
                else:
                    logger.error(f"No s'ha trobat el fitxer de configuració: {config_path}")
                    return
                    return
            
            if self.db_adapter.connect():
                logger.info("Connexió a la base de dades establerta correctament")
            else:
                logger.error("No s'ha pogut establir la connexió a la base de dades")
                self.db_adapter = None
                
        except Exception as e:
            logger.error(f"Error inicialitzant la connexió a la base de dades: {e}")
            self.db_adapter = None
    
    def get_measurement_history(self, client: str, project_reference: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obté l'historial de mesures per un client i referència de projecte
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte (id_referencia_client)
            limit: Número màxim d'entrades a retornar per element (per defecte 10)
        
        Returns:
            List[Dict]: Llista d'elements amb les seves mesures més recents
        """
        if not self.db_adapter:
            logger.error("No hi ha connexió a la base de dades disponible")
            return []
        
        try:
            # Query simplificada per obtenir les últimes mesures per cada element
            # Accepta elements amb valors 'nan' i els gestiona
            query = """
            WITH ranked_measurements AS (
                SELECT 
                    element,
                    nominal,
                    actual,
                    tolerancia_negativa,
                    tolerancia_positiva,
                    data_hora,
                    id_lot,
                    cavitat,
                    ROW_NUMBER() OVER (
                        PARTITION BY element 
                        ORDER BY data_hora DESC, created_at DESC
                    ) as rn
                FROM mesuresqualitat 
                WHERE client = %s 
                    AND id_referencia_client = %s
                    AND element IS NOT NULL
                    AND element != ''
            )
            SELECT 
                element,
                nominal,
                actual,
                tolerancia_negativa,
                tolerancia_positiva,
                data_hora,
                id_lot,
                cavitat
            FROM ranked_measurements 
            WHERE rn <= %s
            ORDER BY element, rn
            """
            
            # Executar la query
            logger.info(f"Executant query amb paràmetres: client='{client}', project_reference='{project_reference}', limit={limit}")
            results = self.db_adapter.execute_query(query, (client, project_reference, limit))
            
            # Verificar si results és una llista (SELECT amb resultats) o un int (no resultats)
            if not isinstance(results, list):
                logger.info(f"Query no ha retornat resultats SELECT: {type(results)}")
                return []
            
            logger.info(f"Query retornada: {len(results)} files")
            
            if not results:
                logger.info(f"No s'han trobat mesures per Client: {client}, Projecte: {project_reference}")
                return []
            
            # Convertir resultats a format d'elements
            elements_dict = {}
            
            for row in results:
                element_name = row[0]
                if element_name not in elements_dict:
                    # Gestió de valors nan - convertir a valors per defecte realistes
                    raw_nominal = row[1]
                    raw_tol_minus = row[3]
                    raw_tol_plus = row[4]
                    raw_actual = row[2]
                    
                    # Si són 'nan' o None, usar valors per defecte
                    if raw_nominal is None or str(raw_nominal).lower() == 'nan':
                        nominal = 0.0
                    else:
                        nominal = float(raw_nominal)
                    
                    if raw_tol_minus is None or str(raw_tol_minus).lower() == 'nan':
                        tol_minus = -0.1  # Tolerància per defecte
                    else:
                        tol_minus = float(raw_tol_minus)
                    
                    if raw_tol_plus is None or str(raw_tol_plus).lower() == 'nan':
                        tol_plus = 0.1  # Tolerància per defecte
                    else:
                        tol_plus = float(raw_tol_plus)
                    
                    elements_dict[element_name] = {
                        'element_id': element_name,
                        'nominal': nominal,
                        'tolerance_minus': tol_minus,
                        'tolerance_plus': tol_plus,
                        'measurements': [],
                        'cavity': row[7] if row[7] is not None else '',
                        'batch': row[6] if row[6] is not None else '',
                        'last_measured': row[5] if row[5] is not None else None
                    }
                
                # Afegir mesura si existeix
                raw_actual = row[2]
                if raw_actual is not None and str(raw_actual).lower() != 'nan':
                    try:
                        elements_dict[element_name]['measurements'].append(float(raw_actual))
                    except (ValueError, TypeError):
                        # Si no es pot convertir, usar el valor nominal
                        elements_dict[element_name]['measurements'].append(
                            elements_dict[element_name]['nominal']
                        )
            
            # Convertir a llista i assegurar-se que cada element té exactament 10 mesures
            elements_list = []
            for element_data in elements_dict.values():
                measurements = element_data['measurements']
                nominal = element_data['nominal']
                
                # Si tenim menys de 10 mesures, completar amb el valor nominal
                if len(measurements) < limit:
                    measurements.extend([nominal] * (limit - len(measurements)))
                    logger.info(f"Element {element_data['element_id']}: Completant amb {limit - len(element_data['measurements'])} valors nominals")
                
                # Si tenim més de 10 mesures, prendre només les primeres 10
                element_data['measurements'] = measurements[:limit]
                elements_list.append(element_data)
            
            logger.info(f"S'han trobat {len(elements_list)} elements únics amb mesures per Client: {client}, Projecte: {project_reference}")
            
            return elements_list
            
        except Exception as e:
            logger.error(f"Error obtenint historial de mesures: {e}")
            return []
    
    def get_elements_by_client_and_project(self, client: str, project_reference: str) -> List[str]:
        """
        Obté la llista d'elements únics per un client i referència de projecte
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte
            
        Returns:
            List[str]: Llista d'elements únics
        """
        if not self.db_adapter:
            logger.error("No hi ha connexió a la base de dades disponible")
            return []
        
        try:
            query = """
            SELECT DISTINCT element
            FROM mesuresqualitat 
            WHERE client = %s 
                AND id_referencia_client = %s
                AND element IS NOT NULL
            ORDER BY element
            """
            
            results = self.db_adapter.execute_query(query, (client, project_reference))
            
            elements = [row[0] for row in results if row[0]]
            
            logger.info(f"S'han trobat {len(elements)} elements únics per Client: {client}, Projecte: {project_reference}")
            
            return elements
            
        except Exception as e:
            logger.error(f"Error obtenint elements: {e}")
            return []
    
    def get_measurement_statistics(self, client: str, project_reference: str) -> Dict[str, Any]:
        """
        Obté estadístiques generals de les mesures
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte
            
        Returns:
            Dict: Estadístiques de les mesures
        """
        if not self.db_adapter:
            return {}
        
        try:
            query = """
            SELECT 
                COUNT(*) as total_measurements,
                COUNT(DISTINCT element) as unique_elements,
                COUNT(DISTINCT id_lot) as unique_lots,
                MIN(data_hora) as first_measurement,
                MAX(data_hora) as last_measurement
            FROM mesuresqualitat 
            WHERE client = %s 
                AND id_referencia_client = %s
                AND element IS NOT NULL
            """
            
            result = self.db_adapter.execute_query(query, (client, project_reference))
            
            if result and result[0]:
                row = result[0]
                return {
                    'total_measurements': row[0],
                    'unique_elements': row[1],
                    'unique_lots': row[2],
                    'first_measurement': row[3],
                    'last_measurement': row[4]
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error obtenint estadístiques: {e}")
            return {}
    
    def get_element_measurement_history(self, client: str, project_reference: str, element_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obté l'historial de mesures per un element específic
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte (id_referencia_client)
            element_id: ID de l'element específic
            limit: Número màxim d'entrades a retornar (per defecte 10)
            
        Returns:
            List[Dict]: Llista de mesures per l'element específic
        """
        if not self.db_adapter:
            logger.error("No hi ha connexió a la base de dades")
            return []
        
        try:
            # Query per obtenir les últimes mesures d'un element específic
            query = '''
            SELECT 
                element,
                nominal,
                actual,
                tolerancia_negativa as tol_neg,
                tolerancia_positiva as tol_pos,
                data_hora,
                id_lot,
                cavitat,
                maquina,
                desviacio,
                check_value,
                ok
            FROM mesuresqualitat 
            WHERE client = %s 
              AND id_referencia_client = %s 
              AND element = %s
              AND element IS NOT NULL 
              AND element != ''
            ORDER BY data_hora DESC
            LIMIT %s
            '''
            
            logger.info(f"Cercant històrial per element: {element_id} (Client: {client}, Projecte: {project_reference})")
            results = self.db_adapter.execute_query(query, (client, project_reference, element_id, limit))
            
            if not isinstance(results, list):
                logger.info(f"Query no ha retornat resultats SELECT: {type(results)}")
                return []
            
            logger.info(f"Query retornada: {len(results)} files per element {element_id}")
            
            if not results:
                logger.info(f"No s'han trobat mesures per Element: {element_id}")
                return []
            
            # Convertir resultats a format de mesures
            measurements = []
            
            for row in results:
                # Gestió de valors nan
                nominal = float(row[1]) if row[1] is not None and str(row[1]).lower() != 'nan' else 0.0
                actual = float(row[2]) if row[2] is not None and str(row[2]).lower() != 'nan' else 0.0
                tol_neg = float(row[3]) if row[3] is not None and str(row[3]).lower() != 'nan' else -0.1
                tol_pos = float(row[4]) if row[4] is not None and str(row[4]).lower() != 'nan' else 0.1
                
                measurement = {
                    'element': row[0],
                    'nominal': nominal,
                    'actual': actual,
                    'tol_neg': tol_neg,
                    'tol_pos': tol_pos,
                    'data_hora': row[5],
                    'id_lot': row[6] if row[6] is not None else '',
                    'cavitat': row[7] if row[7] is not None else '',
                    'maquina': row[8] if row[8] is not None else '',
                    'desviacio': float(row[9]) if row[9] is not None and str(row[9]).lower() != 'nan' else 0.0,
                    'check_value': row[10] if row[10] is not None else '',
                    'ok': row[11] if row[11] is not None else True
                }
                
                measurements.append(measurement)
            
            logger.info(f"Retornant {len(measurements)} mesures per element {element_id}")
            return measurements
            
        except Exception as e:
            logger.error(f"Error obtenint històrial d'element {element_id}: {e}")
            return []
    
    def get_available_elements(self, client: str, project_reference: str) -> List[Dict[str, Any]]:
        """
        Obté la llista d'elements disponibles per un client i referència de projecte
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte (id_referencia_client)
            
        Returns:
            List[Dict]: Llista d'elements disponibles amb el compte de mesures
        """
        if not self.db_adapter:
            logger.error("No hi ha connexió a la base de dades")
            return []
        
        try:
            # Query per obtenir elements únics amb compte de mesures
            query = '''
            SELECT 
                element,
                COUNT(*) as measurement_count,
                MAX(data_hora) as last_measurement,
                MIN(data_hora) as first_measurement
            FROM mesuresqualitat 
            WHERE client = %s 
              AND id_referencia_client = %s
              AND element IS NOT NULL 
              AND element != ''
            GROUP BY element
            ORDER BY COUNT(*) DESC, element ASC
            '''
            
            logger.info(f"Cercant elements disponibles per Client: {client}, Projecte: {project_reference}")
            results = self.db_adapter.execute_query(query, (client, project_reference))
            
            if not isinstance(results, list):
                logger.info(f"Query no ha retornat resultats SELECT: {type(results)}")
                return []
            
            logger.info(f"Query retornada: {len(results)} elements únics")
            
            if not results:
                logger.info(f"No s'han trobat elements per Client: {client}, Projecte: {project_reference}")
                return []
            
            # Convertir resultats a format d'elements
            elements = []
            
            for row in results:
                element = {
                    'element': row[0],
                    'count': row[1],
                    'last_measurement': row[2],
                    'first_measurement': row[3]
                }
                elements.append(element)
            
            logger.info(f"Retornant {len(elements)} elements disponibles")
            return elements
            
        except Exception as e:
            logger.error(f"Error obtenint elements disponibles: {e}")
            return []
    
    def close(self):
        """Tanca la connexió a la base de dades"""
        if self.db_adapter:
            self.db_adapter.close()
