# src/services/measurement_history_service.py

import logging
import json
import os
from typing import List, Dict, Any, Optional
from src.database.database_connection import PostgresConn

logger = logging.getLogger(__name__)

# Constants per les noves taules de mesures al schema 1000_SQB_qualitat
# Cada màquina té la seva pròpia taula amb estructura específica
# IMPORTANT: El schema comença amb número, per tant necessita cometes dobles
MEASUREMENT_SCHEMA = '"1000_SQB_qualitat"'

# Mapatge de columnes per cada taula (normalització a estructura comuna)
# Format: 'columna_estandar': 'columna_real_a_taula'
TABLE_COLUMN_MAPPING = {
    'mesures_gompc_projectes': {
        'table': 'mesures_gompc_projectes',
        'schema': '1000_SQB_qualitat',
        'machine_name': 'GOMPC Projectes (Escanner Projectes)',
        'type': 'dimensional',
        'columns': {
            'id_referencia_client': 'id_referencia_some',  # Referència (NOTA: id_referencia_some!)
            'id_lot': 'id_lot',  # LOT
            'element': 'id_element',  # Element/característica
            'pieza': 'element',  # Nom element (backup)
            'datum': 'element',  # Datum (mateix que element)
            'property': 'element',  # Property (mateix que element)
            'actual': 'actual',  # Valor mesurat
            'nominal': 'nominal',  # Valor nominal
            'tolerancia_positiva': 'tolerancia_positiva',  # Tolerància +
            'tolerancia_negativa': 'tolerancia_negativa',  # Tolerància -
            'desviacio': 'desviacio',  # Desviació
            'data_hora': 'data_hora',  # Timestamp
            'cavitat': 'cavitat'  # Cavitat (si existeix)
        }
    },
    'mesures_gompc_produccio': {
        'table': 'mesures_gompc_produccio',
        'schema': '1000_SQB_qualitat',
        'machine_name': 'GOMPC Producció (Escanner Producció)',
        'type': 'dimensional',
        'columns': {
            'id_referencia_client': 'id_referencia_some',  # Referència
            'id_lot': 'id_lot',
            'element': 'id_element',
            'pieza': 'element',
            'datum': 'element',
            'property': 'element',
            'actual': 'actual',
            'nominal': 'nominal',
            'tolerancia_positiva': 'tolerancia_positiva',
            'tolerancia_negativa': 'tolerancia_negativa',
            'desviacio': 'desviacio',
            'data_hora': 'data_hora',
            'cavitat': 'cavitat'
        }
    },
    'mesureshoytom': {
        'table': 'mesureshoytom',
        'schema': '1000_SQB_qualitat',
        'machine_name': 'Hoytom',
        'type': 'tensile',
        'columns': {
            'id_referencia_client': 'ref_some',  # Columna real: ref_some
            'id_lot': 'operacion_lot_fabric_n',  # LOT real: operacion_lot_fabric_n
            'element': 'tipo_ensayo',  # Usar tipo_ensayo com a element
            'pieza': 'tipo_probeta',  # Tipus de proveta
            'datum': 'denom_probeta',  # Denominació proveta
            'property': 'modo_rotura',  # Mode de rotura
            'actual': 'resist_max_rm',  # Resistència màxima (valor principal)
            'nominal': None,  # No té nominal fix
            'tolerancia_positiva': None,  # No té toleràncies definides
            'tolerancia_negativa': None,
            'desviacio': None,  # No té desviació
            'data_hora': 'fecha_ensayo',  # Data de l'assaig
            'cavitat': None  # No té cavitat
        }
    },
    'mesurestorsio': {
        'table': 'mesurestorsio',
        'schema': '1000_SQB_qualitat',
        'machine_name': 'Desoutter (Torsió)',
        'type': 'torsion',
        'columns': {
            'id_referencia_client': 'ref_some',  # Columna real: ref_some
            'id_lot': 'lot',  # LOT real: lot
            'element': 'tipassaig',  # Tipus d'assaig com a element
            'pieza': 'familia',  # Família
            'datum': 'rosca',  # Rosca
            'property': 'pset',  # PSet
            'actual': 'torque',  # Valor de torque (principal)
            'nominal': None,  # No té nominal fix
            'tolerancia_positiva': None,  # No té toleràncies
            'tolerancia_negativa': None,
            'desviacio': None,  # No té desviació
            'data_hora': 'DataHoraCorrect',  # Data/hora corregida
            'cavitat': None
        }
    },
    'mesureszwick': {
        'table': 'mesureszwick',
        'schema': '1000_SQB_qualitat',
        'machine_name': 'Zwick',
        'type': 'tensile',
        'columns': {
            'id_referencia_client': 'reference',  # Columna real: reference
            'id_lot': 'batch',  # LOT real: batch (també hi ha inspection_lot)
            'element': 'test_type',  # Tipus de test com a element
            'pieza': 'part_name',  # Nom de la peça
            'datum': 'station',  # Estació
            'property': 'break_type',  # Tipus de trencament
            'actual': 'max_force',  # Força màxima (valor principal)
            'nominal': None,  # No té nominal fix
            'tolerancia_positiva': None,  # No té toleràncies
            'tolerancia_negativa': None,
            'desviacio': None,  # No té desviació
            'data_hora': 'test_datetime',  # Data/hora del test
            'cavitat': 'cavity'  # SÍ té cavitat!
        }
    }
}

