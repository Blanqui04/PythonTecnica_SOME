import os
import logging
from src.database.database_uploader import DatabaseUploader

logger = logging.getLogger(__name__)

def update_database(client: str, ref_project: str,
                    db_key: str = "primary",
                    mapping_path: str = "config/column_mappings/table_mappings.json",
                    export_path: str = "data/processed/exports/",
                    db_config_path: str = "config/database/db_config.json") -> bool:
    """
    Runs the database uploader with given client and project reference.
    After successful upload, deletes intermediate datasheet and export CSV files.

    Returns True if success, False if failure.
    """
    try:
        uploader = DatabaseUploader(
            client=client,
            ref_project=ref_project,
            db_key=db_key,
            mapping_path=mapping_path,
            export_path=export_path,
            db_config_path=db_config_path
        )
        uploader.run()

        # Build file names based on convention - adapt if needed
        datasheet_path = os.path.join(export_path, f"{client}_{ref_project}_datasheet.xlsx")
        export_csv_path = os.path.join(export_path, f"{client}_{ref_project}_export.csv")

        for file_path in [datasheet_path, export_csv_path]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not delete {file_path}: {e}")

        return True
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        return False
