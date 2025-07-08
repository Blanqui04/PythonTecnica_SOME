class ExternalDbService:
    def __init__(self):
        self.external_db_connection = ExternalDbConnection()
    
    def enrich_data(self, excel_data, client_name, ref_project):
        """Enrich excel data with external DB info"""
        # Get missing info from external DB
        external_data = self._get_project_info(client_name, ref_project)
        
        # Merge with excel data
        enriched_data = self._merge_data(excel_data, external_data)
        
        return enriched_data
    
    def _get_project_info(self, client_name, ref_project):
        """Query external DB for project info"""
        query = """
        SELECT part_specifications, tolerances, materials 
        FROM external_projects 
        WHERE client = %s AND project_ref = %s
        """
        return self.external_db_connection.execute_query(query, (client_name, ref_project))
    
    def _merge_data(self, excel_data, external_data):
        """Merge excel and external data"""
        # Your merging logic here
        return merged_data