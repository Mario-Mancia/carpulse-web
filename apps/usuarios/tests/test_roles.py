from django.contrib.auth.models import Group
from django.test import TestCase

from apps.usuarios.constants import (
    ESTADO_ACTIVO,
    ESTADO_INACTIVO,
    ESTADO_PENDIENTE,
    ESTADO_SUSPENDIDO,
    GRUPO_ADMINISTRADOR,
    GRUPO_CLIENTE,
    GRUPO_OPERADOR,
)
from apps.usuarios.models import Empleado, EstadoUsuario
from apps.usuarios.selectors.usuarios import destino_por_rol
from apps.usuarios.tests.utiles import crear_administrador, crear_cliente, crear_operador, crear_superusuario


class SemillasTests(TestCase):
    def test_estados_y_grupos_sembrados(self):
        self.assertEqual(
            list(EstadoUsuario.objects.order_by("id").values_list("id", flat=True)),
            [ESTADO_ACTIVO, ESTADO_INACTIVO, ESTADO_SUSPENDIDO, ESTADO_PENDIENTE],
        )
        self.assertEqual(
            set(Group.objects.values_list("name", flat=True)),
            {GRUPO_CLIENTE, GRUPO_OPERADOR, GRUPO_ADMINISTRADOR},
        )


class RolesTests(TestCase):
    def test_cliente(self):
        cliente = crear_cliente()
        self.assertTrue(cliente.tiene_algun_rol((GRUPO_CLIENTE,)))
        self.assertFalse(cliente.tiene_algun_rol((GRUPO_OPERADOR, GRUPO_ADMINISTRADOR)))
        self.assertFalse(cliente.es_personal)

    def test_operador(self):
        operador = crear_operador()
        self.assertTrue(operador.es_personal)
        self.assertTrue(operador.tiene_algun_rol((GRUPO_OPERADOR,)))
        self.assertFalse(operador.tiene_algun_rol((GRUPO_ADMINISTRADOR,)))
        self.assertFalse(operador.tiene_algun_rol((GRUPO_CLIENTE,)))

    def test_administrador(self):
        admin = crear_administrador()
        self.assertTrue(admin.tiene_algun_rol((GRUPO_ADMINISTRADOR,)))
        self.assertFalse(admin.tiene_algun_rol((GRUPO_CLIENTE,)))

    def test_superusuario_es_personal_pero_nunca_cliente(self):
        root = crear_superusuario()
        self.assertTrue(root.tiene_algun_rol((GRUPO_ADMINISTRADOR,)))
        self.assertTrue(root.tiene_algun_rol((GRUPO_OPERADOR,)))
        self.assertFalse(root.tiene_algun_rol((GRUPO_CLIENTE,)))

    def test_personal_con_grupo_cliente_no_es_cliente(self):
        operador = crear_operador()
        operador.groups.add(Group.objects.get(name=GRUPO_CLIENTE))
        self.assertFalse(operador.tiene_algun_rol((GRUPO_CLIENTE,)))
        self.assertTrue(operador.tiene_algun_rol((GRUPO_OPERADOR,)))

    def test_cliente_con_grupo_de_personal_deja_de_ser_cliente(self):
        cliente = crear_cliente()
        cliente.groups.add(Group.objects.get(name=GRUPO_OPERADOR))
        self.assertTrue(cliente.es_personal)
        self.assertFalse(cliente.tiene_algun_rol((GRUPO_CLIENTE,)))

    def test_estados_no_activos_no_tienen_rol(self):
        for estado in (ESTADO_INACTIVO, ESTADO_SUSPENDIDO, ESTADO_PENDIENTE):
            cliente = crear_cliente(correo=f"c{estado}@example.com")
            cliente.estado_id = estado
            cliente.save()
            self.assertFalse(cliente.tiene_algun_rol((GRUPO_CLIENTE,)), estado)

    def test_bloquear_y_reactivar_sincroniza_is_active(self):
        cliente = crear_cliente()
        cliente.estado_id = ESTADO_SUSPENDIDO
        cliente.save()
        cliente.refresh_from_db()
        self.assertFalse(cliente.is_active)
        cliente.estado_id = ESTADO_ACTIVO
        cliente.save()
        cliente.refresh_from_db()
        self.assertTrue(cliente.is_active)

    def test_empleado_dado_de_baja_pierde_roles_de_personal(self):
        operador = crear_operador()
        Empleado.objects.filter(usuario=operador).update(activo=False)
        self.assertFalse(operador.tiene_algun_rol((GRUPO_OPERADOR,)))

    def test_correo_se_normaliza_a_minusculas(self):
        cliente = crear_cliente(correo="MAYUS@Example.COM")
        self.assertEqual(cliente.correo, "mayus@example.com")


class DestinoPorRolTests(TestCase):
    def test_destinos(self):
        self.assertEqual(destino_por_rol(crear_cliente()), "customer:panel")
        self.assertEqual(destino_por_rol(crear_operador()), "gestion:panel")
        self.assertEqual(destino_por_rol(crear_administrador()), "gestion:panel")
        self.assertEqual(destino_por_rol(crear_superusuario()), "gestion:panel")

    def test_sin_rol(self):
        from apps.usuarios.models import Usuario

        sin_rol = Usuario.objects.create_user(correo="x@example.com", password="x", nombres="Ana", apellidos="Ruiz")
        self.assertIsNone(destino_por_rol(sin_rol))
