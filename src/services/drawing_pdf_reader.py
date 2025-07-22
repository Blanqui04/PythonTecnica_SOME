"""
Drawing PDF Reader Service

Aquest servei s'encarrega de buscar i guardar PDFs de dibuixos des del servidor
de fitxers a la base de dades.
"""

import os
import re
import glob
import base64
from typing import List, Dict, Optional
from pathlib import Path
from src.gui.logging_config import logger
from src.database.database_connection import PostgresConn
import json


class DrawingPDFReader:
    """Gestiona la cerca i guardada de PDFs de dibuixos"""
    
    # Configuració del servidor
    SERVER_BASE_PATH = r"\\server.some.local\Projectes en curs"
    TECHNICAL_INFO_FOLDER = "2-PART TECHNICAL INFO"
    DRAWINGS_FOLDER = "1-CUSTOMER PART DRAWINGS"
    
    def __init__(self, client_name: str, project_id: str, db_config_path: str = "config/database/db_config.json"):
        self.client_name = client_name.upper().strip()
        self.project_id = project_id.strip()
        self.db_config_path = db_config_path
        
    def read_and_save_drawings(self) -> Dict:
        """
        Busca tots els PDFs de dibuixos i els guarda a la base de dades
        
        Returns:
            Diccionari amb el resultat de l'operació
        """
        try:
            logger.info(f"Llegint dibuixos per client: {self.client_name}, projecte: {self.project_id}")
            
            # Validar connexió al servidor
            if not self._validate_server_connection():
                return {
                    'success': False,
                    'error': f"No es pot accedir al servidor: {self.SERVER_BASE_PATH}",
                    'pdfs_found': 0,
                    'pdfs_saved': 0
                }
            
            # Buscar PDFs
            pdf_files = self._find_drawing_pdfs()
            
            if not pdf_files:
                return {
                    'success': False,
                    'error': f"No s'han trobat PDFs de dibuixos per al projecte {self.project_id}",
                    'pdfs_found': 0,
                    'pdfs_saved': 0
                }
            
            # Guardar PDFs a la base de dades
            saved_count = self._save_pdfs_to_database(pdf_files)
            
            return {
                'success': True,
                'message': f"S'han processat {len(pdf_files)} PDFs, {saved_count} guardats/actualitzats",
                'pdfs_found': len(pdf_files),
                'pdfs_saved': saved_count,
                'pdf_list': [pdf['filename'] for pdf in pdf_files]
            }
            
        except Exception as e:
            logger.error(f"Error llegint dibuixos: {e}")
            return {
                'success': False,
                'error': f"Error processat dibuixos: {str(e)}",
                'pdfs_found': 0,
                'pdfs_saved': 0
            }
    
    def _validate_server_connection(self) -> bool:
        """Valida que el servidor sigui accessible"""
        try:
            return os.path.exists(self.SERVER_BASE_PATH)
        except Exception as e:
            logger.error(f"Error validant connexió al servidor: {e}")
            return False
    
    def _find_drawing_pdfs(self) -> List[Dict]:
        """
        Busca tots els PDFs de dibuixos per al projecte
        
        Returns:
            Llista de diccionaris amb informació dels PDFs trobats
        """
        try:
            # Construir path de la carpeta de dibuixos
            drawings_path = self._get_drawings_path()
            
            if not drawings_path or not os.path.exists(drawings_path):
                logger.warning(f"Carpeta de dibuixos no trobada: {drawings_path}")
                return []
            
            # Buscar PDFs amb el patró: primeres 3 xifres del projecte + XXXX_versió.pdf
            project_prefix = self.project_id[:3]  # Primeres 3 xifres
            pattern = f"{project_prefix}*_*.pdf"
            search_pattern = os.path.join(drawings_path, pattern)
            
            logger.debug(f"Cercant PDFs amb patró: {search_pattern}")
            
            pdf_files = []
            found_files = glob.glob(search_pattern)
            
            # Patró per extreure informació del nom del fitxer
            filename_pattern = re.compile(rf"({re.escape(project_prefix)}\d*)_(\d+)\.pdf$", re.IGNORECASE)
            
            for pdf_path in found_files:
                filename = os.path.basename(pdf_path)
                match = filename_pattern.match(filename)
                
                if match:
                    drawing_number = match.group(1)  # Ex: "658061"
                    version = int(match.group(2))    # Ex: 5 (de "005")
                    
                    # Llegir el fitxer PDF
                    try:
                        with open(pdf_path, 'rb') as f:
                            pdf_data = f.read()
                        
                        pdf_info = {
                            'filename': filename,
                            'file_path': pdf_path,
                            'drawing_number': drawing_number,
                            'version': version,
                            'pdf_data': pdf_data,
                            'file_size': len(pdf_data)
                        }
                        
                        pdf_files.append(pdf_info)
                        logger.debug(f"PDF trobat: {filename} (dibuix: {drawing_number}, versió: {version})")
                        
                    except Exception as e:
                        logger.warning(f"Error llegint PDF {filename}: {e}")
                else:
                    logger.debug(f"PDF ignorat (no coincideix amb el patró): {filename}")
            
            # Ordenar per número de dibuix i versió
            pdf_files.sort(key=lambda x: (x['drawing_number'], x['version']))
            
            logger.info(f"Trobats {len(pdf_files)} PDFs de dibuixos")
            return pdf_files
            
        except Exception as e:
            logger.error(f"Error buscant PDFs de dibuixos: {e}")
            return []
    
    def _get_drawings_path(self) -> Optional[str]:
        """Obté el path de la carpeta de dibuixos"""
        try:
            # Path del client
            client_path = os.path.join(self.SERVER_BASE_PATH, self.client_name)
            
            if not os.path.exists(client_path):
                logger.warning(f"Carpeta del client no trobada: {client_path}")
                return None
            
            # Buscar carpeta del projecte
            project_folder = None
            for item in os.listdir(client_path):
                item_path = os.path.join(client_path, item)
                if os.path.isdir(item_path) and item.startswith(self.project_id):
                    project_folder = item_path
                    break
            
            if not project_folder:
                logger.warning(f"Carpeta del projecte no trobada per ID: {self.project_id}")
                return None
            
            # Construir path dels dibuixos
            drawings_path = os.path.join(
                project_folder,
                self.TECHNICAL_INFO_FOLDER,
                self.DRAWINGS_FOLDER
            )
            
            return drawings_path
            
        except Exception as e:
            logger.error(f"Error obtenint path de dibuixos: {e}")
            return None
    
    def _save_pdfs_to_database(self, pdf_files: List[Dict]) -> int:
        """
        Guarda els PDFs a la base de dades
        
        Args:
            pdf_files: Llista de PDFs a guardar
            
        Returns:
            Nombre de PDFs guardats/actualitzats
        """
        saved_count = 0
        
        try:
            # Connectar a la base de dades
            with open(self.db_config_path, encoding='utf-8') as f:
                db_configs = json.load(f)
            
            db_config = db_configs.get("primary", {})
            conn = PostgresConn(**db_config)
            
            for pdf_info in pdf_files:
                try:
                    # Convertir PDF a base64 per guardar-lo
                    pdf_base64 = base64.b64encode(pdf_info['pdf_data']).decode('utf-8')
                    
                    # Crear estructura JSON similar a la que s'usa actualment
                    pdf_json = {
                        'filename': pdf_info['filename'],
                        'drawing_number': pdf_info['drawing_number'],
                        'version': pdf_info['version'],
                        'file_size': pdf_info['file_size'],
                        'pdf_data': pdf_base64
                    }
                    
                    # Insertar o actualitzar a la taula planol
                    query = """
                    INSERT INTO planol (id_referencia_client, num_planol, imatge)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id_referencia_client, num_planol) 
                    DO UPDATE SET imatge = EXCLUDED.imatge
                    """
                    
                    params = (
                        self.client_name,
                        pdf_info['drawing_number'],
                        json.dumps(pdf_json)
                    )
                    
                    conn.execute_query(query, params)
                    saved_count += 1
                    
                    logger.info(f"PDF guardat: {pdf_info['filename']} (dibuix: {pdf_info['drawing_number']}, versió: {pdf_info['version']})")
                    
                except Exception as e:
                    logger.error(f"Error guardant PDF {pdf_info['filename']}: {e}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error connectant a la base de dades: {e}")
        
        return saved_count
    
    def get_drawings_info(self) -> Dict:
        """
        Obté informació sobre els dibuixos disponibles sense guardar-los
        
        Returns:
            Diccionari amb informació dels dibuixos trobats
        """
        try:
            pdf_files = self._find_drawing_pdfs()
            
            if not pdf_files:
                return {
                    'success': False,
                    'error': "No s'han trobat PDFs de dibuixos",
                    'drawings_path': self._get_drawings_path(),
                    'pdfs_found': []
                }
            
            # Resumir informació sense les dades binàries
            pdfs_info = []
            for pdf in pdf_files:
                pdfs_info.append({
                    'filename': pdf['filename'],
                    'drawing_number': pdf['drawing_number'],
                    'version': pdf['version'],
                    'file_size': pdf['file_size']
                })
            
            return {
                'success': True,
                'drawings_path': self._get_drawings_path(),
                'pdfs_found': pdfs_info,
                'total_count': len(pdfs_info)
            }
            
        except Exception as e:
            logger.error(f"Error obtenint informació de dibuixos: {e}")
            return {
                'success': False,
                'error': str(e),
                'drawings_path': None,
                'pdfs_found': []
            }
