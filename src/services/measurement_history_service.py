# src/services/measurement_history_service.py

import logging
import json
import os
from typing import List, Dict, Any, Optional
from src.database.database_connection import PostgresConn

logger = logging.getLogger(__name__)

# Constants per les noves taules de mesures
# Només les taules compatibles amb estudis de capacitat (amb element, pieza, datum, property)
# NOTA: Utilitzem schema 'qualitat' que s'alimenta automàticament des d'Airflow
# Si no existeix, fem fallback a 'public'
MEASUREMENT_SCHEMA = 'qualitat'
FALLBACK_SCHEMA = 'public'

# Definició de màquines i les seves taules
MACHINE_TABLES = {
    'gompc_projectes': {
        'name': 'GOMPC Projectes',
        'tables': ['mesures_gompc_projectes'],
        'description': 'Mesures dimensionals de projectes (GOMPC)'
    },
    'gompc_nou': {
        'name': 'GOMPC Nou',
        'tables': ['mesures_gompcnou'],
        'description': 'Mesures dimensionals noves (GOMPCNOU)'
    },
    'all': {
        'name': 'Totes les màquines',
        'tables': ['mesures_gompc_projectes', 'mesures_gompcnou'],
        'description': 'Totes les màquines compatibles amb estudis de capacitat'
    }
}

# Taules per defecte (per compatibilitat amb codi existent)
MEASUREMENT_TABLES = MACHINE_TABLES['all']['tables']

# Taules amb altres estructures (no compatibles amb estudis de capacitat)
# - mesureshoytom: Assaigs de tracció (no té element/pieza/datum/property)
# - mesurestorsio: Assaigs de torsió (no té element/pieza/datum/property)

