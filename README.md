# La Playita - Sistema POS

Sistema de punto de venta desarrollado en Django para La Playita.

## Despliegue en Railway

### 1. Preparación
- Fork este repositorio
- Crea una cuenta en [Railway](https://railway.app)

### 2. Configuración de la base de datos
1. En Railway, crea un nuevo proyecto
2. Agrega un servicio MySQL
3. Copia la URL de conexión de la base de datos

### 3. Configuración del proyecto Django
1. Conecta tu repositorio de GitHub
2. Configura las siguientes variables de entorno:

```
DEBUG=False
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=mysql://usuario:password@host:puerto/database
ALLOWED_HOSTS=tu-dominio.railway.app
```

### 4. Despliegue
Railway detectará automáticamente que es un proyecto Django y ejecutará:
- `pip install -r requirements.txt`
- `python manage.py migrate`
- `python manage.py collectstatic --noinput`
- `gunicorn la_playita_project.wsgi:application`

## Funcionalidades
- Sistema de inventario
- Punto de venta (POS)
- Gestión de clientes
- Reportes
- Sistema PQRS
- Gestión de proveedores

## Tecnologías
- Django 5.2.7
- MySQL
- Bootstrap
- JavaScript
- WhiteNoise (archivos estáticos)