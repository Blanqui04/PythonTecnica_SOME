#!/bin/bash
# Script d'instal·lació per Linux/macOS - PythonTecnica_SOME amb Docker

echo ""
echo "========================================"
echo "   INSTAL·LACIÓ PYTHONTECNICA_SOME"
echo "        amb Docker per Linux/macOS"  
echo "========================================"
echo ""

# Verificar si Docker està instal·lat
echo "Verificant Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no està instal·lat!"
    echo ""
    echo "Per Ubuntu/Debian:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    echo ""
    echo "Per altres distribucions, visita:"
    echo "  https://docs.docker.com/engine/install/"
    echo ""
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no està instal·lat!"
    echo ""
    echo "Instal·la Docker Compose:"
    echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    echo "  sudo chmod +x /usr/local/bin/docker-compose"
    echo ""
    exit 1
fi

echo "✅ Docker està instal·lat correctament"
echo ""

# Verificar que Docker estigui funcionant
if ! docker info &> /dev/null; then
    echo "❌ Docker no està funcionant!"
    echo "Prova iniciar el servei:"
    echo "  sudo systemctl start docker"
    echo "  sudo systemctl enable docker"
    echo ""
    exit 1
fi

# Crear arxiu d'entorn si no existeix
if [ ! -f .env ]; then
    echo "Creant arxiu de configuració..."
    echo "POSTGRES_PASSWORD=pythontecnica_secure_pass" > .env
    echo "✅ Arxiu .env creat"
else
    echo "✅ Arxiu .env ja existeix"
fi

# Configurar X11 per GUI (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Configurant X11 per GUI..."
    xhost +local:docker 2>/dev/null || echo "⚠️  No es pot configurar X11 (GUI pot no funcionar)"
fi

echo ""
echo "Construint i iniciant els serveis..."
echo "Això pot trigar uns minuts la primera vegada..."
echo ""

# Construir i iniciar els serveis
if ! docker-compose up --build -d; then
    echo "❌ Error durant la construcció o inici dels serveis"
    exit 1
fi

echo ""
echo "✅ Instal·lació completada!"
echo ""
echo "📋 INFORMACIÓ DELS SERVEIS:"
echo "   - Aplicació: http://localhost:8080"
echo "   - Base de dades PostgreSQL: localhost:5432"
echo "   - Usuari BD: pythontecnica_user"
echo ""
echo "🛠️ COMANDES ÚTILS:"
echo "   - Veure logs: docker-compose logs -f"
echo "   - Parar serveis: docker-compose down"
echo "   - Reiniciar: docker-compose restart"
echo ""
echo "L'aplicació s'està iniciant..."
echo "Comprova els logs amb: docker-compose logs -f pythontecnica_app"
echo ""

sleep 3

# Mostrar logs de l'aplicació
echo "Mostrant logs de l'aplicació:"
docker-compose logs --tail=20 pythontecnica_app

echo ""
echo "Instal·lació completada! Prem Ctrl+C per sortir del visor de logs."