from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class Rol(models.Model):
    nombre = models.CharField(max_length=35, unique=True)

    class Meta:
        managed = False
        db_table = 'rol'

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("El usuario debe tener documento")

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault("rol", Rol.objects.get(nombre="Administrador"))

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    # Campos EXACTOS de tu tabla real
    username = models.CharField(
        db_column='documento',
        max_length=20,
        unique=True
    )
    password = models.CharField(
        db_column='contrasena',
        max_length=255
    )
    first_name = models.CharField(db_column='nombres', max_length=50)
    last_name = models.CharField(db_column='apellidos', max_length=50)
    email = models.EmailField(db_column='correo', max_length=60, unique=True)
    date_joined = models.DateTimeField(db_column='fecha_creacion', default=timezone.now)
    last_login = models.DateTimeField(db_column='ultimo_login', blank=True, null=True)

    telefono = models.CharField(max_length=20, blank=True, null=True)
    estado = models.CharField(max_length=20, default='activo')

    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        db_column='rol_id'
    )

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    objects = UsuarioManager()

    class Meta:
        managed = True
        db_table = "usuario"

    def save(self, *args, **kwargs):
        if self.rol and self.rol.nombre == "Administrador":
            self.is_superuser = True
            self.is_staff = True
        else:
            self.is_superuser = False
            self.is_staff = False
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.estado == "activo"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
