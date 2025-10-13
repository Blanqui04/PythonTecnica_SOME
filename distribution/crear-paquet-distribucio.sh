#!/bin/bash
# Script per crear paquet de distribució - PythonTecnica_SOME
# Autor: Sistema de distribució automàtica

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "==============================================="
echo "    CREANT PAQUET DE DISTRIBUCIÓ"
echo "         PythonTecnica_SOME v1.0"
echo "==============================================="
echo ""

# Variables
PACKAGE_NAME="PythonTecnica_SOME_Docker_v1.0"
PACKAGE_DIR="./${PACKAGE_NAME}"
DIST_DIR="./distribution"

# Crear directoris
rm -rf "${DIST_DIR}"
mkdir -p "${DIST_DIR}"
mkdir -p "${PACKAGE_DIR}"

echo -e "${GREEN}✅ Directoris creats${NC}"

# Copiar fitxers essencials per Docker
echo ""
echo -e "${BLUE}📁 Copiant fitxers essencials...${NC}"

# Fitxers Docker
cp Dockerfile "${PACKAGE_DIR}/"
cp docker-compose.yml "${PACKAGE_DIR}/"
cp .dockerignore "${PACKAGE_DIR}/"
cp .env.example "${PACKAGE_DIR}/"

# Scripts d'instal·lació
cp docker-install-windows.bat "${PACKAGE_DIR}/"
cp docker-install-linux.sh "${PACKAGE_DIR}/"
cp docker-manager.sh "${PACKAGE_DIR}/"
cp docker-manager-windows.bat "${PACKAGE_DIR}/"

# Documentació
cp DOCKER_README.md "${PACKAGE_DIR}/"
cp "INSTRUCCIONS_INSTAL·LACIO.txt" "${PACKAGE_DIR}/"

echo -e "${GREEN}✅ Fitxers Docker copiats${NC}"

# Copiar codi de l'aplicació
echo ""
echo -e "${BLUE}📦 Copiant codi de l'aplicació...${NC}"

# Fitxer principal
cp main_app.py "${PACKAGE_DIR}/"
cp pytest.ini "${PACKAGE_DIR}/" 2>/dev/null || true

# Carpetes essencials
cp -r src "${PACKAGE_DIR}/" 2>/dev/null || true
cp -r config "${PACKAGE_DIR}/" 2>/dev/null || true
cp -r assets "${PACKAGE_DIR}/" 2>/dev/null || true
cp -r i18n "${PACKAGE_DIR}/" 2>/dev/null || true

# Crear directoris buits necessaris
mkdir -p "${PACKAGE_DIR}/data"
mkdir -p "${PACKAGE_DIR}/logs"
mkdir -p "${PACKAGE_DIR}/sessions"
mkdir -p "${PACKAGE_DIR}/compliance"

echo -e "${GREEN}✅ Codi de l'aplicació copiat${NC}"

# Crear fitxer README per al paquet
echo ""
echo -e "${BLUE}📝 Creant documentació del paquet...${NC}"

cat > "${PACKAGE_DIR}/LLEGEIX-ME_PRIMER.txt" << 'EOF'
# PAQUET DE DISTRIBUCIÓ - PythonTecnica_SOME

Aquest és el paquet complet per instal·lar PythonTecnica_SOME amb Docker.

INSTRUCCIONS RÀPIDES:

Windows:
  1. Instal·la Docker Desktop
  2. Fes doble clic a: docker-install-windows.bat

Linux/macOS:
  1. Instal·la Docker
  2. Executa: ./docker-install-linux.sh

Per més detalls, consulta DOCKER_README.md
EOF

echo -e "${GREEN}✅ Documentació creada${NC}"

# Dona permisos d'execució als scripts
chmod +x "${PACKAGE_DIR}/"*.sh

# Comprimir el paquet
echo ""
echo -e "${BLUE}📦 Creant arxiu TAR.GZ...${NC}"

cd "${DIST_DIR}" || exit 1
tar -czf "${PACKAGE_NAME}.tar.gz" -C .. "${PACKAGE_NAME}"
cd .. || exit 1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Paquet TAR.GZ creat correctament${NC}"
else
    echo -e "${YELLOW}⚠️  Error creant TAR.GZ${NC}"
fi

# Crear també ZIP si zip està disponible
if command -v zip &> /dev/null; then
    echo -e "${BLUE}📦 Creant arxiu ZIP...${NC}"
    cd "${PACKAGE_DIR}" || exit 1
    zip -r "../${DIST_DIR}/${PACKAGE_NAME}.zip" . > /dev/null 2>&1
    cd .. || exit 1
    echo -e "${GREEN}✅ Paquet ZIP creat correctament${NC}"
fi

# Neteja
rm -rf "${PACKAGE_DIR}"

echo ""
echo "================================================"
echo -e "${GREEN}✅ PAQUET DE DISTRIBUCIÓ CREAT CORRECTAMENT!${NC}"
echo "================================================"
echo ""
echo -e "${BLUE}📁 Localització:${NC} ${DIST_DIR}/${PACKAGE_NAME}.*"
echo -e "${BLUE}📊 Contingut del paquet:${NC}"
echo "   - Aplicació completa amb Docker"
echo "   - Scripts d'instal·lació automàtica"
echo "   - Gestors de serveis"
echo "   - Documentació completa"
echo ""
echo -e "${YELLOW}🚀 DISTRIBUCIÓ:${NC}"
echo "   Comparteix aquest arxiu amb altres usuaris"
echo "   Només necessitaran Docker instal·lat!"
echo ""
echo "================================================"