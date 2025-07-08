class DatabaseUploader:
    def __init__(self):
        self.db_service = DatabaseService()
    
    def upload_project_data(self, processed_data):
        """Upload processed data to database"""
        try:
            # Upload in correct order (respecting foreign keys)
            self._upload_projects(processed_data['projects'])
            self._upload_parts(processed_data['parts'])
            self._upload_measurements(processed_data['measurements'])
            self._upload_batches(processed_data['batches'])
            
        except Exception as e:
            # Rollback on error
            self.db_service.rollback()
            raise e
    
    def _upload_projects(self, projects_data):
        """Upload projects table"""
        query = """
        INSERT INTO projects (client_name, ref_project, created_at)
        VALUES (%(client_name)s, %(ref_project)s, %(created_at)s)
        ON CONFLICT (client_name, ref_project) DO UPDATE SET
        updated_at = NOW()
        """
        self.db_service.execute_query(query, projects_data)