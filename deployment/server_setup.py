# deployment/server_setup.py - Configuració del servidor d'actualitzacions
"""
Aquest script configura un servidor simple per gestionar actualitzacions.
Pots usar aquest servidor en un ordinador de la xarxa de l'empresa.
"""

from flask import Flask, jsonify, send_file, request
import os
import json
from pathlib import Path
import hashlib
from datetime import datetime

app = Flask(__name__)

# Configuració
UPDATES_DIR = Path("updates")
UPDATES_DIR.mkdir(exist_ok=True)

# Versió actual disponible
CURRENT_VERSION = "1.0.0"

@app.route('/version.json')
def get_version_info():
    """Retorna informació de la versió actual"""
    version_info = {
        "version": CURRENT_VERSION,
        "release_date": datetime.now().isoformat(),
        "download_url": f"http://{request.host}/download/{CURRENT_VERSION}",
        "release_notes": f"Actualització a la versió {CURRENT_VERSION}",
        "checksum": _get_update_checksum(CURRENT_VERSION)
    }
    return jsonify(version_info)

@app.route('/download/<version>')
def download_update(version):
    """Descarrega un paquet d'actualització"""
    update_file = UPDATES_DIR / f"update_v{version}.zip"
    
    if update_file.exists():
        return send_file(update_file, as_attachment=True)
    else:
        return jsonify({"error": "Version not found"}), 404

@app.route('/upload', methods=['POST'])
def upload_update():
    """Puja una nova actualització (només per administradors)"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    version = request.form.get('version')
    
    if not version:
        return jsonify({"error": "Version not provided"}), 400
    
    # Guardar fitxer d'actualització
    update_file = UPDATES_DIR / f"update_v{version}.zip"
    file.save(update_file)
    
    # Actualitzar versió actual
    global CURRENT_VERSION
    CURRENT_VERSION = version
    
    return jsonify({"message": f"Update {version} uploaded successfully"})

def _get_update_checksum(version):
    """Calcula checksum de l'actualització"""
    update_file = UPDATES_DIR / f"update_v{version}.zip"
    
    if update_file.exists():
        with open(update_file, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    return None

@app.route('/status')
def server_status():
    """Estat del servidor"""
    available_updates = list(UPDATES_DIR.glob("update_v*.zip"))
    
    return jsonify({
        "status": "running",
        "current_version": CURRENT_VERSION,
        "available_updates": [f.stem for f in available_updates],
        "server_time": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Starting PythonTecnica_SOME Update Server...")
    print(f"Updates directory: {UPDATES_DIR.absolute()}")
    print(f"Current version: {CURRENT_VERSION}")
    print()
    print("Endpoints available:")
    print("  GET  /version.json - Get current version info")
    print("  GET  /download/<version> - Download update")
    print("  POST /upload - Upload new update (admin)")
    print("  GET  /status - Server status")
    print()
    
    # Configurar per a xarxa local de l'empresa
    app.run(
        host='0.0.0.0',  # Accessible des de qualsevol IP
        port=8080,       # Port personalitzable
        debug=False      # Desactivar debug en producció
    )
