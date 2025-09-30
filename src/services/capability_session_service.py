# src/services/capability_session_service.py
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CapabilitySessionService:
    """Service for managing capability study sessions"""
    
    def __init__(self, base_path: str = "data/capability_studies"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        
    def save_study_session(self, 
                          client: str,
                          ref_project: str,
                          batch_number: str,
                          elements_data: list,
                          study_config: Dict[str, Any],
                          results: Optional[Dict[str, Any]] = None) -> str:
        """Save a capability study session"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{client}_{ref_project}_{batch_number}_{timestamp}.json"
        filepath = os.path.join(self.base_path, filename)
        
        session_data = {
            "metadata": {
                "client": client,
                "ref_project": ref_project,
                "batch_number": batch_number,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            },
            "elements": elements_data,
            "config": study_config,
            "results": results
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        return filepath
    
    def load_study_session(self, filepath: str) -> Dict[str, Any]:
        """Load a capability study session"""
        with open(filepath, 'r') as f:
            session_data = json.dump(f)
            
        if session_data.get("metadata", {}).get("version") != "1.0":
            raise ValueError("Incompatible session version")
            
        return session_data
    
    def get_recent_sessions(self, 
                          client: Optional[str] = None,
                          ref_project: Optional[str] = None) -> list:
        """Get list of recent sessions with optional filtering"""
        sessions = []
        
        for filename in os.listdir(self.base_path):
            if not filename.endswith('.json'):
                continue
                
            if client and not filename.startswith(client):
                continue
                
            if ref_project and ref_project not in filename:
                continue
                
            filepath = os.path.join(self.base_path, filename)
            try:
                with open(filepath, 'r') as f:
                    metadata = json.load(f).get("metadata", {})
                    
                sessions.append({
                    "filepath": filepath,
                    "metadata": metadata,
                    "timestamp": os.path.getmtime(filepath)
                })
            except Exception:
                continue
                
        sessions.sort(key=lambda x: x["timestamp"], reverse=True)
        return sessions
