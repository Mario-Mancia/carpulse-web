from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.clientes.models import Cliente, UnidadDistancia, UnidadVolumen
from apps.clientes.services.clientes import asegurar_cliente
from apps.usuarios.models import Usuario


class ClienteTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo="Carla@Example.com", password="x", nombres="Carla", apellidos="Pérez", telefono="70000000"
        )

    def test_asegurar_cliente_copia_datos_y_es_idempotente(self):
        cliente = asegurar_cliente(self.usuario)
        self.assertEqual(cliente.correo, "carla@example.com")
        self.assertEqual(cliente.telefono, "70000000")
        self.assertEqual(cliente.unidad_distancia, UnidadDistancia.KILOMETROS)
        self.assertEqual(cliente.unidad_volumen, UnidadVolumen.LITROS)
        self.assertTrue(cliente.notificar_correo)
        self.assertEqual(asegurar_cliente(self.usuario).pk, cliente.pk)
        self.assertEqual(Cliente.objects.count(), 1)

    def test_unidades_invalidas(self):
        cliente = asegurar_cliente(self.usuario)
        cliente.unidad_distancia = "XX"
        with self.assertRaises(ValidationError):
            cliente.save()
        cliente.unidad_distancia = UnidadDistancia.MILLAS
        cliente.unidad_volumen = "ZZZ"
        with self.assertRaises(ValidationError):
            cliente.save()

    def test_un_cliente_por_usuario(self):
        asegurar_cliente(self.usuario)
        with self.assertRaises((ValidationError, IntegrityError)):
            with transaction.atomic():
                Cliente(usuario=self.usuario, nombres="A", apellidos="B", correo="a@b.co").save()

    def test_usuario_con_cliente_no_se_puede_borrar(self):
        asegurar_cliente(self.usuario)
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.usuario.delete()
