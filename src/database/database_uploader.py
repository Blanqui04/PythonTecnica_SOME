import os
import json
import logging
import base64
import tempfile
import pandas as pd
from .database_connection import PostgresConn
from ..services.temp_file_cleaner import TempFileCleaner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseUploader:
    def __init__(self, client, ref_project, db_key="primary",
                 mapping_path="config/column_mappings/table_mappings.json",
                 export_path="data/processed/exports/",
                 db_config_path="config/database/db_config.json"):
        self.client = client
        self.ref_project = ref_project
        self.mapping_path = mapping_path
        self.export_path = export_path
        self.db_config_path = db_config_path
        self.db_key = db_key
        self.conn = self._connect()

    def _connect(self):
        with open(self.db_config_path, encoding='utf-8') as f:
            db_configs = json.load(f)
        if self.db_key not in db_configs:
            raise ValueError(f"Database key '{self.db_key}' not found in config.")
        return PostgresConn(**db_configs[self.db_key])

    def _load_mappings(self):
        with open(self.mapping_path, encoding='utf-8') as f:
            return json.load(f)

    def _get_dataframes(self):
        """Llegeix els fitxers CSV d'exportació per a cada taula del mapping."""
        dfs = {}
        mappings = self._load_mappings()

        for table_name in mappings.keys():
            file_name = f"{self.ref_project}_{table_name}.csv"
            file_path = os.path.join(self.export_path, file_name)

            if not os.path.exists(file_path):
                logger.warning(f"⚠️ Fitxer no trobat per a [{table_name}]: {file_path}")
                continue

            try:
                df = pd.read_csv(file_path)
                dfs[table_name] = df
                logger.info(f"✔️ Carregat: {file_name} ({len(df)} files)")
            except Exception as e:
                logger.warning(f"❌ Error llegint [{file_name}]: {e}")

        return dfs

    def _clean_dataframe_for_db(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converteix valors NaN o None a Python None, per a que SQL els interpreti com a NULL."""
        return df.where(pd.notnull(df), None)

    def upload_all(self):
        mappings = self._load_mappings()
        dataframes = self._get_dataframes()

        load_order = list(mappings.keys())

        errors = {}

        for table in load_order:
            if table not in dataframes:
                logger.warning(f"⚠️ Fitxer no trobat o no carregat per a la taula '{table}'")
                continue

            df = dataframes[table]

            if df.empty:
                logger.warning(f"⚠️ La taula '{table}' està buida. S'omet.")
                continue

            if table in mappings:
                expected_cols = set(mappings[table])
                found_cols = set(df.columns)

                missing_cols = expected_cols - found_cols
                if missing_cols:
                    logger.warning(
                        f"[AVÍS] A '{table}' falten columnes esperades i s'ignoraran: {missing_cols}"
                    )

                ordered_cols = [col for col in mappings[table] if col in df.columns]
                df = df[ordered_cols]
            else:
                logger.warning(f"[AVÍS] No hi ha mapping per a la taula '{table}'. S'omet.")
                continue

            # --- Aquí afegeixes la conversió de tipus només per a ctoferta ---
            if table == 'ctoferta':
                try:
                    df['cicles'] = df['cicles'].astype(int)
                except Exception as e:
                    logger.error(f"Error convertint 'cicles' a int a la taula '{table}': {e}")
                    errors[table] = f"Error tipus 'cicles': {e}"
                    continue

            df = self._clean_dataframe_for_db(df)

            try:
                self.conn.upload_dataframe(df, table)
                logger.info(f"✔️ Dades pujades a la taula '{table}' ({len(df)} files).")
                print(f"✔️ Taula '{table}': pujada correcta amb {len(df)} files")
            except Exception as e:
                errors[table] = str(e)
                logger.error(f"❌ Error pujant a la taula '{table}': {e}")

        if errors:
            print("\n🚨 Errors durant la pujada:")
            for table, err in errors.items():
                print(f" - {table}: {err}")
        else:
            # Si no hi ha errors, executem la neteja automàtica dels fitxers temporals
            try:
                cleaner = TempFileCleaner(config_path="config/cleanup_config.json")
                
                # Determinar polítiques segons el client
                cleanup_result = cleaner.clean_for_project_universal(
                    client=self.client,
                    ref_project=self.ref_project
                )
                
                logger.info(f"Neteja automàtica completada: {cleanup_result.get('summary', 'OK')}")
                print(f"🧹 Neteja automàtica: {cleanup_result.get('files_cleaned', 0)} fitxers eliminats")
                
                if cleanup_result.get('space_freed'):
                    print(f"💾 Espai alliberat: {cleanup_result['space_freed']}")
                    
            except Exception as cleanup_error:
                logger.warning(f"Error en la neteja automàtica: {cleanup_error}")



    def cleanup_csv(self):
        # Ensure export directory exists before trying to list it
        os.makedirs(self.export_path, exist_ok=True)
        
        for filename in os.listdir(self.export_path):
            if self.ref_project in filename and self.client in filename and filename.endswith(".csv"):
                os.remove(os.path.join(self.export_path, filename))
                print(f"🧹 Eliminat: {filename}")
    
    def cleanup_for_any_project(self):
        """Neteja universal per qualsevol tipus de client/projecte."""
        try:
            cleaner = TempFileCleaner(config_path="config/cleanup_config.json")
            
            # Neteja universal basada en el client i projecte actual
            cleanup_result = cleaner.clean_for_project_universal(
                client=self.client,
                ref_project=self.ref_project
            )
            
            # Neteja també fitxers CSV específics d'aquest client/projecte
            self.cleanup_csv()
            
            logger.info(f"Neteja universal completada per {self.client}/{self.ref_project}: {cleanup_result.get('summary', 'OK')}")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Error en neteja universal per {self.client}/{self.ref_project}: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_for_zf_project(self):
        """Neteja específica per projectes ZF amb més control."""
        try:
            cleaner = TempFileCleaner(config_path="config/cleanup_config.json")
            
            # Detectar si és un projecte ZF
            is_zf_project = self.client.upper() == 'ZF' or 'ZF' in self.client.upper()
            
            if is_zf_project:
                # Neteja específica per ZF
                cleanup_result = cleaner.clean_for_zf_project(
                    ref_project=self.ref_project,
                    aggressive=False  # Canvia a True si vols neteja més agressiva
                )
            else:
                # Neteja estàndard per altres clients
                cleanup_result = cleaner.clean_temp_files(
                    project_id=self.ref_project,
                    age_minutes_temp=60,
                    age_hours_processed=6,
                    age_hours_exports=12
                )
            
            # Neteja també fitxers CSV específics d'aquest client/projecte
            self.cleanup_csv()
            
            logger.info(f"Neteja completada per {self.client}/{self.ref_project}: {cleanup_result.get('summary', 'OK')}")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Error en neteja per {self.client}/{self.ref_project}: {e}")
            return {"success": False, "error": str(e)}

    def run(self):
        self.upload_all()
        self.cleanup_csv()

    def get_planol_pdf(self, ref_client, project_id=None):
        """
        Retrieve the latest PDF plan for a given client reference and optionally project.
        
        Args:
            ref_client: Client reference ID (client name)
            project_id: Optional project ID to filter drawings by project
            
        Returns:
            dict: Contains success status, PDF data, filename, and planol number
        """
        logger.debug(f"get_planol_pdf cridat amb ref_client='{ref_client}', project_id='{project_id}'")
        
        if project_id:
            # If project_id provided, filter by drawings that start with project prefix
            project_prefix = project_id[:3] if len(project_id) >= 3 else project_id
            query = """
            SELECT num_planol, imatge 
            FROM planol 
            WHERE id_referencia_client = %s 
              AND num_planol LIKE %s
              AND imatge IS NOT NULL
            ORDER BY num_planol DESC
            LIMIT 1
            """
            params = (ref_client, f"{project_prefix}%")
            logger.debug(f"Consulta amb project_id: query={query}, params={params}")
        else:
            # Original query for backward compatibility
            query = """
            SELECT num_planol, imatge 
            FROM planol 
            WHERE id_referencia_client = %s
              AND imatge IS NOT NULL
            ORDER BY num_planol DESC
            LIMIT 1
            """
            params = (ref_client,)
            logger.debug(f"Consulta sense project_id: query={query}, params={params}")
        
        try:
            conn = self.conn.connect()
            cursor = conn.cursor()
            
            # Debug: Primer llistem tots els plànols per aquesta referència de client
            debug_query = "SELECT num_planol, id_referencia_client FROM planol WHERE id_referencia_client = %s"
            cursor.execute(debug_query, (ref_client,))
            debug_results = cursor.fetchall()
            logger.debug(f"Tots els plànols per ref_client '{ref_client}': {debug_results}")
            
            # Ara executem la consulta real
            cursor.execute(query, params)
            result = cursor.fetchone()
            logger.debug(f"Resultat de la consulta principal: {result}")
            
            if result:
                num_planol, imatge_json = result
                
                # Parse the JSON data
                if isinstance(imatge_json, str):
                    imatge_data = json.loads(imatge_json)
                else:
                    imatge_data = imatge_json
                
                # Extract PDF data
                pdf_base64 = imatge_data.get('pdf_data', '')  # Usar 'pdf_data' en lloc de 'data'
                filename = imatge_data.get('filename', f'planol_{num_planol}.pdf')  # Usar 'filename' en lloc de 'nom'
                
                # Decode base64 to binary
                pdf_binary = base64.b64decode(pdf_base64)
                
                # Log successful retrieval
                logger.info(f"Successfully retrieved planol PDF for client {ref_client}: {filename}")
                
                return {
                    'num_planol': num_planol,
                    'filename': filename,
                    'pdf_data': pdf_binary,
                    'success': True
                }
            else:
                # Log no results found
                logger.warning(f"No planol found for referencia_client: {ref_client}")
                return {
                    'success': False,
                    'error': f'No planol found for referencia_client: {ref_client}'
                }
                
        except Exception as e:
            logger.error(f"Error retrieving planol PDF for client {ref_client}: {str(e)}")
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
        finally:
            cursor.close()

    def save_temp_pdf(self, pdf_data, filename):
        """
        Save PDF data to a temporary file and return the path.
        
        Args:
            pdf_data: Binary PDF data
            filename: Name for the temporary file
            
        Returns:
            str: Path to the temporary file, or None if error occurred
        """
        try:
            # Create a temporary file
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, filename)
            
            # Write PDF data to temporary file
            with open(temp_path, 'wb') as f:
                f.write(pdf_data)
            
            logger.info(f"Temporary PDF saved: {temp_path}")
            return temp_path
        except Exception as e:
            logger.error(f"Error saving temporary PDF: {str(e)}")
            return None

        

            