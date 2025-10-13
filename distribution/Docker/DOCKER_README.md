# 🐳 Guia d'Instal·lació Docker - PythonTecnica_SOME

Aquesta guia et permetrà instal·lar i executar l'aplicació PythonTecnica_SOME en qualsevol PC utilitzant Docker, evitant problemes de dependències i configuració.

## 📋 Requisits del Sistema

### Requisits Mínims
- **RAM**: 4 GB (recomanat 8 GB)
- **Disc**: 2 GB d'espai lliure
- **Sistema Operatiu**: 
  - Windows 10/11 (64-bit)
  - Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)
  - macOS 10.14+

### Software Necessari
- **Docker Desktop** (Windows/macOS) o **Docker Engine** (Linux)
- **Docker Compose** (inclòs amb Docker Desktop)

## 🚀 Instal·lació Ràpida

### Windows

1. **Descarrega i instal·la Docker Desktop:**
   ```
   https://www.docker.com/products/docker-desktop/
   ```

2. **Descarrega el projecte:**
   - Descarrega el ZIP del projecte o clona el repositori
   - Extreu tots els fitxers a una carpeta (ex: `C:\PythonTecnica`)

3. **Executa l'instal·lador:**
   ```batch
   # Obre PowerShell o CMD a la carpeta del projecte
   cd C:\PythonTecnica\PythonTecnica_SOME
   
   # Executa l'script d'instal·lació
   docker-install-windows.bat
   ```

### Linux/macOS

1. **Instal·la Docker:**
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Afegir usuari al grup docker
   sudo usermod -aG docker $USER
   ```

2. **Descarrega el projecte:**
   ```bash
   # Clona o descarrega el projecte
   git clone [URL_DEL_REPOSITORI]
   cd PythonTecnica_SOME
   ```

3. **Executa l'instal·lador:**
   ```bash
   # Dona permisos d'execució
   chmod +x docker-install-linux.sh
   
   # Executa l'script
   ./docker-install-linux.sh
   ```

## 📁 Estructura de Fitxers Docker

Després de la instal·lació, els fitxers Docker seran:

```
PythonTecnica_SOME/
├── Dockerfile                 # Configuració de la imatge
├── docker-compose.yml         # Orquestració de serveis
├── .dockerignore             # Fitxers exclosos de la imatge
├── .env                      # Variables d'entorn
├── docker-install-windows.bat # Script Windows
├── docker-install-linux.sh   # Script Linux/macOS
└── docker-manager.sh         # Gestor de serveis
```

## 🛠️ Gestió dels Serveis

### Comandes Bàsiques

```bash
# Iniciar l'aplicació
docker-compose up -d

# Parar l'aplicació
docker-compose down

# Veure logs
docker-compose logs -f pythontecnica_app

# Estat dels serveis
docker-compose ps
```

### Gestor Avançat (Linux/macOS)

```bash
# Dona permisos d'execució
chmod +x docker-manager.sh

# Comandes disponibles:
./docker-manager.sh start      # Iniciar serveis
./docker-manager.sh stop       # Parar serveis
./docker-manager.sh restart    # Reiniciar serveis
./docker-manager.sh logs       # Veure logs
./docker-manager.sh status     # Estat serveis
./docker-manager.sh backup     # Fer backup BD
./docker-manager.sh clean      # Neteja completa
./docker-manager.sh help       # Ajuda completa
```

## 🔧 Configuració

### Variables d'Entorn (.env)

```bash
# Contrasenya de la base de dades
POSTGRES_PASSWORD=pythontecnica_secure_pass

# Configuració GUI (Linux)
DISPLAY=:0
```

### Ports Utilitzats

- **5432**: Base de dades PostgreSQL
- **8080**: Aplicació web (si aplica)

## 💾 Gestió de Dades

### Persistència
Les dades es guarden en volums Docker i carpetes locals:
- `./data/`: Dades de l'aplicació
- `./logs/`: Logs del sistema
- `./compliance/`: Auditories
- `postgres_data`: Dades de PostgreSQL

### Backups

```bash
# Backup manual
docker-compose exec postgres pg_dump -U pythontecnica_user pythontecnica_db > backup.sql

# Amb el gestor (Linux/macOS)
./docker-manager.sh backup

# Restaurar backup
docker-compose exec -T postgres psql -U pythontecnica_user pythontecnica_db < backup.sql
```

## 🐛 Resolució de Problemes

### Problema: Docker no inicia
**Solució:**
```bash
# Windows: Reinicia Docker Desktop
# Linux: 
sudo systemctl restart docker
```

### Problema: Port ja en ús
**Solució:**
```bash
# Canviar ports al docker-compose.yml
ports:
  - "5433:5432"  # Canvia 5432 per 5433
```

### Problema: Permisos (Linux)
**Solució:**
```bash
sudo chown -R $USER:$USER ./data ./logs
```

### Problema: GUI no funciona (Linux)
**Solució:**
```bash
# Permet connexions X11
xhost +local:docker

# O descomenta aquesta línia al docker-compose.yml:
# privileged: true
```

## 🔄 Actualitzacions

### Actualitzar l'aplicació:

```bash
# Parar serveis
docker-compose down

# Actualitzar codi (si és un repositori git)
git pull

# Reconstruir i iniciar
docker-compose up --build -d
```

### Amb el gestor (Linux/macOS):
```bash
./docker-manager.sh update
```

## 📊 Monitoratge

### Veure logs en temps real:
```bash
docker-compose logs -f
```

### Estat dels contenidors:
```bash
docker-compose ps
```

### Ús de recursos:
```bash
docker stats
```

## 🚪 Accés als Serveis

Després de la instal·lació:

- **Aplicació Principal**: La GUI s'obrirà automàticament
- **Base de Dades**: `localhost:5432`
  - Usuari: `pythontecnica_user`
  - Base de Dades: `pythontecnica_db`
  - Contrasenya: (definida a .env)

## 🆘 Suport

Si tens problemes:

1. **Consulta els logs:**
   ```bash
   docker-compose logs pythontecnica_app
   ```

2. **Verifica l'estat:**
   ```bash
   docker-compose ps
   ```

3. **Reinicia els serveis:**
   ```bash
   docker-compose restart
   ```

4. **Neteja completa (última opció):**
   ```bash
   docker-compose down -v
   docker system prune -f
   # Després tornar a executar la instal·lació
   ```

## 📝 Notes Adicionals

- **Primera execució**: Pot trigar 5-10 minuts descarregant imatges
- **Actualitzacions**: Sempre para els serveis abans d'actualitzar
- **Backups**: Recomana fer backups regulars de la carpeta `./data/`
- **Seguretat**: Canvia la contrasenya per defecte a `.env`

## 🎯 Desinstal·lació

Per eliminar completament l'aplicació:

```bash
# Parar i eliminar contenidors
docker-compose down -v

# Eliminar imatges
docker rmi pythontecnica_some_pythontecnica_app postgres:15-alpine

# Eliminar volums
docker volume prune

# Eliminar carpeta del projecte (opcional)
```

---

**✅ Amb aquesta configuració Docker, pots desplegar l'aplicació en qualsevol PC amb Docker instal·lat, sense preocupar-te per dependències o configuracions específiques!**