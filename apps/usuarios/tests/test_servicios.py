from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.usuarios.constants import ESTADO_ACTIVO, ESTADO_INACTIVO, GRUPO_ADMINISTRADOR, GRUPO_OPERADOR
from apps.usuarios.models import Empleado, EstadoUsuario
from apps.usuarios.services.usuarios import ErrorUsuarios, actualizar_usuario, crear_empleado
from apps.usuarios.tests.utiles import CLAVE, crear_administrador, crear_operador


def datos_para(usuario, **cambios):
    datos = {
        "estado": EstadoUsuario.objects.get(pk=ESTADO_ACTIVO),
        "nombres": usuario.nombres,
        "apellidos": usuario.apellidos,
        "telefono": usuario.telefono,
        "rol": GRUPO_OPERADOR,
        "codigo_empleado": usuario.empleado.codigo_empleado,
        "cargo": usuario.empleado.cargo,
        "fecha_contratacion": None,
        "empleado_activo": True,
    }
    datos.update(cambios)
    return datos


class CrearEmpleadoTests(TestCase):
    def test_crea_usuario_empleado_grupo_y_correo_verificado(self):
        operador = crear_operador()
        self.assertTrue(operador.is_staff)
        self.assertTrue(operador.groups.filter(name=GRUPO_OPERADOR).exists())
        self.assertEqual(operador.empleado.codigo_empleado, "EMP-001")
        self.assertTrue(operador.emailaddress_set.filter(verified=True, primary=True).exists())

    def test_codigo_se_guarda_en_mayusculas(self):
        usuario = crear_empleado(
            correo="b@example.com", nombres="Ana", apellidos="Ruiz", telefono=None, rol=GRUPO_OPERADOR,
            password=CLAVE, codigo_empleado="emp-777", cargo="Soporte",
        )
        self.assertEqual(usuario.empleado.codigo_empleado, "EMP-777")

    def test_rol_invalido(self):
        with self.assertRaises(ErrorUsuarios):
            crear_empleado(
                correo="c@example.com", nombres="Ana", apellidos="Ruiz", telefono=None, rol="Customer",
                password=CLAVE, codigo_empleado="EMP-5", cargo="X",
            )

    def test_clave_debil(self):
        with self.assertRaises(ValidationError):
            crear_empleado(
                correo="d@example.com", nombres="Ana", apellidos="Ruiz", telefono=None, rol=GRUPO_OPERADOR,
                password="123", codigo_empleado="EMP-6", cargo="X",
            )


class ActualizarUsuarioTests(TestCase):
    def test_cambia_rol_de_operador_a_administrador(self):
        admin = crear_administrador()
        operador = crear_operador()
        actualizar_usuario(operador.pk, admin, datos_para(operador, rol=GRUPO_ADMINISTRADOR, cargo="Jefe"))
        operador.refresh_from_db()
        self.assertTrue(operador.groups.filter(name=GRUPO_ADMINISTRADOR).exists())
        self.assertFalse(operador.groups.filter(name=GRUPO_OPERADOR).exists())
        self.assertEqual(operador.empleado.cargo, "Jefe")

    def test_no_puede_desactivarse_a_si_mismo(self):
        admin = crear_administrador()
        with self.assertRaises(ErrorUsuarios):
            actualizar_usuario(
                admin.pk, admin,
                datos_para(admin, rol=GRUPO_ADMINISTRADOR, estado=EstadoUsuario.objects.get(pk=ESTADO_INACTIVO)),
            )

    def test_no_puede_quitarse_el_rol_de_administrador(self):
        admin = crear_administrador()
        crear_administrador(correo="otro@example.com", codigo="EMP-901")
        with self.assertRaises(ErrorUsuarios):
            actualizar_usuario(admin.pk, admin, datos_para(admin, rol=GRUPO_OPERADOR))

    def test_debe_quedar_un_administrador_activo(self):
        unico = crear_administrador()
        operador = crear_operador()
        with self.assertRaises(ErrorUsuarios):
            actualizar_usuario(
                unico.pk, operador,
                datos_para(unico, rol=GRUPO_ADMINISTRADOR, estado=EstadoUsuario.objects.get(pk=ESTADO_INACTIVO)),
            )
        unico.refresh_from_db()
        self.assertEqual(unico.estado_id, ESTADO_ACTIVO)

    def test_desactivar_empleado_distinto_si_hay_otro_administrador(self):
        admin = crear_administrador()
        operador = crear_operador()
        actualizar_usuario(
            operador.pk, admin, datos_para(operador, estado=EstadoUsuario.objects.get(pk=ESTADO_INACTIVO), empleado_activo=False)
        )
        operador.refresh_from_db()
        self.assertFalse(operador.is_active)
        self.assertFalse(Empleado.objects.get(usuario=operador).activo)
