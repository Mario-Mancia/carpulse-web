from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed, user_signed_up
from django.contrib.sessions.models import Session
from django.test import Client, TestCase, override_settings

from apps.clientes.models import Cliente
from apps.usuarios.constants import ESTADO_ACTIVO, ESTADO_PENDIENTE, GRUPO_CLIENTE
from apps.usuarios.models import Usuario
from apps.usuarios.sesiones import cerrar_otras_sesiones
from apps.usuarios.tests.utiles import BACKEND, crear_cliente, crear_superusuario


class SenalesTests(TestCase):
    def test_registro_crea_grupo_y_cliente(self):
        usuario = Usuario.objects.create_user(correo="nuevo@example.com", password="x", nombres="Ana", apellidos="Ruiz")
        user_signed_up.send(sender=Usuario, request=None, user=usuario)
        self.assertTrue(usuario.groups.filter(name=GRUPO_CLIENTE).exists())
        self.assertEqual(Cliente.objects.get(usuario=usuario).correo, "nuevo@example.com")

    def test_registro_ignora_cuentas_del_equipo(self):
        root = crear_superusuario()
        user_signed_up.send(sender=Usuario, request=None, user=root)
        self.assertFalse(root.groups.exists())
        self.assertFalse(Cliente.objects.filter(usuario=root).exists())

    def test_confirmar_correo_activa_cuenta_pendiente(self):
        usuario = Usuario.objects.create_user(
            correo="p@example.com", password="x", nombres="Ana", apellidos="Ruiz", estado_id=ESTADO_PENDIENTE
        )
        direccion = EmailAddress.objects.create(user=usuario, email=usuario.correo, verified=True, primary=True)
        email_confirmed.send(sender=EmailAddress, request=None, email_address=direccion)
        usuario.refresh_from_db()
        self.assertEqual(usuario.estado_id, ESTADO_ACTIVO)


class SesionUnicaTests(TestCase):
    def _sesion_existe(self, cliente):
        return Session.objects.filter(session_key=cliente.session.session_key).exists()

    @override_settings(SESION_UNICA=False)
    def test_cerrar_otras_sesiones_conserva_la_actual(self):
        usuario = crear_cliente()
        a, b = Client(), Client()
        a.force_login(usuario, backend=BACKEND)
        b.force_login(usuario, backend=BACKEND)
        clave_a = a.session.session_key
        self.assertEqual(cerrar_otras_sesiones(usuario, b.session.session_key), 1)
        self.assertFalse(Session.objects.filter(session_key=clave_a).exists())
        self.assertTrue(self._sesion_existe(b))

    @override_settings(SESION_UNICA=True)
    def test_segundo_inicio_de_sesion_cierra_el_primero(self):
        usuario = crear_cliente()
        a, b = Client(), Client()
        a.force_login(usuario, backend=BACKEND)
        clave_a = a.session.session_key
        b.force_login(usuario, backend=BACKEND)
        self.assertFalse(Session.objects.filter(session_key=clave_a).exists())
        self.assertTrue(self._sesion_existe(b))

    @override_settings(SESION_UNICA=True)
    def test_otro_usuario_no_se_ve_afectado(self):
        uno = crear_cliente()
        dos = crear_cliente(correo="dos@example.com")
        a, b = Client(), Client()
        a.force_login(uno, backend=BACKEND)
        b.force_login(dos, backend=BACKEND)
        self.assertTrue(self._sesion_existe(a))
        self.assertTrue(self._sesion_existe(b))
