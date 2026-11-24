from allauth.account.models import EmailAddress
from django.contrib.auth.models import Group

from apps.clientes.services.clientes import asegurar_cliente
from apps.usuarios.constants import GRUPO_ADMINISTRADOR, GRUPO_CLIENTE, GRUPO_OPERADOR
from apps.usuarios.models import Usuario
from apps.usuarios.services.usuarios import crear_empleado

CLAVE = "Clave-segura-123"
BACKEND = "django.contrib.auth.backends.ModelBackend"


def crear_cliente(correo="cliente@example.com", **extra):
    usuario = Usuario.objects.create_user(
        correo=correo, password=CLAVE, nombres="Carla", apellidos="Pérez", **extra
    )
    usuario.groups.add(Group.objects.get(name=GRUPO_CLIENTE))
    asegurar_cliente(usuario)
    EmailAddress.objects.create(user=usuario, email=usuario.correo, verified=True, primary=True)
    return usuario


def crear_personal(rol=GRUPO_OPERADOR, correo=None, codigo="EMP-001"):
    return crear_empleado(
        correo=correo or f"{rol.lower()}@example.com",
        nombres="Marta",
        apellidos="Gómez",
        telefono=None,
        rol=rol,
        password=CLAVE,
        codigo_empleado=codigo,
        cargo="Soporte",
    )


def crear_operador(correo="operador@example.com", codigo="EMP-001"):
    return crear_personal(GRUPO_OPERADOR, correo, codigo)


def crear_administrador(correo="admin@example.com", codigo="EMP-900"):
    return crear_personal(GRUPO_ADMINISTRADOR, correo, codigo)


def crear_superusuario(correo="root@example.com"):
    return Usuario.objects.create_superuser(correo=correo, password=CLAVE, nombres="Root", apellidos="Admin")
