# Dockerfile per PythonTecnica_SOME
# Utilitza una imatge base de Python amb suport per GUI
FROM python:3.11-slim

# Variables d'entorn
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    QT_X11_NO_MITSHM=1 \
    DISPLAY=:0

# Instal·lar dependències del sistema per PyQt5 i altres
RUN apt-get update && apt-get install -y \
    # Dependències essencials
    build-essential \
    pkg-config \
    # Dependències per PyQt5
    qt5-qmake \
    qtbase5-dev \
    qtbase5-dev-tools \
    libqt5gui5 \
    libqt5core5a \
    libqt5widgets5 \
    # Dependències per PostgreSQL
    libpq-dev \
    # Dependències per X11 (GUI)
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    # Eines adicionals
    git \
    wget \
    curl \
    # Neteja
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuari no-root per seguretat
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Establir directori de treball
WORKDIR /app

# Copiar arxius de configuració primer (per millorar cache de Docker)
COPY config/requirements.txt /app/config/
COPY pytest.ini /app/

# Actualitzar pip i instal·lar dependències Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r config/requirements.txt

# Copiar el codi de l'aplicació
COPY . /app/

# Crear directoris necessaris
RUN mkdir -p /app/data /app/logs /app/temp /app/sessions /app/compliance \
    && chown -R appuser:appuser /app

# Canviar a usuari no-root
USER appuser

# Exposar port si l'aplicació té component web
EXPOSE 8080

# Punt d'entrada
CMD ["python", "main_app.py"]