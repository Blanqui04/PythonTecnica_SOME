import os
import pytest
import logging
import sys

# Configura logging per mostrar missatges INFO a consola
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Afegeix project root i src/ al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database.database_uploader import DatabaseUploader  # noqa: E402

client = "ZF"
ref_project = "A027Y916"

uploader = DatabaseUploader(
    client=client,
    ref_project=ref_project,
    mapping_path="config/column_mappings/table_mappings.json",
    export_path="data/processed/exports/",
    db_config_path="config/database/db_config.json",
    db_key="primary"
)

# 🔎 Mostra els fitxers disponibles al directori d’exportació
logger.info("\n📂 Fitxers disponibles a 'exports':")
try:
    export_files = os.listdir(uploader.export_path)
    for file in export_files:
        logger.info(f"  - {file}")
except Exception as e:
    logger.warning(f"❌ Error accedint al directori d’exportació: {e}")

# Carrega mappings
mappings = uploader._load_mappings()
logger.info(f"\n✔️ Mappings trobats: {list(mappings.keys())}")

# Llegeix CSVs del directori d’exportació
dfs = uploader._get_dataframes()
for table_name in mappings.keys():
    if table_name in dfs:
        df = dfs[table_name]
        logger.info(f"✔️ [{table_name}] {len(df)} files carregades correctament.")
    else:
        logger.warning(f"⚠️ [{table_name}] CSV no trobat o no carregat.")

# Test de connexió a la base de dades
def test_database_connection():
    from src.database.database_connection import PostgresConn
    import json

    db_key = "primary"
    config_path = "config/database/db_config.json"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            db_configs = json.load(f)
        db_params = db_configs[db_key]
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        pytest.fail(f"❌ Error llegint el fitxer de configuració: {e}")
        return

    try:
        db = PostgresConn(**db_params)
        conn = db.connect()
        assert conn is not None, "❌ La connexió ha retornat None!"
        logger.info("✔️ Connexió a la base de dades establerta correctament.")
        conn.close()
    except Exception as e:
        pytest.fail(f"❌ Error connectant a la base de dades: {e}")
