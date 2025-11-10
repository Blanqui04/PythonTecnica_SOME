# Guia de Release - PythonTecnica SOME

## 📦 Com crear un paquet de distribució

### 1. Preparació

Assegura't que tens tot actualitzat:

```bash
# Activar entorn virtual
venv\Scripts\activate

# Instal·lar/actualitzar dependències
pip install -r config/requirements.txt
pip install pyinstaller
```

### 2. Construir el paquet

```bash
# Executar script de build
build_release.bat
```

Aquest script farà:
- ✅ Compilar l'aplicació amb PyInstaller
- ✅ Crear estructura de distribució
- ✅ Generar README i script d'instal·lació
- ✅ Crear arxiu ZIP llest per distribuir

### 3. Resultat

Trobaràs el paquet a:
```
release/PythonTecnica_SOME_v2.0.0.zip
```

Contingut del ZIP:
```
PythonTecnica_SOME_v2.0.0/
├── PythonTecnica_SOME/          # Aplicació compilada
│   ├── PythonTecnica_SOME.exe   # Executable principal
│   ├── config/                  # Configuració
│   ├── assets/                  # Recursos
│   ├── i18n/                    # Traduccions
│   └── [llibreries]             # Dependencies
├── README.txt                   # Instruccions per l'usuari
└── INSTALAR.bat                 # Script d'actualització
```

## 🚀 Publicar a GitHub Release

### Opció A: Via Web UI

1. Ves a: https://github.com/Blanqui04/PythonTecnica_SOME/releases
2. Clica **"Draft a new release"**
3. Configura:
   - **Tag version:** v2.0.0
   - **Release title:** PythonTecnica SOME v2.0.0 - Estudis de Capacitat
   - **Description:**
     ```markdown
     ## 🎉 Novetats v2.0.0
     
     ### ✨ Funcionalitats noves
     - Mòdul d'estudis de capacitat implementat
     - Auto-detecció de schema 'qualitat'
     - Millores en rendiment de queries amb UNION
     
     ### 🐛 Correccions
     - Resolt bug de connexió a base de dades
     - Millores en gestió d'errors
     
     ### 📊 Dades
     - Suport per 1.15M+ registres de mesures
     - Integració amb Airflow ETL
     
     ## 📥 Instal·lació
     
     1. Descarrega `PythonTecnica_SOME_v2.0.0.zip`
     2. Descomprimeix l'arxiu
     3. Executa `INSTALAR.bat`
     4. Segueix les instruccions a pantalla
     
     ## ⚙️ Requisits
     - Windows 10/11
     - Connexió a PostgreSQL (172.26.11.201)
     
     ## 🔄 Actualització des de v1.x
     L'script `INSTALAR.bat` detectarà automàticament la versió anterior
     i preservarà la teva configuració.
     ```
4. Arrossega el fitxer `PythonTecnica_SOME_v2.0.0.zip`
5. Marca **"Set as the latest release"**
6. Clica **"Publish release"**

### Opció B: Via Git + GitHub CLI

```bash
# Crear tag
git tag -a v2.0.0 -m "Release v2.0.0 - Estudis de Capacitat"
git push origin v2.0.0

# Crear release amb GitHub CLI
gh release create v2.0.0 ^
    release/PythonTecnica_SOME_v2.0.0.zip ^
    --title "PythonTecnica SOME v2.0.0 - Estudis de Capacitat" ^
    --notes-file RELEASE_NOTES.md
```

## 👥 Distribució als usuaris

### Per actualitzar instal·lacions existents:

Envia als usuaris:
1. Link del release: https://github.com/Blanqui04/PythonTecnica_SOME/releases/latest
2. Instruccions:
   ```
   1. Descarrega PythonTecnica_SOME_v2.0.0.zip
   2. Descomprimeix
   3. Executa INSTALAR.bat
   4. L'script detectarà la versió anterior i actualitzarà
   ```

### Per instal·lacions noves:

```
1. Descarrega PythonTecnica_SOME_v2.0.0.zip
2. Descomprimeix a la carpeta desitjada
3. Executa PythonTecnica_SOME.exe
```

## 🔧 Solució de problemes

### Error: "Missing dependencies"
```bash
# Reconstruir amb totes les dependencies
pip install --upgrade -r config/requirements.txt
build_release.bat
```

### Error: "PyInstaller not found"
```bash
pip install pyinstaller
```

### L'executable no inicia
- Verifica que l'antivirus no bloqueja l'executable
- Executa com a administrador
- Comprova logs a: `%LOCALAPPDATA%\PythonTecnica_SOME\logs\`

## 📋 Checklist abans de publicar

- [ ] Tests passen (5/5)
- [ ] Versió actualitzada a `build_release.bat`
- [ ] README.txt actualitzat amb novetats
- [ ] Compilació exitosa
- [ ] Prova local de l'executable
- [ ] Prova script INSTALAR.bat
- [ ] Commit i push de canvis
- [ ] Tag creat
- [ ] Release publicat a GitHub
- [ ] Notificar usuaris

## 🎯 Versionat

Seguim **Semantic Versioning** (semver.org):

- **MAJOR** (2.x.x): Canvis incompatibles
- **MINOR** (x.1.x): Funcionalitats noves compatibles
- **PATCH** (x.x.1): Correccions de bugs

Exemples:
- `2.0.0` - Primera versió amb estudis de capacitat (MAJOR)
- `2.1.0` - Afegir nou tipus de gràfic (MINOR)
- `2.0.1` - Corregir bug en càlcul Cp (PATCH)

---

**Llest per crear el teu primer release!** 🚀
