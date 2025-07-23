"""
Drawing PDF Reader Service

Aquest servei s'encarrega de buscar i guardar PDFs de dibuixos des del servidor
de fitxers a la base de dades.
"""

import os
import re
import glob
import base64
import time
from typing import List, Dict, Optional
from pathlib import Path
from src.gui.logging_config import logger
from src.database.database_connection import PostgresConn
import json


class DrawingPDFReader:
    """Gestiona la cerca i guardada de PDFs                    
                except Exception as e:
                    logger.error(f"Error guardant PDF {pdf_info['filename']}: {str(e)}", exc_info=True)
            
            try:
                conn.close()
                logger.debug("Connexió a la base de dades tancada correctament")
            except Exception as close_error:
                logger.error(f"Error tancant connexió: {str(close_error)}")
            
        except Exception as e:
            logger.error(f"Error connectant a la base de dades: {str(e)}", exc_info=True)
        
        logger.info(f"Resultat final: {saved_count} PDFs guardats/actualitzats de {len(pdf_files)} totals")
        return saved_countos"""
    
    # Configuració del servidor
    SERVER_BASE_PATH = r"\\server.some.local\\SOME\Projectes en curs"
    TECHNICAL_INFO_FOLDER = "2-PART TECHNICAL INFO"
    TECHNICAL_INFO_FOLDER_ALT = "2- PART TECHNICAL INFO"
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
            
            # Registrar el resultat final del procés
            if saved_count == 0 and len(pdf_files) > 0:
                logger.warning(f"Cap dels {len(pdf_files)} PDFs trobats ha pogut ser guardat a la base de dades")
            elif saved_count < len(pdf_files):
                logger.warning(f"Només s'han guardat {saved_count} dels {len(pdf_files)} PDFs trobats")
            else:
                logger.info(f"Tots els {saved_count} PDFs trobats han estat guardats correctament")
            
            # Preparar informació detallada per al retorn
            pdf_details = []
            for pdf in pdf_files:
                pdf_details.append({
                    'filename': pdf['filename'],
                    'drawing_number': pdf['drawing_number'],
                    'version': pdf['version'],
                    'size': pdf['file_size'],
                    'path': pdf['file_path']
                })
            
            return {
                'success': True,
                'message': f"S'han processat {len(pdf_files)} PDFs, {saved_count} guardats/actualitzats",
                'pdfs_found': len(pdf_files),
                'pdfs_saved': saved_count,
                'pdf_list': [pdf['filename'] for pdf in pdf_files],
                'pdf_details': pdf_details
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
            
            # Buscar PDFs amb diversos patrons per ser més flexible
            project_prefix = self.project_id[:3]  # Primeres 3 xifres
            normalized_prefix = project_prefix.lstrip('0')
            project_full = self.project_id  # ID complet
            normalized_full = project_full.lstrip('0')
            
            # Patrons generals
            patterns = [
                f"{project_prefix}*_*.pdf",  # Patró original
                f"{normalized_prefix}*_*.pdf",  # Versió normalitzada sense zeros inicials
                "*.pdf"  # En el pitjor cas, busca tots els PDFs i després filtra
            ]
            
            # Per a ZF, afegim patrons específics més flexibles
            if self.client_name.upper() == 'ZF':
                logger.debug(f"Utilitzant patrons especials per a client ZF amb projecte {self.project_id}")
                patterns += [
                    # Patrons amb el número complet
                    f"{project_full}*.pdf",
                    f"{normalized_full}*.pdf",
                    # Patrons amb només algunes xifres
                    f"*{project_prefix[-2:]}*.pdf",  # Darreres 2 xifres del prefix
                    f"*{project_full[-4:]}*.pdf",    # Darreres 4 xifres
                    f"49*.pdf",                      # Per 004938000151
                    f"493*.pdf",                     # Parts del número
                    f"4938*.pdf"
                ]
            
            logger.debug(f"Cercant PDFs amb patrons: {patterns}")
            
            # Inicialitzem la llista de PDFs
            found_files = []
            
            # Busquem amb tots els patrons
            for pattern in patterns:
                search_pattern = os.path.join(drawings_path, pattern)
                logger.debug(f"Cercant amb patró: {search_pattern}")
                found_files.extend(glob.glob(search_pattern))
            
            pdf_files = []
            
            # Patró per extreure informació del nom del fitxer - molt més flexible
            # Acceptem diferents formats: número_versió.pdf, número-versió.pdf, número versió.pdf, etc.
            filename_patterns = [
                re.compile(r"(\d+)_(\d+)\.pdf$", re.IGNORECASE),  # Format estàndard: 493800_001.pdf
                re.compile(r"(\d+)[_\- ]?[vV]?(\d+)\.pdf$", re.IGNORECASE),  # Amb separador opcional i 'v' opcional
                re.compile(r"(\d+)\.pdf$", re.IGNORECASE)  # Només número: 493800.pdf (versió per defecte 1)
            ]
            
            # Si el client és ZF, també afegim patrons específics
            if self.client_name.upper() == 'ZF':
                logger.debug("Utilitzant patrons específics per a ZF")
                # Afegim patrons especials per ZF si cal
                filename_patterns.append(re.compile(r"(\d+).*\.pdf$", re.IGNORECASE))  # Qualsevol PDF amb números
            
            for pdf_path in found_files:
                filename = os.path.basename(pdf_path)
                match = None
                drawing_number = None
                version = None
                
                # Prova tots els patrons disponibles
                for pattern in filename_patterns:
                    match = pattern.match(filename)
                    if match:
                        drawing_number = match.group(1)  # Ex: "658061"
                        try:
                            # Si el patró té 2 grups, el segon és la versió
                            version = int(match.group(2)) if match.lastindex >= 2 else 1
                        except (IndexError, ValueError):
                            # Si no hi ha un segon grup o no es pot convertir a enter, assigna versió per defecte
                            version = 1
                        break
                
                if drawing_number:  # Si hem trobat un número de dibuix vàlid
                    
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
            
            # Eliminar duplicats (mateix número de dibuix i versió)
            unique_pdfs = {}
            for pdf in pdf_files:
                key = (pdf['drawing_number'], pdf['version'])
                if key not in unique_pdfs:
                    unique_pdfs[key] = pdf
            
            # Reemplaçar la llista amb els PDFs únics
            pdf_files = list(unique_pdfs.values())
            
            logger.info(f"Trobats {len(pdf_files)} PDFs de dibuixos únics")
            
            if len(pdf_files) == 0:
                logger.warning("No s'han trobat PDFs que coincideixin amb els patrons de cerca")
                
                # Si és el client ZF i projecte específic, fem una cerca exhaustiva
                if self.client_name.upper() == 'ZF' and self.project_id == '004938000151':
                    logger.debug("Intentant cerca exhaustiva per a ZF 004938000151...")
                    
                    # Cerca recursiva de tots els PDFs sota la carpeta del projecte
                    project_path = os.path.dirname(drawings_path) if drawings_path else None
                    if project_path and os.path.exists(project_path):
                        for root, dirs, files in os.walk(project_path):
                            pdf_files_found = [f for f in files if f.lower().endswith('.pdf')]
                            if pdf_files_found:
                                logger.debug(f"PDFs trobats a {root}: {pdf_files_found}")
                                
                                # Intentar carregar aquests PDFs com a últim recurs
                                for pdf_file in pdf_files_found:
                                    try:
                                        pdf_path = os.path.join(root, pdf_file)
                                        with open(pdf_path, 'rb') as f:
                                            pdf_data = f.read()
                                            
                                        # Extreure un número de dibuix del nom del fitxer
                                        # Prenem qualsevol seqüència de dígits com a número de dibuix
                                        drawing_number = re.search(r'(\d+)', pdf_file)
                                        if drawing_number:
                                            drawing_number = drawing_number.group(1)
                                        else:
                                            drawing_number = "000001"  # Valor per defecte
                                            
                                        pdf_info = {
                                            'filename': pdf_file,
                                            'file_path': pdf_path,
                                            'drawing_number': drawing_number,
                                            'version': 1,  # Versió per defecte
                                            'pdf_data': pdf_data,
                                            'file_size': len(pdf_data)
                                        }
                                        
                                        pdf_files.append(pdf_info)
                                        logger.debug(f"PDF afegit de manera especial: {pdf_file}")
                                        
                                    except Exception as e:
                                        logger.warning(f"Error processant PDF {pdf_file}: {e}")
                
                # Llistar tots els arxius de la carpeta per a depuració
                if os.path.exists(drawings_path):
                    all_files = os.listdir(drawings_path)
                    logger.debug(f"Tots els arxius a la carpeta: {all_files}")
            
            return pdf_files
            
        except Exception as e:
            logger.error(f"Error buscant PDFs de dibuixos: {str(e)}", exc_info=True)
            return []
    
    def _get_drawings_path(self) -> Optional[str]:
        """Obté el path de la carpeta de dibuixos"""
        try:
            # Path del client
            client_path = os.path.join(self.SERVER_BASE_PATH, self.client_name)
            logger.debug(f"Buscant en carpeta del client: {client_path}")
            
            if not os.path.exists(client_path):
                logger.warning(f"Carpeta del client no trobada: {client_path}")
                return None
            
            # Normalitzar l'ID del projecte eliminant zeros inicials
            normalized_project_id = self.project_id.lstrip('0')
            
            # Buscar carpeta del projecte - més flexible
            project_folder = None
            for item in os.listdir(client_path):
                item_path = os.path.join(client_path, item)
                item_normalized = item.lstrip('0')
                
                if os.path.isdir(item_path):
                    # Comprovar si l'ID del projecte forma part del nom de la carpeta
                    if (self.project_id in item or
                        normalized_project_id in item or
                        # Comprovar si és part d'un codi compost (separat per _)
                        any(part == self.project_id or part == normalized_project_id 
                            for part in item.split('_'))):
                        
                        project_folder = item_path
                        logger.debug(f"Carpeta del projecte trobada: {item}")
                        break
            
            # Prova amb el path específic conegut per ZF si client és ZF
            if not project_folder and self.client_name.upper() == 'ZF' and self.project_id == '004938000151':
                specific_path = os.path.join(
                    client_path,
                    "004938000151_004938000152 - SENSOR BRACKET LH+RH (ME)"
                )
                if os.path.exists(specific_path):
                    project_folder = specific_path
                    logger.debug(f"Utilitzant carpeta específica coneguda per ZF: {specific_path}")
            
            if not project_folder:
                logger.warning(f"Carpeta del projecte no trobada per ID: {self.project_id}")
                return None
                
            # Construir path dels dibuixos - provar múltiples opcions
            drawing_path_options = [
                # Opció estàndard
                os.path.join(project_folder, self.TECHNICAL_INFO_FOLDER, self.DRAWINGS_FOLDER),
                # Variacions comunes
                os.path.join(project_folder, "2-PART TECHNICAL INFO", "DRAWINGS"),
                os.path.join(project_folder, "PART TECHNICAL INFO", "DRAWINGS"),
                os.path.join(project_folder, "TECHNICAL INFO", "DRAWINGS"),
                os.path.join(project_folder, "TECHNICAL", "DRAWINGS"),
                # Opcions més simples
                os.path.join(project_folder, "DRAWINGS"),
                os.path.join(project_folder, "2-PART TECHNICAL INFO"),  # Potser sense subdirectori
                project_folder  # Últim recurs, la carpeta del projecte directament
            ]
            
            # Provar cada opció
            for path in drawing_path_options:
                if os.path.exists(path):
                    logger.debug(f"Path de dibuixos trobat: {path}")
                    
                    # Llista tots els arxius/directoris en aquesta carpeta per depuració
                    try:
                        contents = os.listdir(path)
                        logger.debug(f"Contingut de la carpeta de dibuixos: {contents}")
                    except Exception as e:
                        logger.warning(f"No s'ha pogut llistar el contingut de {path}: {e}")
                        
                    return path
            
            logger.warning(f"Cap de les rutes de dibuixos existeix per al projecte {self.project_id}")
            return None
            
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
        
        if not pdf_files:
            logger.warning("No hi ha PDFs per guardar")
            return 0
            
        logger.info(f"Intentant guardar {len(pdf_files)} PDFs a la base de dades")
        
        try:
            # Connectar a la base de dades
            logger.debug(f"Utilitzant configuració DB de {self.db_config_path}")
            if not os.path.exists(self.db_config_path):
                logger.error(f"El fitxer de configuració de la base de dades no existeix: {self.db_config_path}")
                return 0
                
            with open(self.db_config_path, encoding='utf-8') as f:
                db_configs = json.load(f)
            
            db_config = db_configs.get("primary", {})
            logger.debug(f"Configuració de DB carregada: {db_config.keys()}")
            
            conn = PostgresConn(**db_config)
            logger.debug("Connexió a PostgreSQL establerta correctament")
            
            # Verificar que la taula existeix
            check_table_query = """
            SELECT EXISTS (
               SELECT FROM information_schema.tables 
               WHERE table_name = 'planol'
            );
            """
            table_exists = conn.fetchone(check_table_query)
            if not table_exists or not table_exists[0]:
                logger.error("La taula 'planol' no existeix a la base de dades")
                return 0
                
            logger.debug("La taula 'planol' existeix, procedint a guardar PDFs")
            
            # IMPORTANT: Verificar i crear entrada a la taula 'peca' si no existeix
            self._ensure_peca_reference_exists(conn)
            
            for pdf_info in pdf_files:
                try:
                    drawing_number = pdf_info['drawing_number']
                    logger.debug(f"Processant PDF {pdf_info['filename']} amb num_planol={drawing_number}")
                    
                    # Verificar si aquest plànol ja existeix
                    check_query = "SELECT COUNT(*) FROM planol WHERE num_planol = %s"
                    result = conn.fetchone(check_query, (drawing_number,))
                    already_exists = result and result[0] > 0
                    
                    if already_exists:
                        logger.debug(f"El plànol amb num_planol={drawing_number} ja existeix, s'actualitzarà")
                    else:
                        logger.debug(f"El plànol amb num_planol={drawing_number} és nou, s'inserirà")
                    
                    # Convertir PDF a base64 per guardar-lo
                    pdf_base64 = base64.b64encode(pdf_info['pdf_data']).decode('utf-8')
                    
                    # Crear estructura JSON similar a la que s'usa actualment
                    pdf_json = {
                        'filename': pdf_info['filename'],
                        'drawing_number': drawing_number,
                        'version': pdf_info['version'],
                        'file_size': pdf_info['file_size'],
                        'pdf_data': pdf_base64
                    }
                    
                    # Neteja i guarda el drawing_number original per a referència
                    original_drawing_number = drawing_number
                    # Neteja el drawing_number per evitar caràcters no vàlids
                    drawing_number = drawing_number.replace(' ', '_').replace('-', '_')
                    
                    # Per mantenir compatibilitat amb el sistema de cerca existent:
                    # La consulta busca num_planol que comenci amb project_prefix (primeres 3 xifres)
                    # Mantenim el drawing_number original però assegurem que sigui únic i compatible
                    
                    project_prefix = self.project_id[:3] if len(self.project_id) >= 3 else self.project_id
                    
                    # Format optimitzat per compatibilitat: {project_prefix}{drawing_number_net}
                    # Això assegura que la cerca per LIKE 'project_prefix%' funcioni
                    if drawing_number.startswith(project_prefix):
                        # Si ja comença amb el prefix, l'utilitzem directament
                        unique_drawing_number = drawing_number
                    else:
                        # Si no comença amb el prefix, l'afegim
                        unique_drawing_number = f"{project_prefix}{drawing_number}"
                    
                    # Afegim un sufix per evitar col·lisions entre clients només si és necessari
                    # Per exemple, si dos clients tenen el mateix drawing_number
                    if self.client_name.upper() != 'AUTOLIV':  # AUTOLIV funciona sense sufix
                        # Però només afegim el sufix si no faria massa llarg el nom
                        potential_suffix = f"_{self.client_name.upper()}"
                        if len(unique_drawing_number + potential_suffix) <= 100:
                            unique_drawing_number += potential_suffix
                    
                    logger.debug(f"Drawing number per a cerca optimitzada: original={original_drawing_number}, final={unique_drawing_number}, project_prefix={project_prefix}")
                    
                    # Assegura que no excedeix la mida de la columna
                    if len(unique_drawing_number) > 100:
                        unique_drawing_number = unique_drawing_number[:100]
                        logger.warning(f"Drawing number truncat: {unique_drawing_number}")
                    
                    drawing_number = unique_drawing_number
                    
                    # Insertar o actualitzar a la taula planol
                    try:
                        # Primer, analitzem l'estructura de la taula
                        table_info_query = """
                        SELECT column_name, data_type, character_maximum_length
                        FROM information_schema.columns
                        WHERE table_name = 'planol'
                        """
                        table_info = conn.fetchall(table_info_query)
                        logger.debug(f"Estructura de la taula 'planol': {table_info}")
                        
                        # Llistem els plànols existents per al debug
                        list_existing_query = "SELECT id_referencia_client, num_planol FROM planol LIMIT 5"
                        existing_samples = conn.fetchall(list_existing_query)
                        logger.debug(f"Exemples de plànols existents: {existing_samples}")
                        
                        # Comprovem si el id_referencia_client ja existeix
                        check_ref_query = "SELECT COUNT(*) FROM planol WHERE id_referencia_client = %s"
                        ref_result = conn.fetchone(check_ref_query, (self.project_id,))
                        ref_exists = ref_result and ref_result[0] > 0
                        logger.debug(f"Referència client '{self.project_id}' existeix a la base de dades: {ref_exists}")
                        
                        # Comprovem si el num_planol ja existeix
                        check_exists_query = "SELECT COUNT(*) FROM planol WHERE num_planol = %s"
                        exists_result = conn.fetchone(check_exists_query, (drawing_number,))
                        already_exists = exists_result and exists_result[0] > 0
                        logger.debug(f"Plànol '{drawing_number}' existeix a la base de dades: {already_exists}")
                        
                        # Preparem el JSON pel plànol
                        json_str = json.dumps(pdf_json)
                        logger.debug(f"Longitud del JSON: {len(json_str)} bytes")
                        
                        if already_exists:
                            # Si ja existeix, actualitzem
                            update_query = """
                            UPDATE planol 
                            SET imatge = %s, id_referencia_client = %s
                            WHERE num_planol = %s
                            """
                            update_params = (
                                json_str,
                                self.project_id,
                                drawing_number
                            )
                            logger.debug(f"Executant UPDATE: query={update_query}, params={update_params}")
                            conn.execute(update_query, update_params, commit=True)
                            logger.info(f"PDF actualitzat: {pdf_info['filename']} (dibuix: {drawing_number})")
                        else:
                            # Si no existeix, insertem
                            insert_query = """
                            INSERT INTO planol (id_referencia_client, num_planol, imatge)
                            VALUES (%s, %s, %s)
                            """
                            insert_params = (
                                self.project_id,
                                drawing_number,
                                json_str
                            )
                            logger.debug(f"Executant INSERT: query={insert_query}, params={self.project_id}, {drawing_number}, [JSON de {len(json_str)} bytes]")
                            conn.execute(insert_query, insert_params, commit=True)
                            logger.info(f"PDF inserit: {pdf_info['filename']} (dibuix: {drawing_number})")
                            
                            # Verifiquem que s'ha inserit correctament
                            verify_query = "SELECT COUNT(*) FROM planol WHERE num_planol = %s"
                            verify_result = conn.fetchone(verify_query, (drawing_number,))
                            verify_exists = verify_result and verify_result[0] > 0
                            logger.debug(f"Verificació després d'INSERT: plànol '{drawing_number}' existeix: {verify_exists}")
                        
                        saved_count += 1
                        
                    except Exception as db_error:
                        logger.error(f"Error en l'operació de base de dades: {str(db_error)}", exc_info=True)
                        
                        # Si hi ha error de clau forana, podria ser que no existeixi l'entrada a 'peca'
                        if "foreign key" in str(db_error).lower() or "fk_id_referencia_client" in str(db_error):
                            logger.debug("Error de clau forana detectat - possiblement manca entrada a taula 'peca'")
                            
                            # Fem rollback de la transacció actual
                            try:
                                conn.connection.rollback()
                                logger.debug("Rollback de transacció realitzat")
                            except:
                                pass
                            
                            # Intentem crear l'entrada a 'peca' i després reintentar
                            if self._ensure_peca_reference_exists(conn):
                                logger.debug("Entrada creada a 'peca', reintentant inserció del plànol")
                                try:
                                    if already_exists:
                                        update_query = """
                                        UPDATE planol 
                                        SET imatge = %s, id_referencia_client = %s
                                        WHERE num_planol = %s
                                        """
                                        update_params = (json_str, self.project_id, drawing_number)
                                        conn.execute(update_query, update_params, commit=True)
                                        logger.info(f"PDF actualitzat després de crear 'peca': {pdf_info['filename']}")
                                    else:
                                        insert_query = """
                                        INSERT INTO planol (id_referencia_client, num_planol, imatge)
                                        VALUES (%s, %s, %s)
                                        """
                                        insert_params = (self.project_id, drawing_number, json_str)
                                        conn.execute(insert_query, insert_params, commit=True)
                                        logger.info(f"PDF inserit després de crear 'peca': {pdf_info['filename']}")
                                    
                                    saved_count += 1
                                    continue  # Passa al següent PDF
                                    
                                except Exception as retry_error:
                                    logger.error(f"Error reintentant després de crear 'peca': {str(retry_error)}")
                            else:
                                logger.error("No s'ha pogut crear l'entrada a 'peca'")
                        
                        # Per a qualsevol altre error, fem rollback i intentem estratègies alternatives
                        try:
                            conn.connection.rollback()
                            logger.debug("Rollback realitzat per error general")
                        except:
                            pass
                        
                        # Log dels tipus d'error per diagnòstic
                        error_str = str(db_error).lower()
                        if "unique" in error_str or "duplicate" in error_str:
                            logger.debug("Error detectat: restricció de clau única/duplicada")
                        elif "null" in error_str:
                            logger.debug("Error detectat: restricció de no-nul")
                        
                        logger.warning(f"No s'ha pogut guardar el PDF {pdf_info['filename']} a la base de dades")
                    
                except Exception as e:
                    logger.error(f"Error guardant PDF {pdf_info['filename']}: {str(e)}", exc_info=True)
            
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
    
    def _ensure_peca_reference_exists(self, conn):
        """
        Assegura que existeixi una entrada a la taula 'peca' per a id_referencia_client
        abans d'intentar inserir plànols
        """
        try:
            # Comprovar si la referència ja existeix a la taula 'peca'
            check_peca_query = "SELECT COUNT(*) FROM peca WHERE id_referencia_client = %s"
            peca_result = conn.fetchone(check_peca_query, (self.project_id,))
            peca_exists = peca_result and peca_result[0] > 0
            
            if peca_exists:
                logger.debug(f"La referència '{self.project_id}' ja existeix a la taula 'peca'")
                return True
                
            logger.info(f"La referència '{self.project_id}' no existeix a la taula 'peca', creant-la...")
            
            # Intent amb només l'id_referencia_client (camp mínim necessari)
            try:
                logger.debug("Intentant crear entrada mínima a 'peca' amb només id_referencia_client")
                minimal_peca_query = "INSERT INTO peca (id_referencia_client) VALUES (%s)"
                conn.execute(minimal_peca_query, (self.project_id,), commit=True)
                logger.info(f"Entrada mínima creada a 'peca' per a '{self.project_id}'")
                
                # Verificar que s'ha creat correctament
                verify_peca_query = "SELECT COUNT(*) FROM peca WHERE id_referencia_client = %s"
                verify_result = conn.fetchone(verify_peca_query, (self.project_id,))
                verify_exists = verify_result and verify_result[0] > 0
                
                if verify_exists:
                    logger.info(f"Entrada verificada correctament a la taula 'peca' per a '{self.project_id}'")
                    return True
                else:
                    logger.error(f"No s'ha pogut verificar la creació de l'entrada a 'peca' per a '{self.project_id}'")
                    return False
                    
            except Exception as minimal_error:
                logger.error(f"Error en la creació mínima a 'peca': {str(minimal_error)}", exc_info=True)
                
                # Últim intent: obtenim l'estructura de la taula i intentem amb més camps
                try:
                    logger.debug("Obtenint estructura de la taula 'peca' per a inserció més completa")
                    peca_structure_query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'peca'
                    ORDER BY ordinal_position
                    """
                    peca_structure = conn.fetchall(peca_structure_query)
                    logger.debug(f"Estructura de la taula 'peca': {peca_structure}")
                    
                    # Intentem inserir amb valors per defecte per a tots els camps obligatoris
                    columns = ['id_referencia_client']
                    values = [self.project_id]
                    placeholders = ['%s']
                    
                    for column_name, data_type, is_nullable, column_default in peca_structure:
                        if column_name != 'id_referencia_client' and is_nullable == 'NO' and column_default is None:
                            # Aquest camp és obligatori i no té valor per defecte
                            if 'varchar' in data_type or 'text' in data_type:
                                columns.append(column_name)
                                values.append(f"Auto-generat per {self.client_name}")
                                placeholders.append('%s')
                            elif 'int' in data_type or 'numeric' in data_type:
                                columns.append(column_name)
                                values.append(0)
                                placeholders.append('%s')
                            elif 'timestamp' in data_type or 'date' in data_type:
                                columns.append(column_name)
                                placeholders.append('NOW()')
                    
                    complete_insert_query = f"""
                    INSERT INTO peca ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    """
                    
                    logger.debug(f"Executant INSERT complet a 'peca': {complete_insert_query}")
                    logger.debug(f"Paràmetres: {values}")
                    
                    conn.execute(complete_insert_query, values, commit=True)
                    logger.info(f"Entrada completa creada a 'peca' per a '{self.project_id}'")
                    return True
                    
                except Exception as complete_error:
                    logger.error(f"També ha fallat la inserció completa a 'peca': {str(complete_error)}", exc_info=True)
                    return False
                
        except Exception as e:
            logger.error(f"Error general creant entrada a la taula 'peca': {str(e)}", exc_info=True)
            return False
