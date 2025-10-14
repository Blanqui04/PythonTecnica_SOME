@echo off
echo ===============================================
echo    CREACIO FORK ESTABLE - PythonTecnica SOME
echo ===============================================
echo.

echo Aquest script us ajudara a crear el fork estable step by step
echo.

echo PASSOS A SEGUIR:
echo.
echo 1. PREPARAR REPOSITORI LOCAL
echo ==============================
echo.

set /p confirm1="Voleu netejar fitxers temporals i preparar el repositori? (S/N): "
if /i "%confirm1%"=="S" (
    echo Executant preparacio...
    call PREPARE_STABLE_FORK.bat
    echo.
    echo [OK] Repositori preparat localment
) else (
    echo Saltant preparacio local...
)

echo.
echo 2. INSTRUCCIONS PER CREAR EL FORK A GITHUB
echo ==========================================
echo.
echo A. Aneu a: https://github.com/Blanqui04/PythonTecnica_SOME
echo B. Cliqueu "Fork" a la part superior dreta
echo C. Nom del fork: "PythonTecnica-SOME-Stable"
echo D. Descripció: "Versió estable d'instal·lació de PythonTecnica SOME"
echo E. Assegureu-vos que sigui PUBLIC
echo F. Cliqueu "Create fork"
echo.

set /p confirm2="Heu creat el fork a GitHub? (S/N): "
if /i not "%confirm2%"=="S" (
    echo.
    echo Per favor, creeu primer el fork a GitHub i torneu a executar aquest script
    pause
    exit /b 1
)

echo.
echo 3. CONFIGURAR REMOT I PUJAR CANVIS
echo ==================================
echo.

set /p fork_url="Introduïu la URL del vostre fork (ex: https://github.com/USUARI/PythonTecnica-SOME-Stable.git): "

echo.
echo Configurant remot del fork...
git remote add stable-fork %fork_url% 2>nul
if errorlevel 1 (
    echo Actualitzant URL del remot existent...
    git remote set-url stable-fork %fork_url%
)

echo.
echo Creant branca estable...
git checkout -b stable-install 2>nul
if errorlevel 1 (
    echo Branca ja existeix, canviant a ella...
    git checkout stable-install
)

echo.
echo Afegint tots els fitxers...
git add .

echo.
echo Fent commit de la versio estable...
git commit -m "🚀 Versió estable 1.0 - Fork d'instal·lació automàtica

- Scripts d'instal·lació automàtica (SETUP.bat, RUN_APP.bat)
- Dependències fixes i testejades
- Documentació d'instal·lació completa
- Entorn virtual auto-configurable
- Versió preparada per distribució"

echo.
echo Pujant al fork estable...
git push stable-fork stable-install

echo.
echo 4. CREAR RELEASE ESTABLE
echo ========================
echo.
echo A. Aneu al vostre fork: %fork_url%
echo B. Cliqueu "Releases" - "Create a new release"
echo C. Tag version: "v1.0.0-stable"
echo D. Release title: "Versió Estable 1.0 - Instal·lació Automàtica"
echo E. Descripció:
echo.
echo --- COPIEU AIXO ---
echo 🚀 Primera versió estable de PythonTecnica SOME
echo.
echo ✅ Instal·lació automàtica amb scripts .bat
echo ✅ Dependències fixes i testejades  
echo ✅ Entorn virtual auto-configurable
echo ✅ Documentació completa d'instal·lació
echo ✅ Suport tècnic inclòs
echo.
echo 📦 **Instal·lació ultra-ràpida:**
echo 1. Descarregar ZIP o clonar repositori
echo 2. Executar SETUP.bat
echo 3. Executar RUN_APP.bat
echo.
echo 🎯 **Per a:** Usuaris finals i entorns de producció
echo --- FI COPIA ---
echo.
echo F. Marqueu "This is a pre-release" si és una beta
echo G. Cliqueu "Publish release"
echo.

echo ===============================================
echo    FORK ESTABLE CREAT CORRECTAMENT!
echo ===============================================
echo.
echo El vostre fork estable esta disponible a:
echo %fork_url%
echo.
echo Els usuaris ja poden:
echo 1. Clonar/descarregar el fork
echo 2. Executar SETUP.bat
echo 3. Executar RUN_APP.bat
echo.
pause