# Definició de màquines disponibles
MACHINE_TABLES = {
    'gompc_projectes': {
        'name': 'GOMPC Projectes (Escanner Projectes)',
        'table_key': 'mesures_gompc_projectes',
        'description': 'Mesures dimensionals de projectes amb escàner GOMPC',
        'type': 'dimensional'
    },
    'gompc_produccio': {
        'name': 'GOMPC Producció (Escanner Producció)',
        'table_key': 'mesures_gompc_produccio',
        'description': 'Mesures dimensionals de producció amb escàner GOMPC',
        'type': 'dimensional'
    },
    'hoytom': {
        'name': 'Hoytom',
        'table_key': 'mesureshoytom',
        'description': 'Assaigs de tracció amb màquina Hoytom',
        'type': 'tensile'
    },
    'torsio': {
        'name': 'Desoutter (Torsió)',
        'table_key': 'mesurestorsio',
        'description': 'Assaigs de torsió amb torquímetre Desoutter',
        'type': 'torsion'
    },
    'zwick': {
        'name': 'Zwick',
        'table_key': 'mesureszwick',
        'description': 'Assaigs de tracció amb màquina Zwick',
        'type': 'tensile'
    },
    'all': {
        'name': 'Totes les màquines',
        'table_key': 'all',
        'description': 'Consulta a totes les taules de mesures disponibles',
        'type': 'mixed'
    }
}

# Taules per defecte (per compatibilitat amb codi existent)
# PRIORITZEM mesures_gompc_projectes com a taula principal
DEFAULT_TABLE = 'mesures_gompc_projectes'
ALL_TABLES = list(TABLE_COLUMN_MAPPING.keys())

