import os
import json
import logging
import pandas as pd
from .database_connection import PostgresConn

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



    def cleanup_csv(self):
        for filename in os.listdir(self.export_path):
            if self.ref_project in filename and self.client in filename and filename.endswith(".csv"):
                os.remove(os.path.join(self.export_path, filename))
                print(f"🧹 Eliminat: {filename}")

    def run(self):
        self.upload_all()
        self.cleanup_csv()
