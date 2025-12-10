FROM python:3.11-slim

# Instalar dependencias del sistema para weasyprint
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY la_playita_project/ ./la_playita_project/

# Cambiar al directorio del proyecto Django
WORKDIR /app/la_playita_project

# Comando por defecto
CMD ["gunicorn", "la_playita_project.wsgi:application", "--bind", "0.0.0.0:$PORT"]