import os
import json
import logging
import base64
import tempfile
import pandas as pd
from .database_connection import PostgresConn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseUploader:
    def __init__(self, client, ref_project, db_key="secondary",
                 import_path="data/processed/imports/",
                 export_path="data/processed/exports/",
                 db_config_path="config/database/db_config.json"):
        self.client = client
        self.ref_project = ref_project
        self.import_path = import_path
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