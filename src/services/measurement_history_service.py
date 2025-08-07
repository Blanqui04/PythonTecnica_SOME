# src/services/measurement_history_service.py

import logging
import json
import os
from typing import List, Dict, Any, Optional
from src.database.database_connection import PostgresConn

logger = logging.getLogger(__name__)

class MeasurementHistoryService:
    """Servei per obtenir l'historial de mesures de la base de dades"""
    
    def __init__(self):
        """Inicialitza el servei amb la configuració de la base de dades"""
        self.db_connection = None
        self._load_db_config()
    
    def _load_db_config(self):
        """Carrega la configuració de la base de dades"""
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", "config", "database", "db_config.json"
            )
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Utilitza la configuració per defecte (primera entrada)
            db_config = list(config.values())[0]
            
            self.db_connection = PostgresConn(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port']
            )
            
            logger.info("Configuració de base de dades carregada correctament")
            
        except Exception as e:
            logger.error(f"Error carregant configuració de base de dades: {e}")
            raise
    
    def get_measurement_history(self, client: str, project_reference: str, limit: int = 10, batch_lot: str = None) -> List[Dict[str, Any]]:
        """
        Obté l'historial de mesures per un client i projecte
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte
            limit: Límit de registres a retornar
            batch_lot: Batch/lot específic (opcional)
            
        Returns:
            Llista de diccionaris amb les mesures
        """
        try:
            if batch_lot:
                query = """
                    SELECT DISTINCT element, pieza, datum, property
                    FROM mesuresqualitat 
                    WHERE client = %s AND id_referencia_client = %s AND id_lot = %s
                    ORDER BY element, pieza, datum, property
                    LIMIT %s
                """
                results = self.db_connection.fetchall(query, (client, project_reference, batch_lot, limit))
            else:
                query = """
                    SELECT DISTINCT element, pieza, datum, property
                    FROM mesuresqualitat 
                    WHERE client = %s AND id_referencia_client = %s
                    ORDER BY element, pieza, datum, property
                    LIMIT %s
                """
                results = self.db_connection.fetchall(query, (client, project_reference, limit))
            
            measurements = []
            for row in results:
                measurements.append({
                    'element': row[0],
                    'pieza': row[1],
                    'datum': row[2],
                    'property': row[3]
                })
            
            batch_info = f" per batch {batch_lot}" if batch_lot else ""
            logger.info(f"Trobats {len(measurements)} elements per {client} - {project_reference}{batch_info}")
            return measurements
            
        except Exception as e:
            logger.error(f"Error obtenint historial de mesures: {e}")
            raise
    
    def get_available_elements(self, client: str, project_reference: str, batch_lot: str = None) -> List[Dict[str, Any]]:
        """
        Obté tots els elements disponibles per un client i projecte
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte
            batch_lot: Batch/lot específic (opcional)
            
        Returns:
            Llista de diccionaris amb els elements disponibles
        """
        try:
            if batch_lot:
                query = """
                    SELECT DISTINCT 
                        COALESCE(element, 'None') as element,
                        COALESCE(pieza, 'None') as pieza, 
                        COALESCE(datum, 'None') as datum,
                        COALESCE(property, 'None') as property,
                        COUNT(*) as count
                    FROM mesuresqualitat 
                    WHERE client = %s AND id_referencia_client = %s AND id_lot = %s
                    GROUP BY element, pieza, datum, property
                    ORDER BY element, pieza, datum, property
                """
                results = self.db_connection.fetchall(query, (client, project_reference, batch_lot))
            else:
                query = """
                    SELECT DISTINCT 
                        COALESCE(element, 'None') as element,
                        COALESCE(pieza, 'None') as pieza, 
                        COALESCE(datum, 'None') as datum,
                        COALESCE(property, 'None') as property,
                        COUNT(*) as count
                    FROM mesuresqualitat 
                    WHERE client = %s AND id_referencia_client = %s
                    GROUP BY element, pieza, datum, property
                    ORDER BY element, pieza, datum, property
                """
                results = self.db_connection.fetchall(query, (client, project_reference))
            
            elements = []
            for row in results:
                elements.append({
                    'element': row[0],
                    'pieza': row[1], 
                    'datum': row[2],
                    'property': row[3],
                    'count': row[4]
                })
            
            batch_info = f" per batch {batch_lot}" if batch_lot else ""
            logger.info(f"Trobats {len(elements)} elements disponibles per {client} - {project_reference}{batch_info}")
            return elements
            
        except Exception as e:
            logger.error(f"Error obtenint elements disponibles: {e}")
            raise
    
    def get_element_measurement_history(self, client: str, project_reference: str, element_id: str, limit: int = 10, batch_lot: str = None) -> List[Dict[str, Any]]:
        """
        Obté l'historial de mesures per un element específic
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte
            element_id: ID de l'element (format: element|pieza|datum|property)
            limit: Límit de registres a retornar
            batch_lot: Batch/lot específic (opcional)
            
        Returns:
            Llista de diccionaris amb les mesures de l'element
        """
        try:
            # Parsejar l'element_id
            parts = element_id.split('|')
            if len(parts) != 4:
                raise ValueError(f"Format d'element_id incorrecte: {element_id}")
            
            element, pieza, datum, property_name = parts
            
            # Construir la consulta tenint en compte els valors NULL
            base_conditions = "client = %s AND id_referencia_client = %s"
            element_conditions = []
            params = [client, project_reference]
            
            if batch_lot:
                base_conditions += " AND id_lot = %s"
                params.append(batch_lot)
            
            # Afegir condicions per element, pieza, datum, property considerant NULL
            if element is None or element == 'None':
                element_conditions.append("element IS NULL")
            else:
                element_conditions.append("element = %s")
                params.append(element)
                
            if pieza is None or pieza == 'None':
                element_conditions.append("pieza IS NULL")
            else:
                element_conditions.append("pieza = %s")
                params.append(pieza)
                
            if datum is None or datum == 'None':
                element_conditions.append("datum IS NULL")
            else:
                element_conditions.append("datum = %s")
                params.append(datum)
                
            if property_name is None or property_name == 'None':
                element_conditions.append("property IS NULL")
            else:
                element_conditions.append("property = %s")
                params.append(property_name)
            
            all_conditions = base_conditions + " AND " + " AND ".join(element_conditions)
            params.append(limit)
            
            query = f"""
                SELECT actual, data_hora, id_lot, cavitat, nominal, tolerancia_negativa, tolerancia_positiva
                FROM mesuresqualitat 
                WHERE {all_conditions}
                ORDER BY data_hora DESC
                LIMIT %s
            """
            
            results = self.db_connection.fetchall(query, tuple(params))
            
            measurements = []
            for row in results:
                measurements.append({
                    'valor_mesura': row[0],  # actual from database
                    'data_hora': row[1],
                    'id_lot': row[2],
                    'cavitat': row[3],
                    'nominal': row[4] if row[4] is not None else 0.0,
                    'tol_neg': abs(row[5]) if row[5] is not None else 0.0,  # tolerancia_negativa (make positive)
                    'tol_pos': row[6] if row[6] is not None else 0.0,       # tolerancia_positiva
                    'element': element,
                    'pieza': pieza,
                    'datum': datum,
                    'property': property_name
                })
            
            batch_info = f" per batch {batch_lot}" if batch_lot else ""
            logger.info(f"Trobades {len(measurements)} mesures per element {element_id}{batch_info}")
            return measurements
            
        except Exception as e:
            logger.error(f"Error obtenint historial per element {element_id}: {e}")
            raise
    
    def get_available_lots(self, client: str, project_reference: str) -> List[Dict[str, Any]]:
        """
        Obté tots els lots disponibles per un client i projecte
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte
            
        Returns:
            Llista de diccionaris amb els lots disponibles
        """
        try:
            query = """
                SELECT DISTINCT id_lot, COUNT(*) as count, 
                       MIN(data_hora) as first_measurement, 
                       MAX(data_hora) as last_measurement
                FROM mesuresqualitat 
                WHERE client = %s AND id_referencia_client = %s AND id_lot IS NOT NULL
                GROUP BY id_lot
                ORDER BY last_measurement DESC
            """
            
            results = self.db_connection.fetchall(query, (client, project_reference))
            
            lots = []
            for row in results:
                lots.append({
                    'id_lot': row[0],
                    'count': row[1],
                    'first_measurement': row[2],
                    'last_measurement': row[3]
                })
            
            logger.info(f"Trobats {len(lots)} lots disponibles per {client} - {project_reference}")
            return lots
            
        except Exception as e:
            logger.error(f"Error obtenint lots disponibles: {e}")
            raise
    
    def close(self):
        """Tanca la connexió amb la base de dades"""
        if self.db_connection:
            self.db_connection.close()
            logger.debug("Connexió amb la base de dades tancada")
