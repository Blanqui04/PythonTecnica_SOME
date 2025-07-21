# Guia Completa de Deployment - PythonTecnica_SOME

## Resum Executiu
Aquest document explica com fer el deployment de l'aplicació PythonTecnica_SOME a l'empresa, assegurant que tots els PCs tinguin accés a les últimes actualitzacions i connexió automàtica a la base de dades.

## Arquitectura del Sistema

### Components del Deployment
1. **Aplicació Principal**: Executable standalone amb PyQt5
2. **Sistema d'Actualitzacions**: Comprova automàticament noves versions
3. **Configuració Empresarial**: Connexió automàtica a la BBDD
4. **Servidor d'Actualitzacions**: Servidor intern per distribuir updates

## Procés de Deployment

### Pas 1: Preparar l'Aplicació per al Build

```bash
# 1. Navegar al directori del projecte
cd C:\Github\PythonTecnica_SOME\PythonTecnica_SOME

# 2. Executar el build
build.bat
```

### Pas 2: Configurar Servidor d'Actualitzacions (Opcional però Recomanat)

1. **Escollir un servidor intern** (exemple: 172.26.5.200)
2. **Instal·lar Python i Flask**:
   ```bash
   pip install flask
   ```
3. **Copiar i executar el servidor**:
   ```bash
   python deployment/server_setup.py
   ```
4. **Configurar URL del servidor** a `auto_updater.py`:
   ```python
   update_server_url = "http://172.26.5.200:8080/updates"
   ```

### Pas 3: Distribució a l'Empresa

#### Opció A: Instal·lació Manual per PC
1. Copiar la carpeta `deployment_package` a cada PC
2. Executar `install.bat` com a administrador
3. L'aplicació s'instal·la automàticament

#### Opció B: Deployment Centralitzat (Recomanat)
1. **Pujar a servidor compartit**:
   ```
   \\servidor-empresa\software\PythonTecnica_SOME\
   ```

2. **Crear script de deployment en xarxa**:
   ```batch
   @echo off
   echo Instal·lant PythonTecnica_SOME des del servidor...
   
   REM Copiar fitxers localment
   xcopy "\\servidor-empresa\software\PythonTecnica_SOME\*" "C:\temp\pythontecnica\" /s /e /y
   
   REM Executar instal·lació
   cd "C:\temp\pythontecnica\"
   install.bat
   
   REM Neteja
   rmdir "C:\temp\pythontecnica\" /s /q
   ```

3. **Distribuir via GPO (Group Policy)**:
   - Configurar com a script de startup
   - O crear paquet MSI personalitzat

## Configuració Automàtica

### Connexió a la Base de Dades
L'aplicació es configura automàticament amb:
- **Host**: 172.26.5.159
- **Port**: 5433
- **Database**: documentacio_tecnica
- **User**: administrador
- **Password**: Some2025.!$%

### Variables d'Entorn Empresarials
```
APP_ENV=production
DB_AUTO_CONNECT=true
UPDATE_CHECK_INTERVAL=3600
COMPANY_NAME=SOME
```

## Sistema d'Actualitzacions

### Funcionament Automàtic
- Comprova actualitzacions cada hora
- Descarrega automàticament si n'hi ha
- Notifica a l'usuari abans d'aplicar
- Reinicia l'aplicació si cal

### Gestió d'Actualitzacions
1. **Crear nova versió**:
   ```bash
   python deployment/build_and_deploy.py --update --version=1.1.0
   ```

2. **Pujar al servidor**:
   ```bash
   # Copiar update_v1.1.0.zip i version.json al servidor
   ```

3. **Distribució automàtica**: Els clients comproven i actualitzen automàticament

## Monitoratge i Manteniment

### Logs de l'Aplicació
- **Ubicació**: `C:\Program Files\SOME\PythonTecnica_SOME\logs\`
- **Fitxers**:
  - `app.log`: Log general de l'aplicació
  - `updates.log`: Log d'actualitzacions
  - `db.log`: Log de connexions a BBDD

### Verificació del Sistema
```python
# Script per verificar instal·lació
python -c "
import sys
sys.path.append('C:\\Program Files\\SOME\\PythonTecnica_SOME')
from deployment.config_manager import ConfigManager
cm = ConfigManager()
print('Config OK:', cm.verify_config())
"
```

## Troubleshooting

### Problemes Comuns

1. **Error de connexió a BBDD**:
   - Verificar connectivitat de xarxa
   - Comprovar credencials a `config/database/db_config.json`

2. **Actualitzacions no funcionen**:
   - Verificar accés al servidor d'actualitzacions
   - Comprovar logs a `logs/updates.log`

3. **Aplicació no s'inicia**:
   - Verificar que Python està instal·lat
   - Comprovar dependències amb `pip list`

### Scripts de Diagnòstic
```batch
REM diagnostic.bat
@echo off
echo Diagnostic PythonTecnica_SOME...

echo Checking Python...
python --version

echo Checking application...
python "C:\Program Files\SOME\PythonTecnica_SOME\main_app.py" --check

echo Checking database connection...
python -c "from src.database.database_connection import test_connection; test_connection()"

echo Checking updates...
python "C:\Program Files\SOME\PythonTecnica_SOME\deployment\check_updates.py"
```

## Seguretat

### Mesures Implementades
- Connexions segures a la BBDD
- Verificació de checksums per actualitzacions
- Logs d'auditoria
- Configuració només de lectura per usuaris

### Recomanacions
- Configurar firewall per permetre només connexions internes
- Usar HTTPS per al servidor d'actualitzacions en producció
- Implementar autenticació per pujar actualitzacions

## Escalabilitat

### Per a més de 50 PCs
1. **Servidor d'actualitzacions dedicat**
2. **CDN intern** per distribuir actualitzacions
3. **Base de dades de telemetria** per monitorar ús

### Automatització Avançada
1. **CI/CD Pipeline**:
   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy PythonTecnica_SOME
   on:
     push:
       tags: ['v*']
   jobs:
     build:
       runs-on: windows-latest
       steps:
         - uses: actions/checkout@v3
         - run: python deployment/build_and_deploy.py --update --version=${{ github.ref_name }}
   ```

2. **Monitoratge centralizat** amb Elasticsearch/Kibana

## Contacte i Suport
- **Equip IT**: it@some.com
- **Documentació**: http://intranet.some.com/pythontecnica
- **Incidències**: Portal intern IT

---

**Data**: 21 de juliol de 2025  
**Versió del document**: 1.0  
**Autor**: Equip de Desenvolupament PythonTecnica_SOME