class MeasurementHistoryService:
    """Servei per obtenir l'historial de mesures de la base de dades"""
    
    def __init__(self, machine: str = 'all'):
        """
        Inicialitza el servei amb la configuració de la base de dades
        
        Args:
            machine: Tipus de màquina/taula a utilitzar. Opcions:
                    - 'gompc_projectes': Només GOMPC Projectes
                    - 'gompc_nou': Només GOMPC Nou
                    - 'all': Totes les màquines (per defecte)
        """
        self.db_connection = None
        self.machine = machine
        
        # Obtenir taules per la màquina seleccionada
        if machine in MACHINE_TABLES:
            self.measurement_tables = MACHINE_TABLES[machine]['tables']
            self.machine_name = MACHINE_TABLES[machine]['name']
            logger.info(f"Màquina seleccionada: {self.machine_name}")
        else:
            # Fallback a totes les taules
            self.measurement_tables = MEASUREMENT_TABLES
            self.machine_name = 'Totes les màquines'
            logger.warning(f"Màquina '{machine}' no reconeguda, usant totes les taules")
        
        self.schema = None  # Es detectarà automàticament
        self._load_db_config()
        self._detect_schema()
    
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
    
    def _detect_schema(self):
        """Detecta automàticament quin schema utilitzar (qualitat o public)"""
        try:
            conn = self.db_connection.connect()
            cursor = conn.cursor()
            
            # Verificar si existeix el schema 'qualitat' amb taules
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = ANY(%s)
            """, (MEASUREMENT_SCHEMA, MEASUREMENT_TABLES))
            
            count_qualitat = cursor.fetchone()[0]
            
            if count_qualitat > 0:
                self.schema = MEASUREMENT_SCHEMA
                logger.info(f"[OK] Utilitzant schema '{MEASUREMENT_SCHEMA}' (alimentat per Airflow ETL)")
            else:
                self.schema = FALLBACK_SCHEMA
                logger.info(f"[INFO] Schema '{MEASUREMENT_SCHEMA}' no disponible, utilitzant '{FALLBACK_SCHEMA}' (legacy)")
            
            cursor.close()
            
        except Exception as e:
            logger.warning(f"Error detectant schema, utilitzant fallback: {e}")
            self.schema = FALLBACK_SCHEMA
    
    def _convert_query_to_union(self, query_template: str, params: tuple) -> tuple:
        """
        Converteix un query amb 'FROM mesuresqualitat' a UNION ALL de totes les taules
        
        Args:
            query_template: Query original amb 'FROM mesuresqualitat'
            params: Paràmetres del query
            
        Returns:
            Tuple (query_modificat, params_multiplicats)
        """
        # Dividir el query en parts (abans i després de FROM mesuresqualitat)
        if 'FROM mesuresqualitat' not in query_template:
            # Si no té mesuresqualitat, retornar sense canvis
            return (query_template, params)
        
        # Reemplaçar mesuresqualitat per una taula genèrica amb àlies __TABLE__ t
        query_template = query_template.replace('FROM mesuresqualitat', 'FROM __TABLE__ t')
        
        # Construir UNION ALL amb schema detectat
        union_parts = []
        for table in self.measurement_tables:
            # Utilitzar schema.table
            full_table_name = f"{self.schema}.{table}"
            table_query = query_template.replace('__TABLE__', full_table_name)
            union_parts.append(f"({table_query})")
        
        final_query = " UNION ALL ".join(union_parts)
        
        # Multiplicar paràmetres per cada taula
        final_params = params * len(self.measurement_tables)
        
        return (final_query, final_params)
    
    def _build_union_query(self, select_clause: str, where_clause: str, order_clause: str = "", limit_clause: str = "") -> str:
        """
        Construeix un query amb UNION ALL per totes les taules de mesures
        
        Args:
            select_clause: Columnes a seleccionar (sense SELECT)
            where_clause: Condicions WHERE (sense WHERE)
            order_clause: Ordre (opcional, sense ORDER BY)
            limit_clause: Límit (opcional, sense LIMIT)
            
        Returns:
            Query complet amb UNION ALL
        """
        union_parts = []
        for table in self.measurement_tables:
            query_part = f"SELECT {select_clause} FROM {table}"
            if where_clause:
                query_part += f" WHERE {where_clause}"
            union_parts.append(f"({query_part})")
        
        full_query = " UNION ALL ".join(union_parts)
        
        if order_clause:
            full_query = f"SELECT * FROM ({full_query}) AS combined ORDER BY {order_clause}"
        
        if limit_clause:
            full_query += f" LIMIT {limit_clause}"
            
        return full_query
    
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
            select_clause = "DISTINCT element, pieza, datum, property"
            
            if batch_lot:
                where_clause = "client = %s AND id_referencia_client = %s AND UPPER(id_lot) LIKE UPPER(%s)"
                params = (client, project_reference, f'%{batch_lot}%')
            else:
                where_clause = "client = %s AND id_referencia_client = %s"
                params = (client, project_reference)
            
            order_clause = "element, pieza, datum, property"
            
            # Construir query amb UNION ALL de totes les taules
            query = self._build_union_query(
                select_clause=select_clause,
                where_clause=where_clause,
                order_clause=order_clause,
                limit_clause="%s"
            )
            
            # Repetir paràmetres per cada taula en el UNION
            all_params = params * len(self.measurement_tables) + (limit,)
            results = self.db_connection.fetchall(query, all_params)
            
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
    
    def get_element_measurements(self, client: str, project_reference: str, element_name: str, property_name: str = None, batch_lot: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obté mesures específiques per un element i propietat
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte  
            element_name: Nom de l'element
            property_name: Propietat de l'element (opcional)
            batch_lot: Batch/lot específic (opcional)
            limit: Límit de resultats
            
        Returns:
            Llista de mesures per l'element especificat
        """
        try:
            logger.info(f"🔍 Obtenint mesures per element='{element_name}', property='{property_name}'")
            
            # Utilitzar cerca universal flexible
            search_strategies = self._build_universal_search_conditions(client, project_reference)
            
            results = []
            
            for strategy in search_strategies:
                try:
                    # Handle special case for IN clauses  
                    if 'IN ({})' in strategy['ref_condition']:
                        ref_params = strategy['params'][1:]
                        placeholders = ','.join(['%s'] * len(ref_params))
                        ref_condition = strategy['ref_condition'].replace('{}', placeholders)
                    else:
                        ref_condition = strategy['ref_condition']
                    
                    # Build base conditions
                    conditions = [
                        strategy['client_condition'],
                        ref_condition,
                        "element = %s"
                    ]
                    params = strategy['params'] + [element_name]
                    
                    # Add property condition if specified
                    if property_name and property_name != 'N/A':
                        conditions.append("property = %s")
                        params.append(property_name)
                    
                    # Add batch lot condition if specified (CONTAINS matching)
                    if batch_lot:
                        conditions.append("UPPER(id_lot) LIKE UPPER(%s)")
                        params.append(f'%{batch_lot}%')
                    
                    # Build final WHERE clause
                    where_clause = " AND ".join(conditions)
                    
                    # Construir query amb UNION ALL de totes les taules
                    select_clause = """
                        id_referencia_client, element, pieza, datum, property, 
                        actual, nominal, tolerancia_negativa, tolerancia_positiva, 
                        desviacio, data_hora, id_lot, cavitat
                    """
                    
                    union_parts = []
                    for table in self.measurement_tables:
                        table_query = f"""
                            SELECT {select_clause}
                            FROM {table}
                            WHERE {where_clause}
                        """
                        union_parts.append(f"({table_query})")
                    
                    query = " UNION ALL ".join(union_parts)
                    query = f"SELECT * FROM ({query}) AS combined ORDER BY data_hora DESC LIMIT %s"
                    
                    # Repetir paràmetres per cada taula
                    all_params = params * len(self.measurement_tables) + [limit]
                    
                    results = self.db_connection.fetchall(query, all_params)
                    
                    if results:
                        logger.info(f"✅ Estratègia '{strategy['name']}' trobada: {len(results)} mesures per {element_name}")
                        break
                    else:
                        logger.debug(f"❌ Estratègia '{strategy['name']}': cap mesura per {element_name}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error en estratègia '{strategy['name']}': {e}")
                    continue
            
            measurements = []
            for row in results:
                measurements.append({
                    'id_referencia_client': row[0],
                    'element': row[1],
                    'pieza': row[2],
                    'datum': row[3],
                    'property': row[4],
                    'actual': float(row[5]) if row[5] is not None else None,
                    'nominal': float(row[6]) if row[6] is not None else None,
                    'tolerancia_negativa': float(row[7]) if row[7] is not None else None,
                    'tolerancia_positiva': float(row[8]) if row[8] is not None else None,
                    'desviacio': float(row[9]) if row[9] is not None else None,
                    'data_hora': row[10],
                    'id_lot': row[11],
                    'cavitat': row[12]
                })
                
            logger.info(f"✅ Trobades {len(measurements)} mesures per {element_name}")
            return measurements
            
        except Exception as e:
            logger.error(f"Error obtenint mesures de l'element: {e}")
            raise
    
    def get_available_elements(self, client: str, project_reference: str, batch_lot: str = None) -> List[Dict[str, Any]]:
        """
        Obté tots els elements disponibles per un client i projecte amb cerca flexible
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte
            batch_lot: Batch/lot específic (opcional)
            
        Returns:
            Llista de diccionaris amb els elements disponibles
        """
        try:
            logger.info(f"🔍 Buscant elements per client='{client}', project_reference='{project_reference}'")
            
            # Utilitzar el mètode universal per generar estratègies de cerca
            search_strategies = self._build_universal_search_conditions(client, project_reference)
            
            results = []
            
            for strategy in search_strategies:
                try:
                    # Handle special case for IN clauses
                    if 'IN ({})' in strategy['ref_condition']:
                        # Replace {} with correct number of placeholders
                        ref_params = strategy['params'][1:]  # Skip client param
                        placeholders = ','.join(['%s'] * len(ref_params))
                        ref_condition = strategy['ref_condition'].replace('{}', placeholders)
                    else:
                        ref_condition = strategy['ref_condition']
                    
                    if batch_lot:
                        query_template = f"""
                            SELECT DISTINCT 
                                COALESCE(element, 'N/A') as element,
                                COALESCE(pieza, 'N/A') as pieza, 
                                COALESCE(datum, 'N/A') as datum,
                                COALESCE(property, 'N/A') as property,
                                id_referencia_client,
                                COUNT(*) as count
                            FROM mesuresqualitat 
                            WHERE {strategy['client_condition']} 
                            AND {ref_condition} 
                            AND UPPER(id_lot) LIKE UPPER(%s)
                            GROUP BY element, pieza, datum, property, id_referencia_client
                        """
                        params = strategy['params'] + [f'%{batch_lot}%']
                        query, final_params = self._convert_query_to_union(query_template, tuple(params))
                        query = f"SELECT * FROM ({query}) AS combined ORDER BY element, pieza, datum, property"
                    else:
                        query_template = f"""
                            SELECT DISTINCT 
                                COALESCE(element, 'N/A') as element,
                                COALESCE(pieza, 'N/A') as pieza, 
                                COALESCE(datum, 'N/A') as datum,
                                COALESCE(property, 'N/A') as property,
                                id_referencia_client,
                                COUNT(*) as count
                            FROM mesuresqualitat 
                            WHERE {strategy['client_condition']} 
                            AND {ref_condition}
                            GROUP BY element, pieza, datum, property, id_referencia_client
                        """
                        params = strategy['params']
                        query, final_params = self._convert_query_to_union(query_template, tuple(params))
                        query = f"SELECT * FROM ({query}) AS combined ORDER BY element, pieza, datum, property"
                    
                    results = self.db_connection.fetchall(query, final_params)
                    
                    if results:
                        logger.info(f"✅ Estratègia '{strategy['name']}' trobada: {len(results)} elements")
                        # Show which reference was found
                        unique_refs = set([row[4] for row in results])
                        logger.info(f"   📁 Referències trobades: {list(unique_refs)}")
                        break
                    else:
                        logger.debug(f"❌ Estratègia '{strategy['name']}': cap resultat")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error en estratègia '{strategy['name']}': {e}")
                    continue
            
            elements = []
            for row in results:
                elements.append({
                    'element': row[0],
                    'pieza': row[1], 
                    'datum': row[2],
                    'property': row[3],
                    'ref_client': row[4],
                    'count': row[5]
                })
            
            batch_info = f" per batch {batch_lot}" if batch_lot else ""
            logger.info(f"Trobats {len(elements)} elements disponibles per {client} - {project_reference}{batch_info}")
            return elements
            
        except Exception as e:
            logger.error(f"Error obtenint elements disponibles: {e}")
            raise
    
    def _build_universal_search_conditions(self, client: str, project_reference: str):
        """
        Construeix condicions de cerca universals per qualsevol client i referència
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte
            
        Returns:
            Llista d'estratègies de cerca amb condicions SQL i paràmetres
        """
        
        # Generar variants de referència universals
        ref_variants = [
            project_reference,  # Original
            f"{project_reference}D",  # Sufig D (molt comú)
            f"{project_reference}_D",  # Sufig _D
            f"{project_reference}d",  # Sufig d minúscula
            project_reference.upper(),  # Majúscules
            project_reference.lower(),  # Minúscules
        ]
        
        # Si la referència és numèrica, afegir variants amb zeros i separadors
        if project_reference.replace('-', '').replace('_', '').isdigit():
            clean_ref = project_reference.replace('-', '').replace('_', '')
            ref_variants.extend([
                f"00{clean_ref}",  # Amb zeros al davant
                f"0{clean_ref}",   # Amb un zero al davant
                f"{clean_ref[:3]}_{clean_ref[3:]}_002" if len(clean_ref) >= 3 else f"{clean_ref}_002",  # Format _002
                f"{clean_ref[:3]}_{clean_ref[3:]}_001" if len(clean_ref) >= 3 else f"{clean_ref}_001",  # Format _001
                f"002_{clean_ref}_002",  # Format 002_xxx_002
            ])
        
        # Generar variants de client universals
        client_variants = [
            client,  # Original
            client.upper(),  # Majúscules
            client.lower(),  # Minúscules
            client.replace(' ', ''),  # Sense espais
            client.replace('-', ''),  # Sense guions
            client.replace('_', ''),  # Sense guions baixos
        ]
        
        # Construir estratègies de cerca
        strategies = []
        
        # 1. Cerca CONTAINS (flexible) amb variants principals
        main_ref_variants = ref_variants[:4]  # Les 4 més comunes
        main_client_variants = client_variants[:3]  # Les 3 més comunes
        
        for client_var in main_client_variants:
            for ref_var in main_ref_variants:
                strategies.append({
                    'name': f'Contains: {client_var[:10]} + {ref_var[:15]}',
                    'client_condition': 'UPPER(client) = UPPER(%s)',
                    'ref_condition': 'UPPER(id_referencia_client) LIKE UPPER(%s)',
                    'params': [client_var, f'%{ref_var}%'],  # CONTAINS matching
                    'priority': 1  # Alta prioritat
                })
        
        # 2. Cerca case-insensitive flexible
        strategies.append({
            'name': 'Case-insensitive + TRIM',
            'client_condition': 'UPPER(TRIM(client)) = UPPER(TRIM(%s))',
            'ref_condition': 'UPPER(TRIM(id_referencia_client)) IN ({})',
            'params': [client] + [ref.upper() for ref in main_ref_variants],
            'priority': 2
        })
        
        # 3. Cerca amb LIKE patterns
        like_patterns = [
            f"{project_reference}%",  # Comença amb
            f"%{project_reference}%",  # Conté
            f"%{project_reference}D",  # Acaba amb D
        ]
        
        for pattern in like_patterns:
            strategies.append({
                'name': f'LIKE: ...{pattern[-10:]}',
                'client_condition': 'UPPER(TRIM(client)) = UPPER(TRIM(%s))',
                'ref_condition': 'id_referencia_client LIKE %s',
                'params': [client, pattern],
                'priority': 3
            })
        
        # 4. Cerca fuzzy de client (menys prioritat)
        if len(client) > 3:  # Només per clients amb nom llarg
            client_patterns = [f"%{client}%", f"{client}%"]
            for pattern in client_patterns:
                strategies.append({
                    'name': f'Client fuzzy: {pattern[:15]}',
                    'client_condition': 'client LIKE %s',
                    'ref_condition': 'id_referencia_client = %s',
                    'params': [pattern, project_reference],
                    'priority': 4
                })
        
        # 5. Cerca a id_referencia_some (PRIORITAT ALTA - moltes dades aquí)
        # NOTA: id_referencia_some pot ser TEXT o INTEGER segons la taula, per això fem CAST
        for client_var in main_client_variants:
            for ref_var in main_ref_variants:
                strategies.append({
                    'name': f'id_referencia_some: {client_var[:10]} + {ref_var[:15]}',
                    'client_condition': 'UPPER(client) = UPPER(%s)',
                    'ref_condition': 'UPPER(CAST(id_referencia_some AS TEXT)) LIKE UPPER(%s)',
                    'params': [client_var, f'%{ref_var}%'],
                    'priority': 1  # Alta prioritat (mateix nivell que id_referencia_client)
                })
        
        # Ordenar per prioritat (menor número = més prioritat)
        strategies.sort(key=lambda x: x.get('priority', 5))
        
        return strategies
    
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
            base_conditions = "t.client = %s AND t.id_referencia_client = %s"
            element_conditions = []
            params = [client, project_reference]
            
            if batch_lot:
                base_conditions += " AND UPPER(t.id_lot) LIKE UPPER(%s)"
                params.append(f'%{batch_lot}%')
            
            # Afegir condicions per element, pieza, datum, property considerant NULL
            if element is None or element == 'None':
                element_conditions.append("t.element IS NULL")
            else:
                element_conditions.append("t.element = %s")
                params.append(element)
                
            if pieza is None or pieza == 'None':
                element_conditions.append("t.pieza IS NULL")
            else:
                element_conditions.append("t.pieza = %s")
                params.append(pieza)
                
            if datum is None or datum == 'None':
                element_conditions.append("t.datum IS NULL")
            else:
                element_conditions.append("t.datum = %s")
                params.append(datum)
                
            if property_name is None or property_name == 'None':
                element_conditions.append("t.property IS NULL")
            else:
                element_conditions.append("t.property = %s")
                params.append(property_name)
            
            all_conditions = base_conditions + " AND " + " AND ".join(element_conditions)
            
            query_template = f"""
                SELECT actual, data_hora, id_lot, cavitat, nominal, tolerancia_negativa, tolerancia_positiva
                FROM mesuresqualitat 
                WHERE {all_conditions}
            """
            
            # Convertir a UNION de totes les taules
            query, final_params = self._convert_query_to_union(query_template, tuple(params))
            query = f"SELECT * FROM ({query}) AS combined ORDER BY data_hora DESC LIMIT %s"
            final_params = final_params + (limit,)
            
            results = self.db_connection.fetchall(query, final_params)
            
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
            query_template = """
                SELECT DISTINCT id_lot, COUNT(*) as count, 
                       MIN(data_hora) as first_measurement, 
                       MAX(data_hora) as last_measurement
                FROM mesuresqualitat 
                WHERE client = %s AND id_referencia_client = %s AND id_lot IS NOT NULL
                GROUP BY id_lot
            """
            
            params = (client, project_reference)
            query, final_params = self._convert_query_to_union(query_template, params)
            query = f"SELECT * FROM ({query}) AS combined ORDER BY last_measurement DESC"
            
            results = self.db_connection.fetchall(query, final_params)
            
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
    
    @staticmethod
    def get_available_machines() -> Dict[str, Dict[str, str]]:
        """
        Retorna les màquines disponibles per estudis de capacitat
        
        Returns:
            Dict amb informació de cada màquina disponible
        """
        return MACHINE_TABLES
    
    def get_current_machine(self) -> str:
        """Retorna el nom de la màquina actual"""
        return self.machine_name
    
    def close(self):
        """Tanca la connexió amb la base de dades"""
        if self.db_connection:
            self.db_connection.close()
            logger.debug("Connexió amb la base de dades tancada")
