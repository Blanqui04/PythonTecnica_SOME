"""
Database Schema Adapter for Quality Measurements

Aquest mòdul s'encarrega d'adaptar l'esquema de la base de dades per guardar
les mesures de qualitat obtingudes del network scanner.

Adapta la taula mesuresqualitat per incloure totes les columnes del dat            'client': 'character varying(100)',
            'data_hora': 'timestamp without time zone',
            'maquina': 'character varying(50) DEFAULT \'gompc\'',
            'fase': 'character varying(100)',  # Nova columna per clients especials
            'element': 'character varying(200)', CSV.
"""

import logging
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class QualityMeasurementDBAdapter:
    """Gestiona l'adaptació de l'esquema de BBDD per les mesures de qualitat"""
    
    def __init__(self, db_config: Dict[str, str]):
        """
        Inicialitza l'adaptador
        
        Args:
            db_config: Configuració de la base de dades
        """
        self.db_config = db_config
        self.connection = None
        
        # Mapatge de columnes CSV a columnes BBDD
        self.column_mapping = {
            'CLIENT': 'client',
            'REFERENCIA': 'id_referencia_client',
            'LOT': 'id_lot',
            'DATA_HORA': 'data_hora',
            'FASE': 'fase',  # Nova columna per clients especials
            'RIVETS_TYPE': 'rivets_type',  # Nova columna específica per PTCOVER
            'CAVITAT': 'cavitat',  # Nova columna específica per PTCOVER
            'Element': 'element',
            'Pieza': 'pieza',
            'Datum': 'datum',
            'Property': 'property',
            'Nominal': 'nominal',
            'Actual': 'actual',
            'Tol -': 'tolerancia_negativa',
            'Tol +': 'tolerancia_positiva',
            'Dev': 'desviacio',
            'Check': 'check_value',
            'Out': 'out_value',
            'Alignment': 'alignment'
        }
        
        # Camp fixe per aquesta màquina
        self.maquina = "gompc"
    
    def connect(self) -> bool:
        """
        Connecta a la base de dades
        
        Returns:
            bool: True si la connexió és exitosa
        """
        try:
            # Utilitzar configuració primary si existeix, sinó configuració directa
            if 'primary' in self.db_config:
                config = self.db_config['primary']
            else:
                config = self.db_config
            
            self.connection = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                # Assegurar encoding UTF-8 per suportar Unicode correctament
                client_encoding='utf8'
            )
            self.connection.autocommit = True
            
            # Configurar la connexió per treballar amb UTF-8
            with self.connection.cursor() as cursor:
                cursor.execute("SET CLIENT_ENCODING TO 'UTF8'")
                cursor.execute("SET DateStyle TO 'ISO, DMY'")
                
            logger.info(f"Connexió a la base de dades establerta amb UTF-8: {config['host']}:{config['port']}")
            return True
        except Exception as e:
            logger.error(f"Error connectant a la base de dades: {e}")
            return False
    
    def disconnect(self):
        """Tanca la connexió a la base de dades"""
        if self.connection:
            self.connection.close()
            logger.info("Connexió a la base de dades tancada")
    
    def close(self):
        """Àlies per disconnect() per compatibilitat"""
        self.disconnect()
    
    def get_current_table_structure(self) -> Dict[str, str]:
        """
        Obté l'estructura actual de la taula mesuresqualitat
        
        Returns:
            dict: Diccionari amb nom_columna: tipus_dada
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, character_maximum_length, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'mesuresqualitat' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                
                columns = {}
                for row in cursor.fetchall():
                    col_name, data_type, max_length, is_nullable = row
                    if max_length:
                        full_type = f"{data_type}({max_length})"
                    else:
                        full_type = data_type
                    
                    columns[col_name] = {
                        'type': full_type,
                        'nullable': is_nullable == 'YES'
                    }
                
                logger.info(f"Estructura actual de mesuresqualitat: {len(columns)} columnes")
                return columns
                
        except Exception as e:
            logger.error(f"Error obtenint estructura de la taula: {e}")
            return {}
    
    def create_adapted_table_schema(self) -> str:
        """
        Genera l'SQL per crear la taula mesuresqualitat adaptada
        
        Returns:
            str: SQL per crear la taula
        """
        sql = """
        -- Taula mesuresqualitat adaptada per mesures de qualitat GOMPC amb suport Unicode i precisió millorada
        DROP TABLE IF EXISTS mesuresqualitat CASCADE;
        
        CREATE TABLE mesuresqualitat (
            -- Claus primàries originals (mantingudes per compatibilitat)
            id_referencia_some character varying(100) NOT NULL,
            id_element character varying(100) NOT NULL,
            
            -- Camps originals amb tipus millorats
            valor numeric(15,6),  -- Precisió millorada per preservar decimals
            ok boolean,
            id_referencia_client character varying(100),
            id_lot character varying(100),
            
            -- Nous camps per les dades de qualitat GOMPC
            client character varying(100),
            data_hora timestamp without time zone,
            maquina character varying(50) DEFAULT 'gompc',
            fase character varying(100),  -- Nova columna per clients especials (MATRIU, PLA, etc.)
            rivets_type character varying(100),  -- Nova columna específica per PTCOVER (4 RIVETS, 5 RIVETS)
            cavitat character varying(100),  -- Nova columna específica per PTCOVER (nom de la cavitat)
            
            -- Camps detallats de la mesura amb tipus millorats per suportar Unicode i precisió
            element character varying(200),
            pieza character varying(200),
            datum character varying(200),
            property character varying(200),
            nominal numeric(15,6),  -- Precisió millorada
            actual numeric(15,6),   -- Precisió millorada
            tolerancia_negativa numeric(15,6),  -- Precisió millorada
            tolerancia_positiva numeric(15,6),  -- Precisió millorada
            desviacio numeric(15,6),  -- Precisió millorada
            check_value character varying(100),
            out_value character varying(100),
            alignment character varying(200),
            
            -- Metadades
            created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT mesuresqualitat_pkey PRIMARY KEY (id_referencia_some, id_element)
        );
        
        -- Índexs per millorar el rendiment
        CREATE INDEX idx_mesuresqualitat_client ON mesuresqualitat(client);
        CREATE INDEX idx_mesuresqualitat_lot ON mesuresqualitat(id_lot);
        CREATE INDEX idx_mesuresqualitat_data_hora ON mesuresqualitat(data_hora);
        CREATE INDEX idx_mesuresqualitat_maquina ON mesuresqualitat(maquina);
        CREATE INDEX idx_mesuresqualitat_referencia_client ON mesuresqualitat(id_referencia_client);
        
        -- Comentaris per documentar
        COMMENT ON TABLE mesuresqualitat IS 'Mesures de qualitat obtingudes de les màquines de control (GOMPC, etc.)';
        COMMENT ON COLUMN mesuresqualitat.maquina IS 'Identificador de la màquina que ha fet la mesura (gompc, etc.)';
        COMMENT ON COLUMN mesuresqualitat.data_hora IS 'Data i hora de la mesura extreta del nom del fitxer';
        COMMENT ON COLUMN mesuresqualitat.client IS 'Nom del client (AUTOLIV, BROSE, etc.)';
        """
        
        return sql
    
    def update_table_schema(self) -> Dict[str, Any]:
        """
        Actualitza l'esquema de la taula mesuresqualitat
        
        Returns:
            dict: Resultat de l'actualització amb success i message
        """
        try:
            logger.info("Actualitzant esquema de la taula mesuresqualitat...")
            
            # Obtenir estructura actual
            current_structure = self.get_current_table_structure()
            
            if not current_structure:
                logger.info("La taula no existeix, creant nova estructura...")
                schema_sql = self.create_adapted_table_schema()
                
                with self.connection.cursor() as cursor:
                    cursor.execute(schema_sql)
                
                logger.info("Nova taula mesuresqualitat creada amb èxit")
                return {
                    'success': True,
                    'message': 'Nova taula mesuresqualitat creada amb èxit'
                }
            
            else:
                logger.info("La taula existeix, aplicant modificacions necessàries...")
                
                # Crear script d'actualització progressiva
                alter_statements = self._generate_alter_statements(current_structure)
                
                with self.connection.cursor() as cursor:
                    for statement in alter_statements:
                        try:
                            cursor.execute(statement)
                            logger.info(f"Executat: {statement[:50]}...")
                        except Exception as e:
                            logger.warning(f"Error executant ALTER: {e}")
                
                logger.info("Taula mesuresqualitat actualitzada")
                return {
                    'success': True,
                    'message': f'Taula actualitzada amb {len(alter_statements)} modificacions'
                }
                
        except Exception as e:
            logger.error(f"Error actualitzant esquema: {e}")
            return {
                'success': False,
                'message': f'Error actualitzant esquema: {e}'
            }
    
    def _generate_alter_statements(self, current_structure: Dict) -> List[str]:
        """
        Genera statements ALTER TABLE per afegir columnes faltants
        
        Args:
            current_structure: Estructura actual de la taula
            
        Returns:
            list: Llista de statements SQL
        """
        statements = []
        
        # Columnes noves que cal afegir
        new_columns = {
            'client': 'character varying(100)',
            'data_hora': 'timestamp without time zone',
            'maquina': "character varying(50) DEFAULT 'gompc'",
            'fase': 'character varying(100)',  # Nova columna per clients especials
            'rivets_type': 'character varying(100)',  # Nova columna específica per PTCOVER
            'cavitat': 'character varying(100)',  # Nova columna específica per PTCOVER
            'element': 'character varying(200)',
            'pieza': 'character varying(200)',
            'datum': 'character varying(200)',
            'property': 'character varying(200)',
            'nominal': 'real',
            'actual': 'real',
            'tolerancia_negativa': 'real',
            'tolerancia_positiva': 'real',
            'desviacio': 'real',
            'check_value': 'character varying(100)',
            'out_value': 'character varying(100)',
            'alignment': 'character varying(200)',
            'created_at': 'timestamp without time zone DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'timestamp without time zone DEFAULT CURRENT_TIMESTAMP'
        }
        
        # Afegir columnes que no existeixen
        for col_name, col_type in new_columns.items():
            if col_name not in current_structure:
                statements.append(f"ALTER TABLE mesuresqualitat ADD COLUMN {col_name} {col_type};")
        
        # Afegir índexs si no existeixen
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_client ON mesuresqualitat(client);",
            "CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_lot ON mesuresqualitat(id_lot);",
            "CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_data_hora ON mesuresqualitat(data_hora);",
            "CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_maquina ON mesuresqualitat(maquina);",
            "CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_referencia_client ON mesuresqualitat(id_referencia_client);",
            "CREATE INDEX IF NOT EXISTS idx_mesuresqualitat_fase ON mesuresqualitat(fase);"
        ]
        
        statements.extend(index_statements)
        
        return statements
    
    def generate_table_update_statements(self) -> List[str]:
        """
        Genera statements per actualitzar l'esquema de la taula si cal
        
        Returns:
            list: Llista de statements SQL per actualitzar l'esquema
        """
        try:
            current_structure = self.get_current_table_structure()
            return self._generate_alter_statements(current_structure)
        except Exception as e:
            logger.error(f"Error generant statements d'actualització: {e}")
            return []
    
    def prepare_dataset_for_insertion(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara el dataset per a la inserció a la BBDD amb suport Unicode millorat
        
        Args:
            df: DataFrame amb les dades del CSV
            
        Returns:
            DataFrame preparat per la inserció amb encoding correcte
        """
        logger.info(f"Preparant dataset de {len(df)} files per inserció amb suport Unicode")
        
        # Crear còpia del dataset
        prepared_df = df.copy()
        
        # Neteja inicial - eliminar columnes duplicades
        prepared_df = prepared_df.loc[:, ~prepared_df.columns.duplicated()]
        
        # Neteja de caràcters especials i normalització Unicode millorada
        prepared_df = self._clean_encoding_issues_enhanced(prepared_df)
        
        # Verificar que tenim les columnes essencials
        required_cols = ['CLIENT', 'REFERENCIA', 'LOT']
        for col in required_cols:
            if col not in prepared_df.columns:
                logger.error(f"Columna essencial {col} no trobada al dataset")
                return pd.DataFrame()  # Retornar dataset buit
        
        # Generar claus primàries amb normalització Unicode
        prepared_df['id_referencia_some'] = (
            self._normalize_text_for_db(prepared_df['CLIENT'].astype(str)) + '_' + 
            self._normalize_text_for_db(prepared_df['REFERENCIA'].astype(str)) + '_' + 
            self._normalize_text_for_db(prepared_df['LOT'].astype(str))
        )
        
        # Generar id_element amb més seguretat i normalització
        element_col = prepared_df.get('Element', pd.Series(['UNKNOWN'] * len(prepared_df)))
        property_col = prepared_df.get('Property', pd.Series(['UNKNOWN'] * len(prepared_df)))
        
        prepared_df['id_element'] = (
            self._normalize_text_for_db(element_col.fillna('UNKNOWN').astype(str)) + '_' + 
            self._normalize_text_for_db(property_col.fillna('UNKNOWN').astype(str))
        )
        
        # Mapear columnes - només les que existeixen
        column_mapping = {}
        for csv_col, db_col in self.column_mapping.items():
            if csv_col in prepared_df.columns:
                column_mapping[csv_col] = db_col
        
        prepared_df = prepared_df.rename(columns=column_mapping)
        
        # Afegir camp màquina
        prepared_df['maquina'] = self.maquina
        
        # Convertir data_hora a timestamp
        if 'data_hora' in prepared_df.columns:
            prepared_df['data_hora'] = pd.to_datetime(prepared_df['data_hora'], errors='coerce')
        
        # Assignar valor i ok basant-se en 'actual' amb precisió millorada
        if 'actual' in prepared_df.columns:
            prepared_df['valor'] = self._convert_to_numeric_with_precision(prepared_df['actual'])
            # Determinar OK basant-se en si està dins de toleràncies
            prepared_df['ok'] = self._calculate_ok_status(prepared_df)
        else:
            prepared_df['valor'] = None
            prepared_df['ok'] = True
        
        # Afegir timestamps
        current_time = datetime.now()
        prepared_df['created_at'] = current_time
        prepared_df['updated_at'] = current_time
        
        # Netejar valors NaN per columnes que no poden ser NULL
        prepared_df['id_referencia_some'] = prepared_df['id_referencia_some'].fillna('UNKNOWN')
        prepared_df['id_element'] = prepared_df['id_element'].fillna('UNKNOWN')
        
        # Convertir camps numèrics amb gestió millorada de precisió
        numeric_cols = ['nominal', 'actual', 'tolerancia_negativa', 'tolerancia_positiva', 'desviacio', 'valor']
        for col in numeric_cols:
            if col in prepared_df.columns:
                prepared_df[col] = self._convert_to_numeric_with_precision(prepared_df[col])
        
        # Convertir camps de text amb normalització Unicode i limitar longitud
        text_cols = ['client', 'element', 'pieza', 'datum', 'property', 'check_value', 'out_value', 'alignment', 'fase']
        for col in text_cols:
            if col in prepared_df.columns:
                prepared_df[col] = prepared_df[col].apply(self._normalize_text_for_db).str[:200]
        
        # Per clients regulars sense fase, afegir columna buida
        if 'fase' not in prepared_df.columns:
            prepared_df['fase'] = None
        
        logger.info(f"Dataset preparat amb suport Unicode: {len(prepared_df)} files, {len(prepared_df.columns)} columnes")
        return prepared_df
    
    def _calculate_ok_status(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula l'estat OK basant-se en toleràncies
        
        Args:
            df: DataFrame amb les dades
            
        Returns:
            Series amb valors booleanos
        """
        ok_status = pd.Series(True, index=df.index)
        
        # Si hi ha toleràncies definides, comprovar si està dins dels límits
        if all(col in df.columns for col in ['actual', 'nominal', 'tolerancia_negativa', 'tolerancia_positiva']):
            actual = pd.to_numeric(df['actual'], errors='coerce')
            nominal = pd.to_numeric(df['nominal'], errors='coerce')
            tol_neg = pd.to_numeric(df['tolerancia_negativa'], errors='coerce')
            tol_pos = pd.to_numeric(df['tolerancia_positiva'], errors='coerce')
            
            # Calcular límits
            lower_limit = nominal + tol_neg  # tol_neg ja hauria de ser negatiu
            upper_limit = nominal + tol_pos
            
            # Marcar com NOK si està fora de toleràncies
            mask_valid = actual.notna() & nominal.notna() & tol_neg.notna() & tol_pos.notna()
            mask_out_of_tolerance = (actual < lower_limit) | (actual > upper_limit)
            
            ok_status.loc[mask_valid & mask_out_of_tolerance] = False
        
        return ok_status
    
    def _clean_encoding_issues(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Neteja problemes d'encoding per evitar errors UTF8/WIN1252
        
        Args:
            df: DataFrame original
            
        Returns:
            DataFrame net
        """
        import unicodedata
        import re
        
        cleaned_df = df.copy()
        
        # Llista de caràcters problemàtics coneguts i les seves substitucions
        # Nota: No tocar separadors decimals (,.) ni símbols numèrics fins després de la conversió
        char_replacements = {
            'Ø': 'O',  # Caràcter danès/noruec
            'ø': 'o',
            'Å': 'A',
            'å': 'a',
            'Æ': 'AE',
            'æ': 'ae',
            'Ä': 'A',
            'ä': 'a',
            'Ö': 'O',
            'ö': 'o',
            'Ü': 'U',
            'ü': 'u',
            'ß': 'ss',
            'Ñ': 'N',
            'ñ': 'n',
            'Ç': 'C',
            'ç': 'c',
            # Caràcters numèrics els deixem per la conversió específica
            # '°': 'deg',  # Grau - es neteja en la conversió numèrica
            # 'μ': 'u',    # Micro - es neteja en la conversió numèrica
            # 'Δ': 'Delta',  # Delta grec
            # '±': '+/-',   # Més/menys - es neteja en la conversió numèrica
            '²': '2',     # Superíndex 2
            '³': '3',     # Superíndex 3
        }
        
        # Processar columnes de text
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == 'object':  # Columnes de text
                try:
                    # Convertir a string i aplicar substitucions
                    cleaned_df[col] = cleaned_df[col].astype(str)
                    
                    # Aplicar substitucions de caràcters coneguts
                    for problematic, replacement in char_replacements.items():
                        cleaned_df[col] = cleaned_df[col].str.replace(problematic, replacement, regex=False)
                    
                    # Normalitzar unicode i eliminar accents
                    cleaned_df[col] = cleaned_df[col].apply(
                        lambda x: unicodedata.normalize('NFKD', str(x))
                        .encode('ascii', 'ignore')
                        .decode('ascii') if pd.notna(x) else x
                    )
                    
                    # Eliminar caràcters de control i no imprimibles
                    cleaned_df[col] = cleaned_df[col].apply(
                        lambda x: re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(x)) if pd.notna(x) else x
                    )
                    
                except Exception as e:
                    logger.warning(f"Error netejant encoding de la columna {col}: {e}")
                    # Si hi ha error, mantenir valors originals
                    pass
        
        logger.info("Neteja d'encoding completada")
        return cleaned_df

    def _convert_to_numeric_european(self, series: pd.Series) -> pd.Series:
        """
        Converteix una sèrie a valors numèrics gestionant formats europeus
        
        Args:
            series: Sèrie pandas amb valors a convertir
            
        Returns:
            Sèrie pandas amb valors numèrics
        """
        def clean_numeric_value(value):
            """Neteja un valor per convertir-lo a numèric"""
            if pd.isna(value):
                return None
            
            # Convertir a string
            str_val = str(value).strip()
            
            # Si ja és un número vàlid, retornar-lo
            try:
                return float(str_val)
            except ValueError:
                pass
            
            # Netejar valors comuns
            str_val = str_val.replace(' ', '')  # Eliminar espais
            str_val = str_val.replace('±', '')   # Eliminar símbol ±
            str_val = str_val.replace('+/-', '') # Eliminar +/-
            str_val = str_val.replace('°', '')   # Eliminar símbols de grau
            str_val = str_val.replace('μ', '')   # Eliminar micro
            
            # Si conté comes i punts, determinar quin és el separador decimal
            if ',' in str_val and '.' in str_val:
                # Format: 1.234,56 (europeu) -> 1234.56
                if str_val.rindex(',') > str_val.rindex('.'):
                    str_val = str_val.replace('.', '').replace(',', '.')
                # Format: 1,234.56 (americà) -> mantenir
                else:
                    str_val = str_val.replace(',', '')
            elif ',' in str_val:
                # Només comes - assumir format europeu: 1,5 -> 1.5
                str_val = str_val.replace(',', '.')
            
            # Eliminar caràcters no numèrics excepte el punt decimal i el signe menys
            import re
            str_val = re.sub(r'[^\d\.\-]', '', str_val)
            
            # Assegurar que només hi ha un punt decimal
            parts = str_val.split('.')
            if len(parts) > 2:
                str_val = parts[0] + '.' + ''.join(parts[1:])
            
            try:
                return float(str_val) if str_val else None
            except ValueError:
                logger.warning(f"No s'ha pogut convertir valor: '{value}' -> '{str_val}'")
                return None
        
        # Aplicar la funció de neteja
        cleaned_series = series.apply(clean_numeric_value)
        
        # Informar sobre conversions
        original_count = len(series.dropna())
        converted_count = len(cleaned_series.dropna())
        if original_count > 0:
            success_rate = (converted_count / original_count) * 100
            logger.info(f"Conversió numèrica: {converted_count}/{original_count} valors ({success_rate:.1f}%)")
        
        return cleaned_series

    def _calculate_ok_status(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula l'estat OK basant-se en toleràncies
        
        Args:
            df: DataFrame amb dades
            
        Returns:
            Series amb valors True/False per l'estat OK
        """
        try:
            ok_status = pd.Series([True] * len(df), index=df.index)
            
            # Si tenim toleràncies, verificar si està dins dels límits
            if all(col in df.columns for col in ['actual', 'tolerancia_negativa', 'tolerancia_positiva']):
                actual = pd.to_numeric(df['actual'], errors='coerce')
                tol_neg = pd.to_numeric(df['tolerancia_negativa'], errors='coerce')
                tol_pos = pd.to_numeric(df['tolerancia_positiva'], errors='coerce')
                
                # Calcular límits
                lower_limit = tol_neg  # Tolerància negativa ja inclou el signe
                upper_limit = tol_pos  # Tolerància positiva
                
                # Verificar si està dins dels límits
                within_limits = (
                    (actual >= lower_limit) & 
                    (actual <= upper_limit)
                )
                
                # Només aplicar on tenim valors vàlids
                valid_mask = actual.notna() & tol_neg.notna() & tol_pos.notna()
                ok_status.loc[valid_mask] = within_limits.loc[valid_mask]
            
            return ok_status
            
        except Exception as e:
            logger.warning(f"Error calculant estat OK: {e}")
            # Retornar tots True per defecte
            return pd.Series([True] * len(df), index=df.index)
    
    def insert_dataset(self, df: pd.DataFrame, batch_size: int = 1000) -> Dict[str, Any]:
        """
        Insereix el dataset a la taula mesuresqualitat
        
        Args:
            df: DataFrame amb les dades preparades
            batch_size: Mida del lot per la inserció
            
        Returns:
            dict: Resum de la inserció amb success, records_inserted, errors, etc.
        """
        try:
            logger.info(f"Iniciant inserció de {len(df)} files en lots de {batch_size}")
            
            # El dataset ja ha de venir preparat, no cal preparar-lo de nou
            prepared_df = df.copy()
            
            # Obtenir columnes de la taula
            table_columns = self.get_current_table_structure()
            
            # Filtrar només columnes que existeixen a la taula
            df_columns = [col for col in prepared_df.columns if col in table_columns]
            insert_df = prepared_df[df_columns]
            
            # Inserció en lots
            total_inserted = 0
            total_errors = 0
            errors_list = []
            
            for i in range(0, len(insert_df), batch_size):
                batch = insert_df.iloc[i:i+batch_size]
                
                try:
                    # Generar SQL d'inserció
                    placeholders = ', '.join(['%s'] * len(df_columns))
                    columns_str = ', '.join(df_columns)
                    
                    sql = f"""
                    INSERT INTO mesuresqualitat ({columns_str}) 
                    VALUES ({placeholders})
                    ON CONFLICT (id_referencia_some, id_element) 
                    DO UPDATE SET 
                        {', '.join([f"{col} = EXCLUDED.{col}" for col in df_columns if col not in ['id_referencia_some', 'id_element', 'updated_at']])},
                        updated_at = CURRENT_TIMESTAMP
                    """
                    
                    with self.connection.cursor() as cursor:
                        # Preparar dades per la inserció
                        data_tuples = [tuple(row) for row in batch.values]
                        cursor.executemany(sql, data_tuples)
                    
                    total_inserted += len(batch)
                    logger.info(f"Lot {i//batch_size + 1}: {len(batch)} files inserides (Total: {total_inserted})")
                    
                except Exception as e:
                    total_errors += len(batch)
                    error_msg = f"Error en lot {i//batch_size + 1}: {e}"
                    errors_list.append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Inserció completada: {total_inserted} files inserides, {total_errors} errors")
            
            return {
                'success': total_errors == 0,
                'records_inserted': total_inserted,
                'skipped_records': total_errors,
                'errors': errors_list,
                'total_processed': len(df)
            }
            
        except Exception as e:
            logger.error(f"Error durant la inserció: {e}")
            return {
                'success': False,
                'records_inserted': 0,
                'skipped_records': 0,
                'errors': [str(e)],
                'total_processed': len(df) if 'df' in locals() else 0
            }
    
    def get_insert_summary(self) -> Dict[str, Any]:
        """
        Obté un resum de les dades inserides
        
        Returns:
            dict: Resum de la inserció
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Total records
                cursor.execute("SELECT COUNT(*) as total FROM mesuresqualitat WHERE maquina = %s", (self.maquina,))
                total = cursor.fetchone()['total']
                
                # Per client
                cursor.execute("""
                    SELECT client, COUNT(*) as count 
                    FROM mesuresqualitat 
                    WHERE maquina = %s AND client IS NOT NULL
                    GROUP BY client 
                    ORDER BY count DESC
                """, (self.maquina,))
                by_client = cursor.fetchall()
                
                # Per lot
                cursor.execute("""
                    SELECT COUNT(DISTINCT id_lot) as unique_lots 
                    FROM mesuresqualitat 
                    WHERE maquina = %s AND id_lot IS NOT NULL
                """, (self.maquina,))
                unique_lots = cursor.fetchone()['unique_lots']
                
                # Rang de dates
                cursor.execute("""
                    SELECT MIN(data_hora) as min_date, MAX(data_hora) as max_date 
                    FROM mesuresqualitat 
                    WHERE maquina = %s AND data_hora IS NOT NULL
                """, (self.maquina,))
                date_range = cursor.fetchone()
                
                return {
                    'total_records': total,
                    'unique_lots': unique_lots,
                    'by_client': [dict(row) for row in by_client],
                    'date_range': {
                        'min_date': date_range['min_date'],
                        'max_date': date_range['max_date']
                    },
                    'machine': self.maquina
                }
                
        except Exception as e:
            logger.error(f"Error obtenint resum: {e}")
            return {}
    
    def print_insert_summary(self):
        """Imprimeix un resum de les dades inserides"""
        summary = self.get_insert_summary()
        
        if not summary:
            print("❌ No es pot obtenir el resum de la inserció")
            return
        
        print(f"\n📊 RESUM DE LA INSERCIÓ A MESURESQUALITAT")
        print(f"{'='*60}")
        print(f"🤖 Màquina: {summary['machine']}")
        print(f"📋 Total registres: {summary['total_records']:,}")
        print(f"📦 Lots únics: {summary['unique_lots']}")
        
        if summary['date_range']['min_date'] and summary['date_range']['max_date']:
            print(f"📅 Rang de dates:")
            print(f"   Des de: {summary['date_range']['min_date']}")
            print(f"   Fins a: {summary['date_range']['max_date']}")
        
        if summary['by_client']:
            print(f"\n🏢 DISTRIBUCIÓ PER CLIENT:")
            for client_data in summary['by_client']:
                print(f"   {client_data['client']}: {client_data['count']:,} registres")
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """
        Executa una query SQL i retorna els resultats
        
        Args:
            query: Query SQL a executar
            params: Paràmetres de la query (opcional)
            
        Returns:
            List[tuple]: Resultats de la query
        """
        try:
            if not self.connection:
                raise Exception("No hi ha connexió activa a la base de dades")
            
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Si és una query SELECT o WITH, retornar resultats
                query_stripped = query.strip().upper()
                if query_stripped.startswith('SELECT') or query_stripped.startswith('WITH'):
                    return cursor.fetchall()
                else:
                    # Per queries INSERT/UPDATE/DELETE, confirmar els canvis
                    self.connection.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            logger.error(f"Error executant query: {e}")
            if self.connection:
                self.connection.rollback()
            raise e
    
    def execute_query_to_dataframe(self, query: str, params: tuple = None) -> pd.DataFrame:
        """
        Executa una query SQL i retorna els resultats com a DataFrame
        
        Args:
            query: Query SQL a executar
            params: Paràmetres de la query (opcional)
            
        Returns:
            pd.DataFrame: Resultats de la query com a DataFrame
        """
        try:
            if not self.connection:
                raise Exception("No hi ha connexió activa a la base de dades")
            
            # Usar pandas per llegir directament de la BD
            if params:
                df = pd.read_sql_query(query, self.connection, params=params)
            else:
                df = pd.read_sql_query(query, self.connection)
            
            logger.info(f"Query executada correctament: {len(df)} files retornades")
            return df
            
        except Exception as e:
            logger.error(f"Error executant query to DataFrame: {e}")
            raise e
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Obté informació detallada d'una taula
        
        Args:
            table_name: Nom de la taula
            
        Returns:
            Dict amb informació de la taula
        """
        try:
            info = {}
            
            # Informació bàsica de la taula
            query = """
            SELECT 
                schemaname, tablename, tableowner, 
                hasindexes, hasrules, hastriggers
            FROM pg_tables 
            WHERE tablename = %s
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (table_name,))
                result = cursor.fetchone()
                
                if result:
                    info['basic'] = {
                        'schema': result[0],
                        'name': result[1],
                        'owner': result[2],
                        'has_indexes': result[3],
                        'has_rules': result[4],
                        'has_triggers': result[5]
                    }
                
                # Columnes de la taula
                columns_query = """
                SELECT 
                    column_name, data_type, character_maximum_length,
                    is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
                """
                
                cursor.execute(columns_query, (table_name,))
                columns = cursor.fetchall()
                
                info['columns'] = []
                for col in columns:
                    info['columns'].append({
                        'name': col[0],
                        'type': col[1],
                        'max_length': col[2],
                        'nullable': col[3] == 'YES',
                        'default': col[4]
                    })
                
                # Contar files
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                cursor.execute(count_query)
                info['row_count'] = cursor.fetchone()[0]
            
            return info
            
        except Exception as e:
            logger.error(f"Error obtenint informació de la taula {table_name}: {e}")
            return {}
    
    def update_record_by_key(self, table_name: str, key_column: str, key_value: str, updates: Dict[str, Any]) -> bool:
        """
        Actualitza un registre utilitzant qualsevol columna com a clau
        
        Args:
            table_name: Nom de la taula
            key_column: Nom de la columna clau
            key_value: Valor de la clau
            updates: Diccionari amb les columnes i valors a actualitzar
            
        Returns:
            bool: True si s'ha actualitzat correctament
        """
        try:
            if not updates:
                return False
            
            # Construir query UPDATE amb la clau personalitzada
            set_clauses = []
            values = []
            
            for column, value in updates.items():
                set_clauses.append(f'"{column}" = %s')
                values.append(value)
            
            query = f"""
            UPDATE "{table_name}" 
            SET {', '.join(set_clauses)}
            WHERE "{key_column}" = %s
            """
            
            values.append(key_value)
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, values)
                self.connection.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Registre amb {key_column}={key_value} actualitzat a {table_name}")
                    return True
                else:
                    logger.warning(f"No s'ha trobat el registre amb {key_column}={key_value} a {table_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error actualitzant registre per clau: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def update_record(self, table_name: str, record_id: int, updates: Dict[str, Any]) -> bool:
        """
        Actualitza un registre específic
        
        Args:
            table_name: Nom de la taula
            record_id: ID del registre a actualitzar
            updates: Diccionari amb les columnes i valors a actualitzar
            
        Returns:
            bool: True si s'ha actualitzat correctament
        """
        try:
            if not updates:
                return False
            
            # Construir query UPDATE
            set_clauses = []
            values = []
            
            for column, value in updates.items():
                set_clauses.append(f"{column} = %s")
                values.append(value)
            
            query = f"""
            UPDATE {table_name} 
            SET {', '.join(set_clauses)}
            WHERE id = %s
            """
            
            values.append(record_id)
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, values)
                self.connection.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Registre {record_id} actualitzat a {table_name}")
                    return True
                else:
                    logger.warning(f"No s'ha trobat el registre {record_id} a {table_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error actualitzant registre: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def delete_record_by_key(self, table_name: str, key_column: str, key_value: str) -> bool:
        """
        Elimina un registre utilitzant qualsevol columna com a clau
        
        Args:
            table_name: Nom de la taula
            key_column: Nom de la columna clau
            key_value: Valor de la clau
            
        Returns:
            bool: True si s'ha eliminat correctament
        """
        try:
            query = f'DELETE FROM "{table_name}" WHERE "{key_column}" = %s'
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (key_value,))
                self.connection.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Registre amb {key_column}={key_value} eliminat de {table_name}")
                    return True
                else:
                    logger.warning(f"No s'ha trobat el registre amb {key_column}={key_value} a {table_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error eliminant registre per clau: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def delete_record(self, table_name: str, record_id: int) -> bool:
        """
        Elimina un registre específic
        
        Args:
            table_name: Nom de la taula
            record_id: ID del registre a eliminar
            
        Returns:
            bool: True si s'ha eliminat correctament
        """
        try:
            query = f"DELETE FROM {table_name} WHERE id = %s"
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (record_id,))
                self.connection.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Registre {record_id} eliminat de {table_name}")
                    return True
                else:
                    logger.warning(f"No s'ha trobat el registre {record_id} a {table_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error eliminant registre: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def _normalize_text_for_db(self, text_series_or_value) -> str:
        """
        Normalitza text per a la base de dades (reemplaça caràcters Unicode problemàtics)
        
        Args:
            text_series_or_value: Text o sèrie de pandas a normalitzar
            
        Returns:
            str o sèrie: Text normalitzat
        """
        from src.services.value_cleaner import ValueCleaner
        
        if pd.isna(text_series_or_value):
            return ""
        
        if isinstance(text_series_or_value, pd.Series):
            return text_series_or_value.apply(lambda x: ValueCleaner.normalize_unicode_text(str(x)) if not pd.isna(x) else "")
        else:
            return ValueCleaner.normalize_unicode_text(str(text_series_or_value))
    
    def _convert_to_numeric_with_precision(self, numeric_series) -> pd.Series:
        """
        Converteix una sèrie a numèric amb màxima precisió preservada
        
        Args:
            numeric_series: Sèrie de pandas amb valors numèrics
            
        Returns:
            pd.Series: Sèrie amb valors numèrics nets
        """
        from src.services.value_cleaner import ValueCleaner
        
        if isinstance(numeric_series, pd.Series):
            return numeric_series.apply(ValueCleaner.clean_numeric_value)
        else:
            return ValueCleaner.clean_numeric_value(numeric_series)
    
    def _clean_encoding_issues_enhanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Neteja problemes d'encoding amb suport Unicode millorat
        
        Args:
            df: DataFrame a netejar
            
        Returns:
            DataFrame: DataFrame amb encoding net
        """
        from src.services.value_cleaner import ValueCleaner
        
        df_clean = df.copy()
        
        # Netejar totes les columnes de text
        for col in df_clean.select_dtypes(include=['object']).columns:
            try:
                df_clean[col] = df_clean[col].apply(
                    lambda x: ValueCleaner.normalize_unicode_text(str(x)) if not pd.isna(x) else x
                )
            except Exception as e:
                logger.warning(f"Error netejant columna {col}: {e}")
                continue
        
        return df_clean
