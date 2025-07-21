# INSTRUCCIONS COMPLETES PER AL DEPLOYMENT - PythonTecnica_SOME

## 🚀 DEPLOYMENT EMPRESARIAL COMPLET

Aquesta guia et permetrà fer el deployment de l'aplicació PythonTecnica_SOME a tots els PCs de l'empresa amb actualitzacions automàtiques i connexió automàtica a la BBDD.

## 📋 RESUM DE LO QUE HEM CREAT

S'han creat els següents components per al deployment:

### 1. Sistema de Build Automàtic
- `deployment/build_and_deploy.py`: Script principal per construir l'aplicació
- `deployment/setup.py`: Configuració per cx_Freeze
- `build.bat`: Script Windows per executar el build

### 2. Sistema d'Actualitzacions Automàtiques  
- `deployment/auto_updater.py`: Gestió d'actualitzacions automàtiques
- `deployment/check_updates.py`: Script per comprovar actualitzacions
- `deployment/server_setup.py`: Servidor d'actualitzacions intern

### 3. Configuració Empresarial
- `deployment/config_manager.py`: Configuració automàtica per a l'empresa
- `deployment/enterprise_installer.py`: Instal·lador empresarial
- Configuració automàtica de BBDD (172.26.5.159:5433)

## 🛠️ PROCÉS DE DEPLOYMENT PAS A PAS

### FASE 1: PREPARAR EL BUILD

1. **Instal·lar dependències de build:**
```cmd
pip install pyinstaller cx-Freeze setuptools wheel
```

2. **Executar el build:**
```cmd
cd C:\Github\PythonTecnica_SOME\PythonTecnica_SOME
python deployment\build_and_deploy.py
```

Això crearà:
- `dist/PythonTecnica_SOME/`: Aplicació compilada
- `deployment_package/`: Paquet llest per distribuir

### FASE 2: CONFIGURAR SERVIDOR D'ACTUALITZACIONS (OPCIONAL)

Si vols actualitzacions automàtiques:

1. **Escollir un servidor de l'empresa** (ex: 172.26.5.200)

2. **Instal·lar Flask al servidor:**
```cmd
pip install flask
```

3. **Copiar i executar el servidor:**
```cmd
python deployment\server_setup.py
```

4. **Actualitzar URL a auto_updater.py:**
```python
update_server_url = "http://172.26.5.200:8080/updates"
```

### FASE 3: DISTRIBUCIÓ A L'EMPRESA

#### Opció A: Distribució Manual
1. Copiar `deployment_package/` a cada PC
2. Executar `install.bat` com a administrador
3. L'aplicació s'instal·la a `C:\Program Files\SOME\PythonTecnica_SOME\`

#### Opció B: Distribució de Xarxa (RECOMANAT)
1. Pujar `deployment_package/` a una carpeta compartida:
   ```
   \\servidor-empresa\software\PythonTecnica_SOME\
   ```

2. Crear script de deployment de xarxa:
```batch
@echo off
echo Instal·lant PythonTecnica_SOME...
robocopy "\\servidor-empresa\software\PythonTecnica_SOME" "C:\temp\pythontecnica" /s
cd "C:\temp\pythontecnica"
install.bat
rmdir "C:\temp\pythontecnica" /s /q
```

3. Distribuir via GPO o email

## ⚙️ CONFIGURACIÓ AUTOMÀTICA

### Connexió Automàtica a BBDD
L'aplicació es configura automàticament per connectar-se a:
- **Host**: 172.26.5.159
- **Port**: 5433  
- **Database**: documentacio_tecnica
- **Usuari**: administrador
- **Password**: Some2025.!$%

### Característiques del Deployment:
- ✅ Instal·lació automàtica a `C:\Program Files\SOME\PythonTecnica_SOME\`
- ✅ Accesos directes al menú d'inici i escriptori
- ✅ Connexió automàtica a la BBDD en arrancar
- ✅ Comprovació d'actualitzacions cada hora
- ✅ Aplicació d'actualitzacions automàtiques
- ✅ Logs detallats per troubleshooting

## 🔄 GESTIÓ D'ACTUALITZACIONS

### Crear Nova Versió:
```cmd
python deployment\build_and_deploy.py --update --version=1.1.0
```

### Pujar Nova Versió al Servidor:
1. Copiar `update_v1.1.0.zip` al servidor d'actualitzacions
2. Actualitzar `version.json`
3. Els clients actualitzaran automàticament

## 📊 MONITORATGE

### Logs Disponibles:
- `logs/app.log`: Log general de l'aplicació
- `logs/updates.log`: Log d'actualitzacions  
- `logs/db.log`: Log de connexions BBDD

### Verificar Instal·lació:
```cmd
dir "C:\Program Files\SOME\PythonTecnica_SOME"
```

## 🚨 TROUBLESHOOTING

### Problemes Comuns:

1. **"Python no trobat"**
   - Instal·lar Python des de python.org
   - Assegurar-se que està al PATH

2. **"Error de connexió BBDD"**
   - Verificar connectivitat: `ping 172.26.5.159`
   - Comprovar credencials a `config/database/db_config.json`

3. **"Actualitzacions no funcionen"**
   - Verificar accés al servidor d'actualitzacions
   - Comprovar `logs/updates.log`

### Script de Diagnòstic:
```cmd
REM Comprovar estat de l'aplicació
python "C:\Program Files\SOME\PythonTecnica_SOME\main_app.py" --check
```

## 🔐 SEGURETAT

- Connexions segures a la BBDD
- Verificació de checksums per actualitzacions
- Logs d'auditoria complets
- Accés restringit a configuració

## 📞 SUPORT

Per qualsevol problema:
- **Equip IT**: it@some.com
- **Logs**: `C:\Program Files\SOME\PythonTecnica_SOME\logs\`
- **Configuració**: `C:\Program Files\SOME\PythonTecnica_SOME\config\`

---

## 🎯 RESUM EXECUTIU PELS DIRECTIUS

**L'aplicació ara està preparada per:**
1. **Deployment automàtic** a tots els PCs de l'empresa
2. **Connexió automàtica** a la base de dades (172.26.5.159)
3. **Actualitzacions automàtiques** sense intervenció manual
4. **Instal·lació centralitzada** amb un sol clic
5. **Monitoratge complet** amb logs detallats

**Temps estimat de deployment:**
- Preparació: 30 minuts
- Instal·lació per PC: 5 minuts automàtics
- Configuració servidor actualitzacions: 15 minuts (opcional)

**Beneficis:**
- ✅ Tots els PCs sempre actualitzats
- ✅ Connexió BBDD sempre funcional  
- ✅ Zero manteniment manual
- ✅ Escalable a centenars de PCs
