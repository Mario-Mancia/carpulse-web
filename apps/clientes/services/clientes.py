from django.db import transaction

from apps.clientes.models import Cliente


@transaction.atomic
def asegurar_cliente(usuario):
    cliente = Cliente.objects.filter(usuario=usuario).first()
    if cliente is not None:
        return cliente
    return Cliente.objects.create(
        usuario=usuario,
        nombres=usuario.nombres,
        apellidos=usuario.apellidos,
        correo=usuario.correo,
        telefono=usuario.telefono,
    )
