import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from users.models import Usuario

# Obtener el usuario con documento 10000000
usuario = Usuario.objects.get(username='10000000')

print(f"Usuario: {usuario.username}")
print(f"Rol: {usuario.rol.nombre}")
print(f"is_staff: {usuario.is_staff}")
print(f"is_superuser: {usuario.is_superuser}")

# Actualizar permisos
if usuario.rol.nombre == 'Administrador':
    usuario.is_staff = True
    usuario.is_superuser = True
    usuario.save()
    print("\n✅ Permisos actualizados")
    print(f"is_staff: {usuario.is_staff}")
    print(f"is_superuser: {usuario.is_superuser}")
else:
    print("\n⚠️ El usuario no es Administrador")
