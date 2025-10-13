#!/bin/bash
# Scripts de gestió per Docker - PythonTecnica_SOME

# Colors per terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo ""
    echo "🐳 Gestor Docker per PythonTecnica_SOME"
    echo ""
    echo "Ús: ./docker-manager.sh [COMANDA]"
    echo ""
    echo "COMANDES DISPONIBLES:"
    echo "  start          - Iniciar tots els serveis"
    echo "  stop           - Parar tots els serveis"
    echo "  restart        - Reiniciar tots els serveis"
    echo "  logs           - Mostrar logs de l'aplicació"
    echo "  logs-db        - Mostrar logs de la base de dades"
    echo "  status         - Estat dels contenidors"
    echo "  build          - Reconstruir les imatges"
    echo "  clean          - Eliminar contenidors i imatges"
    echo "  backup         - Fer backup de la base de dades"
    echo "  shell          - Obrir shell dins del contenidor app"
    echo "  db-shell       - Obrir shell de PostgreSQL"
    echo "  update         - Actualitzar i reconstruir"
    echo "  help           - Mostrar aquesta ajuda"
    echo ""
}

check_docker() {
    if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker o Docker Compose no estan instal·lats!${NC}"
        exit 1
    fi
}

case "$1" in
    "start")
        echo -e "${BLUE}🚀 Iniciant serveis...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✅ Serveis iniciats!${NC}"
        ;;
    "stop")
        echo -e "${YELLOW}⏹️  Parant serveis...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Serveis aturats!${NC}"
        ;;
    "restart")
        echo -e "${YELLOW}🔄 Reiniciant serveis...${NC}"
        docker-compose restart
        echo -e "${GREEN}✅ Serveis reiniciats!${NC}"
        ;;
    "logs")
        echo -e "${BLUE}📋 Logs de l'aplicació:${NC}"
        docker-compose logs -f pythontecnica_app
        ;;
    "logs-db")
        echo -e "${BLUE}📋 Logs de la base de dades:${NC}"
        docker-compose logs -f postgres
        ;;
    "status")
        echo -e "${BLUE}📊 Estat dels contenidors:${NC}"
        docker-compose ps
        ;;
    "build")
        echo -e "${BLUE}🏗️  Reconstruint imatges...${NC}"
        docker-compose build --no-cache
        echo -e "${GREEN}✅ Imatges reconstruïdes!${NC}"
        ;;
    "clean")
        echo -e "${YELLOW}🧹 Netejant contenidors i imatges...${NC}"
        docker-compose down -v --rmi all
        docker system prune -f
        echo -e "${GREEN}✅ Neteja completada!${NC}"
        ;;
    "backup")
        echo -e "${BLUE}💾 Creant backup de la base de dades...${NC}"
        mkdir -p ./data/backup
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        docker-compose exec postgres pg_dump -U pythontecnica_user pythontecnica_db > "./data/backup/$BACKUP_FILE"
        echo -e "${GREEN}✅ Backup creat: ./data/backup/$BACKUP_FILE${NC}"
        ;;
    "shell")
        echo -e "${BLUE}🐚 Obrint shell del contenidor app...${NC}"
        docker-compose exec pythontecnica_app bash
        ;;
    "db-shell")
        echo -e "${BLUE}🐚 Obrint shell de PostgreSQL...${NC}"
        docker-compose exec postgres psql -U pythontecnica_user -d pythontecnica_db
        ;;
    "update")
        echo -e "${BLUE}🔄 Actualitzant aplicació...${NC}"
        git pull
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo -e "${GREEN}✅ Aplicació actualitzada!${NC}"
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Comanda desconeguda: $1${NC}"
        show_help
        exit 1
        ;;
esac