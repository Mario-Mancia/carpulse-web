from django.contrib.auth.models import Group
from django.core.management.color import no_style
from django.db import connections, transaction

ESTADOS_USUARIO = (
    (1, "Activo", "Cuenta habilitada para utilizar la plataforma."),
    (2, "Inactivo", "Cuenta deshabilitada."),
    (3, "Suspendido", "Cuenta suspendida temporalmente."),
    (4, "Pendiente de verificación", "Cuenta pendiente de verificar."),
)


def sembrar_datos_iniciales(sender=None, using="default", **kwargs):
    from apps.core.models import ConfiguracionPlataforma
    from apps.usuarios.constants import GRUPOS
    from apps.usuarios.models import EstadoUsuario

    conexion = connections[using]
    existentes = set(conexion.introspection.table_names())
    requeridas = {modelo._meta.db_table for modelo in (EstadoUsuario, ConfiguracionPlataforma, Group)}
    if not requeridas <= existentes:
        return

    with transaction.atomic(using=using):
        for id_, nombre, descripcion in ESTADOS_USUARIO:
            EstadoUsuario.objects.using(using).get_or_create(
                nombre=nombre, defaults={"id": id_, "descripcion": descripcion}
            )
        for nombre in GRUPOS:
            Group.objects.using(using).get_or_create(name=nombre)
        if not ConfiguracionPlataforma.objects.using(using).exists():
            ConfiguracionPlataforma(nombre_plataforma="CarPulse").save(using=using)

        sentencias = conexion.ops.sequence_reset_sql(no_style(), [EstadoUsuario])
        with conexion.cursor() as cursor:
            for sentencia in sentencias:
                cursor.execute(sentencia)
