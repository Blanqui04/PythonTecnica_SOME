# src/gui/utils/session_manager.py 
import json
import os
from datetime import datetime
from typing import Dict, Any

class CapabilitySessionManager:
    def __init__(self, base_path: str = "./data/sessions"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def save_session(self, session_data: Dict[str, Any], filename: str = None) -> str:
        """Save session data to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capability_session_{timestamp}.json"

        filepath = os.path.join(self.base_path, filename)
        
        # Add metadata
        session_data['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }

        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)

        return filepath

    def load_session(self, filepath: str) -> Dict[str, Any]:
        """Load session data from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Verify version compatibility
        metadata = data.get('metadata', {})
        if metadata.get('version', '0.0') != '1.0':
            raise ValueError("Incompatible session version")
            
        return data

    def get_recent_sessions(self, limit: int = 5) -> list:
        """Get list of recent session files"""
        sessions = []
        for filename in os.listdir(self.base_path):
            if filename.endswith('.json'):
                filepath = os.path.join(self.base_path, filename)
                sessions.append({
                    'filepath': filepath,
                    'timestamp': os.path.getmtime(filepath)
                })
        
        # Sort by timestamp and limit
        sessions.sort(key=lambda x: x['timestamp'], reverse=True)
        return sessions[:limit]