class MeasurementHistoryService:
    """Servei per obtenir l'historial de mesures de la base de dades"""
    
    def __init__(self, machine: str = 'gompc_projectes'):
        """
        Inicialitza el servei amb la configuració de la base de dades
        
        Args:
            machine: Tipus de màquina/taula a utilitzar. Opcions:
                    - 'gompc_projectes': GOMPC Projectes (PER DEFECTE)
                    - 'gompc_produccio': GOMPC Producció
                    - 'hoytom': Hoytom
                    - 'torsio': Desoutter (Torsió)
                    - 'zwick': Zwick
                    - 'all': Totes les màquines
        """
        self.db_connection = None
        self.machine = machine
        self.schema = MEASUREMENT_SCHEMA  # Sempre utilitzem 1000_SQB_qualitat
        
        # Obtenir configuració de la màquina seleccionada
        if machine in MACHINE_TABLES:
            machine_config = MACHINE_TABLES[machine]
            self.machine_name = machine_config['name']
            
            # Si és 'all', utilitzar totes les taules
            if machine == 'all':
                self.table_keys = ALL_TABLES
            else:
                self.table_keys = [machine_config['table_key']]
            
            logger.info(f"Màquina seleccionada: {self.machine_name}")
            logger.info(f"Taules: {self.table_keys}")
        else:
            # Fallback a taula per defecte
            self.table_keys = [DEFAULT_TABLE]
            self.machine_name = TABLE_COLUMN_MAPPING[DEFAULT_TABLE]['machine_name']
            logger.warning(f"Màquina '{machine}' no reconeguda, usant taula per defecte: {DEFAULT_TABLE}")
        
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
    
    def _get_table_mapping(self, table_key: str) -> Dict[str, Any]:
        """Obté el mapatge de columnes per una taula específica"""
        if table_key in TABLE_COLUMN_MAPPING:
            return TABLE_COLUMN_MAPPING[table_key]
        else:
            logger.warning(f"Taula '{table_key}' no trobada al mapatge, usant default")
            return TABLE_COLUMN_MAPPING[DEFAULT_TABLE]
    
    def _build_select_columns(self, table_key: str) -> str:
        """Construeix la llista de columnes SELECT amb àlies per normalitzar noms"""
        mapping = self._get_table_mapping(table_key)
        columns = mapping['columns']
        
        select_parts = []
        for std_col, real_col in columns.items():
            if real_col is None:
                # Columna no disponible, usar NULL
                select_parts.append(f"NULL as {std_col}")
            else:
                # Columna disponible
                if real_col == std_col:
                    select_parts.append(real_col)
                else:
                    select_parts.append(f"{real_col} as {std_col}")
        
        return ", ".join(select_parts)
    
    def _get_reference_column(self, table_key: str) -> str:
        """Obté el nom real de la columna de referència per una taula"""
        mapping = self._get_table_mapping(table_key)
        return mapping['columns']['id_referencia_client']
    
    def _get_lot_column(self, table_key: str) -> str:
        """Obté el nom real de la columna de LOT per una taula"""
        mapping = self._get_table_mapping(table_key)
        return mapping['columns']['id_lot']
    
    def _build_union_query_with_mapping(self, where_conditions: Dict[str, str], 
                                         order_by: str = None, 
                                         limit: int = None) -> tuple:
        """
        Construeix un query UNION ALL utilitzant el mapatge de columnes
        
        Args:
            where_conditions: Diccionari amb condicions WHERE per columnes estàndard
                            Ex: {'id_referencia_client': 'SOME123', 'id_lot': 'LOT001'}
            order_by: Columna estàndard per ORDER BY (opcional)
            limit: Límit de resultats (opcional)
            
        Returns:
            Tuple (query, params)
        """
        union_parts = []
        all_params = []
        
        for table_key in self.table_keys:
            mapping = self._get_table_mapping(table_key)
            table_name = f"{self.schema}.{mapping['table']}"
            
            # Construir SELECT amb columnes normalitzades
            select_cols = self._build_select_columns(table_key)
            
            # Construir WHERE amb columnes reals
            where_parts = []
            table_params = []
            for std_col, value in where_conditions.items():
                real_col = mapping['columns'].get(std_col)
                if real_col and real_col != 'NULL':
                    if value is not None:
                        where_parts.append(f"{real_col} = %s")
                        table_params.append(value)
            
            # Construir query per aquesta taula
            query = f"SELECT {select_cols} FROM {table_name}"
            if where_parts:
                query += f" WHERE {' AND '.join(where_parts)}"
            
            union_parts.append(f"({query})")
            all_params.extend(table_params)
        
        # Unir totes les parts
        final_query = " UNION ALL ".join(union_parts)
        
        # Afegir ORDER BY i LIMIT a l'exterior
        if order_by:
            final_query = f"SELECT * FROM ({final_query}) AS combined ORDER BY {order_by}"
        if limit:
            final_query += f" LIMIT {limit}"
        
        return (final_query, tuple(all_params))
    
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
    
    def get_element_measurements(self, client: str, project_reference: str, element_name: str, property_name: str = None, batch_lot: str = None, lot: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obté mesures específiques per un element
        Utilitza el nou sistema de mapatge de columnes
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte  
            element_name: Nom de l'element
            property_name: Propietat (opcional, per compatibilitat)
            batch_lot: Batch/lot (opcional, per compatibilitat)
            lot: LOT específic (opcional)
            limit: Límit de resultats
            
        Returns:
            Llista de mesures per l'element especificat
        """
        try:
            logger.info(f"🔍 [NEW SYSTEM] Obtenint mesures per element='{element_name}'")
            
            # Usar batch_lot si lot no està especificat
            if lot is None and batch_lot:
                lot = batch_lot
            
            # Variants de referència
            ref_variants = [
                project_reference,
                f"{project_reference}D",
                f"{project_reference}_D",
                project_reference.upper(),
                project_reference.lower()
            ]
            
            all_measurements = []
            
            for table_key in self.table_keys:
                try:
                    mapping = self._get_table_mapping(table_key)
                    table_name = f"{self.schema}.{mapping['table']}"
                    
                    # Columnes reals
                    ref_col = mapping['columns']['id_referencia_client']
                    lot_col = mapping['columns']['id_lot']
                    element_col = mapping['columns']['element']
                    actual_col = mapping['columns']['actual']
                    nominal_col = mapping['columns']['nominal']
                    tol_pos_col = mapping['columns']['tolerancia_positiva']
                    tol_neg_col = mapping['columns']['tolerancia_negativa']
                    desv_col = mapping['columns']['desviacio']
                    data_col = mapping['columns']['data_hora']
                    cavitat_col = mapping['columns']['cavitat'] if mapping['columns']['cavitat'] else 'NULL'
                    
                    # Query amb columnes normalitzades
                    if lot:
                        query = f"""
                            SELECT 
                                {ref_col} as id_referencia_client,
                                {element_col} as element,
                                {element_col} as pieza,
                                {element_col} as datum,
                                {element_col} as property,
                                {actual_col} as actual,
                                {nominal_col} as nominal,
                                {tol_neg_col} as tolerancia_negativa,
                                {tol_pos_col} as tolerancia_positiva,
                                {desv_col} as desviacio,
                                {data_col} as data_hora,
                                {lot_col} as id_lot,
                                {cavitat_col} as cavitat
                            FROM {table_name}
                            WHERE {ref_col} IN (%s, %s, %s, %s, %s)
                            AND {element_col} = %s
                            AND {lot_col} = %s
                            ORDER BY {data_col} DESC
                            LIMIT %s
                        """
                        params = tuple(ref_variants + [element_name, lot, limit])
                    else:
                        query = f"""
                            SELECT 
                                {ref_col} as id_referencia_client,
                                {element_col} as element,
                                {element_col} as pieza,
                                {element_col} as datum,
                                {element_col} as property,
                                {actual_col} as actual,
                                {nominal_col} as nominal,
                                {tol_neg_col} as tolerancia_negativa,
                                {tol_pos_col} as tolerancia_positiva,
                                {desv_col} as desviacio,
                                {data_col} as data_hora,
                                {lot_col} as id_lot,
                                {cavitat_col} as cavitat
                            FROM {table_name}
                            WHERE {ref_col} IN (%s, %s, %s, %s, %s)
                            AND {element_col} = %s
                            ORDER BY {data_col} DESC
                            LIMIT %s
                        """
                        params = tuple(ref_variants + [element_name, limit])
                    
                    results = self.db_connection.fetchall(query, params)
                    
                    if results:
                        logger.info(f"   ✅ {table_key}: {len(results)} mesures")
                        all_measurements.extend(results)
                        
                except Exception as e:
                    logger.warning(f"   ⚠️ Error en {table_key}: {e}")
                    continue
            
            # Processar resultats
            measurements = []
            for row in all_measurements:
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
                
            logger.info(f"✅ Total: {len(measurements)} mesures per {element_name}")
            return measurements
            
        except Exception as e:
            logger.error(f"Error obtenint mesures de l'element: {e}")
            raise
    
    def get_available_elements(self, client: str, project_reference: str, batch_lot: str = None, lot: str = None) -> List[Dict[str, Any]]:
        """
        Obté tots els elements disponibles per un client i projecte
        Utilitza el nou sistema de mapatge de columnes per schema 1000_SQB_qualitat
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte  
            batch_lot: Batch/lot específic (opcional, per compatibilitat)
            lot: LOT específic (opcional)
            
        Returns:
            Llista de diccionaris amb els elements disponibles
        """
        try:
            logger.info(f"🔍 [NEW SYSTEM] Buscant elements a {self.schema}")
            logger.info(f"   Client: '{client}', Referència: '{project_reference}'")
            logger.info(f"   Taules: {self.table_keys}")
            
            # Usar batch_lot si lot no està especificat
            if lot is None and batch_lot:
                lot = batch_lot
            
            all_results = []
            
            for table_key in self.table_keys:
                try:
                    mapping = self._get_table_mapping(table_key)
                    table_name = f"{self.schema}.{mapping['table']}"
                    
                    # Columnes reals per aquesta taula
                    ref_col = mapping['columns']['id_referencia_client']
                    lot_col = mapping['columns']['id_lot']
                    element_col = mapping['columns']['element']
                    
                    logger.info(f"   🔎 Consultant taula: {table_name}")
                    logger.info(f"      Columna referència: {ref_col}")
                    
                    # Construir query amb variants de referència
                    ref_variants = [
                        project_reference,
                        f"{project_reference}D",
                        f"{project_reference}_D",
                        project_reference.upper(),
                        project_reference.lower()
                    ]
                    
                    # Query per obtenir elements distincts
                    if lot:
                        query = f"""
                            SELECT 
                                COALESCE({element_col}, 'N/A') as element,
                                COALESCE({element_col}, 'N/A') as pieza, 
                                COALESCE({element_col}, 'N/A') as datum,
                                COALESCE({element_col}, 'N/A') as property,
                                {ref_col} as id_referencia_client,
                                COUNT(*) as count
                            FROM {table_name}
                            WHERE {ref_col} IN (%s, %s, %s, %s, %s)
                            AND {lot_col} = %s
                            GROUP BY {element_col}, {ref_col}
                            ORDER BY element
                        """
                        params = tuple(ref_variants + [lot])
                    else:
                        query = f"""
                            SELECT 
                                COALESCE({element_col}, 'N/A') as element,
                                COALESCE({element_col}, 'N/A') as pieza, 
                                COALESCE({element_col}, 'N/A') as datum,
                                COALESCE({element_col}, 'N/A') as property,
                                {ref_col} as id_referencia_client,
                                COUNT(*) as count
                            FROM {table_name}
                            WHERE {ref_col} IN (%s, %s, %s, %s, %s)
                            GROUP BY {element_col}, {ref_col}
                            ORDER BY element
                        """
                        params = tuple(ref_variants)
                    
                    results = self.db_connection.fetchall(query, params)
                    
                    if results:
                        logger.info(f"      ✅ Trobats {len(results)} elements")
                        all_results.extend(results)
                    else:
                        logger.debug(f"      ❌ Cap element trobat")
                        
                except Exception as e:
                    logger.warning(f"   ⚠️ Error consultant {table_key}: {e}")
                    continue
            
            # Processar resultats
            elements = []
            seen = set()  # Evitar duplicats
            
            for row in all_results:
                # Crear clau única per element
                key = f"{row[0]}_{row[4]}"  # element_referència
                if key not in seen:
                    seen.add(key)
                    elements.append({
                        'element': row[0],
                        'pieza': row[1], 
                        'datum': row[2],
                        'property': row[3],
                        'ref_client': row[4],
                        'count': row[5],
                        'name': row[0]  # Afegir 'name' per compatibilitat
                    })
            
            batch_info = f" per LOT {lot}" if lot else ""
            logger.info(f"✅ Total: {len(elements)} elements únics{batch_info}")
            return elements
            
        except Exception as e:
            logger.error(f"❌ Error obtenint elements disponibles: {e}")
            raise
    
    def get_distinct_lots(self, client: str, project_reference: str) -> List[str]:
        """
        Obté LOTs distints per un client i referència
        Utilitza el nou sistema de mapatge de columnes
        
        Args:
            client: Nom del client
            project_reference: Referència del projecte
            
        Returns:
            Llista de LOTs distints ordenats
        """
        try:
            logger.info(f"🔍 [NEW SYSTEM] Obtenint LOTs distints")
            logger.info(f"   Client: '{client}', Referència: '{project_reference}'")
            
            lots = set()
            
            # Variants de referència
            ref_variants = [
                project_reference,
                f"{project_reference}D",
                f"{project_reference}_D",
                project_reference.upper(),
                project_reference.lower()
            ]
            
            for table_key in self.table_keys:
                try:
                    mapping = self._get_table_mapping(table_key)
                    table_name = f"{self.schema}.{mapping['table']}"
                    
                    ref_col = mapping['columns']['id_referencia_client']
                    lot_col = mapping['columns']['id_lot']
                    
                    query = f"""
                        SELECT DISTINCT {lot_col}
                        FROM {table_name}
                        WHERE {ref_col} IN (%s, %s, %s, %s, %s)
                        AND {lot_col} IS NOT NULL
                        AND {lot_col} != ''
                    """
                    
                    results = self.db_connection.fetchall(query, tuple(ref_variants))
                    
                    if results:
                        for row in results:
                            if row[0]:
                                lots.add(row[0])
                        logger.info(f"   ✅ {table_key}: {len(results)} LOTs")
                        
                except Exception as e:
                    logger.warning(f"   ⚠️ Error en {table_key}: {e}")
                    continue
            
            lot_list = sorted(list(lots))
            logger.info(f"✅ Total: {len(lot_list)} LOTs distints")
            return lot_list
            
        except Exception as e:
            logger.error(f"❌ Error obtenint LOTs distints: {e}")
            return []
    
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
