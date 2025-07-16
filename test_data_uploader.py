# test_data_uploader.py
import os
import sys

# Afegeix la carpeta 'src' al path per poder importar correctament
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.database.database_uploader import DatabaseUploader

def main():
    client = "ADIENT"             # <-- canvia-ho si cal
    ref_project = "5704341"       # <-- canvia-ho segons el projecte a provar

    print(f"\n🚀 Iniciant pujada a base de dades per a {client=} i {ref_project=}\n")

    uploader = DatabaseUploader(
        client=client,
        ref_project=ref_project,
        db_key="primary",  # o "dev", "test" segons la configuració a db_config.json
        mapping_path="config/column_mappings/table_mappings.json",
        export_path="data/processed/exports/",
        db_config_path="config/database/db_config.json"
    )

    try:
        uploader.run()
        print("\n✅ Pujada completada amb èxit!\n")
    except Exception as e:
        print(f"\n❌ Error durant la pujada de dades: {e}\n")

if __name__ == "__main__":
    main()
