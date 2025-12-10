FROM python:3.11-slim

# Instalar dependencias del sistema para weasyprint y mysql client
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-2.0-dev \
    libffi-dev \
    libfreetype6-dev \
    libfontconfig1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    libxcb1-dev \
    libxcb-render0-dev \
    libxcb-shm0-dev \
    mysql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto y el backup
COPY la_playita_project/ ./la_playita_project/
COPY database/ult_ver_backup_912.sql ./backup.sql

# Cambiar al directorio del proyecto Django
WORKDIR /app/la_playita_project

# Exponer el puerto
EXPOSE 8000

# Copiar y configurar script de importación
COPY import_backup.sh /start.sh
RUN chmod +x /start.sh

# Comando por defecto
CMD ["/start.sh"]