@echo off
REM Script d'instal·lació per Windows - PythonTecnica_SOME amb Docker

echo.
echo ========================================
echo   INSTAL·LACIO PYTHONTECNICA_SOME
echo         amb Docker per Windows  
echo ========================================
echo.

REM Verificar si Docker està instal·lat
echo Verificant Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker no està instal·lat!
    echo.
    echo Per favor, instal·la Docker Desktop des de:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose no està disponible!
    echo Per favor, assegura't que Docker Desktop estigui actualitzat.
    pause
    exit /b 1
)

echo ✅ Docker està instal·lat correctament
echo.

REM Crear arxiu d'entorn si no existeix
if not exist .env (
    echo Creant arxiu de configuració...
    echo POSTGRES_PASSWORD=pythontecnica_secure_pass > .env
    echo ✅ Arxiu .env creat
) else (
    echo ✅ Arxiu .env ja existeix
)

echo.
echo Construint i iniciant els serveis...
echo Això pot trigar uns minuts la primera vegada...
echo.

REM Construir i iniciar els serveis
docker-compose up --build -d

if %errorlevel% neq 0 (
    echo ❌ Error durant la construcció o inici dels serveis
    pause
    exit /b 1
)

echo.
echo ✅ Instal·lació completada!
echo.
echo 📋 INFORMACIÓ DELS SERVEIS:
echo    - Aplicació: http://localhost:8080
echo    - Base de dades PostgreSQL: localhost:5432
echo    - Usuari BD: pythontecnica_user
echo.
echo 🛠️ COMANDES ÚTILS:
echo    - Veure logs: docker-compose logs -f
echo    - Parar serveis: docker-compose down
echo    - Reiniciar: docker-compose restart
echo.
echo L'aplicació s'està iniciant...
echo Comprova els logs amb: docker-compose logs -f pythontecnica_app
echo.

timeout /t 5 /nobreak >nul

REM Mostrar logs de l'aplicació
echo Mostrant logs de l'aplicació:
docker-compose logs --tail=20 pythontecnica_app

echo.
echo Prem qualsevol tecla per sortir...
pause >nul