import pandas as pd
import os
import json
from datetime import datetime

class DataProcessor:
    """Process raw Excel data into structured format"""
    
    def __init__(self):
        self.csv_folder = r'C:\Github\PythonTecnica_SOME\data\temp'
        self.processed_folder = r'C:\Github\PythonTecnica_SOME\data\processed'
    
    def process_kop_data(self, raw_data, client, ref_project):
        """Process KOP specific data"""
        try:
            # Process structure data
            estructura_data = self._process_estructura(raw_data['estructura'], client, ref_project)
            
            # Process extra data
            dades_extra = self._process_dades_extra(raw_data['dades_extra'], client, ref_project)
            
            # Create final datasheet
            datasheet = self._create_datasheet(estructura_data, dades_extra, client, ref_project)
            
            return {
                'estructura': estructura_data,
                'dades_extra': dades_extra,
                'datasheet': datasheet,
                'client': client,
                'ref_project': ref_project,
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error processing KOP data: {e}")
    
    def _process_estructura(self, df, client, ref_project):
        """Process structure data"""
        # Clean structure data
        df.dropna(how='all', inplace=True)
        df.dropna(how='all', axis=1, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        cleaned_data = []
        for _, row in df.iterrows():
            filtered_row = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip() != '']
            if len(filtered_row) > 2:
                filtered_row = filtered_row[:2]
            cleaned_data.append(filtered_row)
        
        # Save as CSV (optional)
        csv_path = os.path.join(self.csv_folder, f"estructura_{client}_{ref_project}.csv")
        cleaned_df = pd.DataFrame(cleaned_data)
        cleaned_df.to_csv(csv_path, index=False, header=False)
        
        return cleaned_data
    
    def _process_dades_extra(self, df, client, ref_project):
        """Process extra data"""
        # Process extra data
        df = df.iloc[:, [1, 2, 5, 6]]
        df.dropna(how='all', inplace=True)
        
        p_1 = df.iloc[:, :2].dropna(how='all')
        p_2 = df.iloc[:, 2:].dropna(how='all')
        
        p_1.columns = ['Key', 'Value']
        p_2.columns = ['Key', 'Value']
        
        result = pd.concat([p_1, p_2], ignore_index=True)
        
        # Save as CSV (optional)
        csv_path = os.path.join(self.csv_folder, f"dades_extra_{client}_{ref_project}.csv")
        result.to_csv(csv_path, index=False, header=False)
        
        return result.to_dict('records')
    
    def _create_datasheet(self, estructura_data, dades_extra, client, ref_project):
        """Create final datasheet"""
        # Convert to DataFrames
        df_estr = pd.DataFrame(estructura_data)
        df_dades = pd.DataFrame(dades_extra)
        
        # Clean and transpose
        df_estr = df_estr.map(lambda x: str(x).replace('\n', ' ').strip() if pd.notnull(x) else x)
        df_dades = df_dades.map(lambda x: str(x).replace('\n', ' ').strip() if pd.notnull(x) else x)
        
        df_est_transposed = df_estr.T
        df_dades_transposed = df_dades.T
        
        # Combine
        combined_df = pd.concat([df_est_transposed, df_dades_transposed], axis=1)
        if len(combined_df) > 2:
            combined_df = combined_df.iloc[:2]
        
        # Save final datasheet
        csv_path = os.path.join(self.processed_folder, f"datasheet_{client}_{ref_project}.csv")
        combined_df.to_csv(csv_path, index=False, header=False)
        
        return combined_df.to_dict('records')