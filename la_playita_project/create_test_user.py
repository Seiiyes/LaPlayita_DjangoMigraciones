import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

Usuario = get_user_model()
Rol = Usuario.rol.field.related_model

def create_test_user():
    try:
        rol_admin, _ = Rol.objects.get_or_create(nombre="Administrador")
        
        if not Usuario.objects.filter(username="1000").exists():
            Usuario.objects.create_superuser(
                username="1000",
                password="password123",
                first_name="Test",
                last_name="Admin",
                email="test@admin.com",
                rol=rol_admin
            )
            print("Usuario '1000' creado con password 'password123'")
        else:
            print("Usuario '1000' ya existe")
            
    except Exception as e:
        print(f"Error creando usuario: {e}")

if __name__ == "__main__":
    create_test_user()
