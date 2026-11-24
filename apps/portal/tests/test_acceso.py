import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.core.models import ClaveRecurso, ConfiguracionPlataforma, RecursoGrafico
from apps.usuarios.tests.utiles import (
    BACKEND,
    CLAVE,
    crear_administrador,
    crear_cliente,
    crear_operador,
    crear_superusuario,
)


def entrar(usuario):
    cliente = Client()
    cliente.force_login(usuario, backend=BACKEND)
    return cliente


class InvitadoTests(TestCase):
    def test_paginas_publicas(self):
        for nombre in ("guest:inicio", "guest:terminos"):
            respuesta = self.client.get(reverse(nombre))
            self.assertEqual(respuesta.status_code, 200, nombre)
        self.assertContains(self.client.get(reverse("guest:inicio")), "CarPulse")

    def test_anonimo_es_enviado_al_login(self):
        for nombre in ("customer:panel", "gestion:panel", "gestion:configuracion", "redirigir"):
            url = reverse(nombre)
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 302, nombre)
            self.assertIn(reverse("account_login"), respuesta["Location"], nombre)

    def test_registro_publico_cerrado_en_fase_0(self):
        respuesta = self.client.post(
            reverse("account_signup"),
            {"email": "nuevo@example.com", "password1": CLAVE, "password2": CLAVE},
        )
        self.assertNotEqual(respuesta.status_code, 302)
        from apps.usuarios.models import Usuario

        self.assertFalse(Usuario.objects.filter(correo="nuevo@example.com").exists())


class RedireccionPorRolTests(TestCase):
    def test_cada_rol_va_a_su_panel(self):
        casos = (
            (crear_cliente(), reverse("customer:panel")),
            (crear_operador(), reverse("gestion:panel")),
            (crear_administrador(), reverse("gestion:panel")),
            (crear_superusuario(), reverse("gestion:panel")),
        )
        for usuario, destino in casos:
            respuesta = entrar(usuario).get(reverse("redirigir"))
            self.assertRedirects(respuesta, destino, fetch_redirect_response=False)

    def test_usuario_sin_rol_vuelve_al_inicio(self):
        from apps.usuarios.models import Usuario

        sin_rol = Usuario.objects.create_user(correo="x@example.com", password="x", nombres="Ana", apellidos="Ruiz")
        respuesta = entrar(sin_rol).get(reverse("redirigir"))
        self.assertRedirects(respuesta, reverse("guest:inicio"), fetch_redirect_response=False)


class AccesoPorRolTests(TestCase):
    def test_cliente_solo_ve_su_panel(self):
        c = entrar(crear_cliente())
        self.assertEqual(c.get(reverse("customer:panel")).status_code, 200)
        self.assertEqual(c.get(reverse("gestion:panel")).status_code, 403)
        self.assertEqual(c.get(reverse("gestion:configuracion")).status_code, 403)

    def test_personal_no_entra_al_panel_de_cliente(self):
        for usuario in (crear_operador(), crear_administrador(correo="a@example.com"), crear_superusuario()):
            self.assertEqual(entrar(usuario).get(reverse("customer:panel")).status_code, 403)

    def test_operador_ve_gestion_pero_no_configuracion(self):
        c = entrar(crear_operador())
        self.assertEqual(c.get(reverse("gestion:panel")).status_code, 200)
        self.assertEqual(c.get(reverse("gestion:configuracion")).status_code, 403)
        self.assertNotContains(c.get(reverse("gestion:panel")), reverse("gestion:configuracion"))

    def test_administrador_ve_configuracion(self):
        c = entrar(crear_administrador())
        self.assertEqual(c.get(reverse("gestion:panel")).status_code, 200)
        self.assertContains(c.get(reverse("gestion:panel")), reverse("gestion:configuracion"))
        self.assertEqual(c.get(reverse("gestion:configuracion")).status_code, 200)

    def test_superusuario_ve_configuracion(self):
        self.assertEqual(entrar(crear_superusuario()).get(reverse("gestion:configuracion")).status_code, 200)

    def test_operador_no_puede_modificar_configuracion(self):
        c = entrar(crear_operador())
        respuesta = c.post(reverse("gestion:configuracion"), {"accion": "guardar_config", "nombre_plataforma": "X"})
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(ConfiguracionPlataforma.objects.get().nombre_plataforma, "CarPulse")

    def test_cuenta_suspendida_pierde_acceso(self):
        from apps.usuarios.constants import ESTADO_SUSPENDIDO

        cliente = crear_cliente()
        c = entrar(cliente)
        cliente.estado_id = ESTADO_SUSPENDIDO
        cliente.save()
        respuesta = c.get(reverse("customer:panel"))
        self.assertIn(respuesta.status_code, (302, 403))


class InicioDeSesionTests(TestCase):
    def test_login_real_redirige_segun_rol(self):
        crear_cliente()
        crear_operador()
        casos = (("cliente@example.com", reverse("customer:panel")), ("operador@example.com", reverse("gestion:panel")))
        for correo, destino in casos:
            c = Client()
            respuesta = c.post(reverse("account_login"), {"login": correo, "password": CLAVE})
            self.assertEqual(respuesta.status_code, 302, correo)
            self.assertEqual(respuesta["Location"], reverse("redirigir"), correo)
            self.assertRedirects(c.get(reverse("redirigir")), destino, fetch_redirect_response=False)

    def test_clave_incorrecta_no_inicia_sesion(self):
        crear_cliente()
        respuesta = self.client.post(reverse("account_login"), {"login": "cliente@example.com", "password": "incorrecta"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


def imagen_png():
    buffer = io.BytesIO()
    Image.new("RGB", (40, 40), (58, 130, 246)).save(buffer, format="PNG")
    return SimpleUploadedFile("logo.png", buffer.getvalue(), content_type="image/png")


class ConfiguracionViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._medios = tempfile.mkdtemp()
        cls._anulacion = override_settings(MEDIA_ROOT=cls._medios)
        cls._anulacion.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._anulacion.disable()
        shutil.rmtree(cls._medios, ignore_errors=True)

    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.c = entrar(crear_administrador())
        self.url = reverse("gestion:configuracion")

    def test_guardar_configuracion(self):
        datos = {
            "accion": "guardar_config",
            "nombre_plataforma": "CarPulse Demo",
            "correo_contacto": "hola@carpulse.test",
            "telefono_contacto": "",
            "sitio_web": "",
            "max_vehiculos_por_cliente": 3,
            "retencion_sincronizaciones_dias": 90,
            "recordatorio_anticipacion_dias": 7,
            "recordatorio_anticipacion_km": 500,
        }
        self.assertRedirects(self.c.post(self.url, datos), self.url, fetch_redirect_response=False)
        cfg = ConfiguracionPlataforma.objects.get()
        self.assertEqual(cfg.nombre_plataforma, "CarPulse Demo")
        self.assertEqual(cfg.correo_contacto, "hola@carpulse.test")

    def test_configuracion_invalida(self):
        respuesta = self.c.post(self.url, {"accion": "guardar_config", "nombre_plataforma": "X", "max_vehiculos_por_cliente": 0})
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(ConfiguracionPlataforma.objects.get().nombre_plataforma, "CarPulse")

    def test_subir_y_quitar_recurso(self):
        with self.captureOnCommitCallbacks(execute=True):
            respuesta = self.c.post(
                self.url,
                {"accion": "subir_recurso", "clave": ClaveRecurso.LOGO, "archivo": imagen_png(), "texto_alternativo": "Logo"},
            )
        self.assertRedirects(respuesta, self.url, fetch_redirect_response=False)
        self.assertTrue(RecursoGrafico.objects.filter(clave=ClaveRecurso.LOGO).exists())
        self.assertContains(self.c.get(reverse("guest:inicio")), "<img src=")
        with self.captureOnCommitCallbacks(execute=True):
            self.c.post(self.url, {"accion": "quitar_recurso", "clave": ClaveRecurso.LOGO})
        self.assertFalse(RecursoGrafico.objects.filter(clave=ClaveRecurso.LOGO).exists())

    def test_archivo_que_no_es_imagen_se_rechaza(self):
        falso = SimpleUploadedFile("x.png", b"no es imagen", content_type="image/png")
        respuesta = self.c.post(self.url, {"accion": "subir_recurso", "clave": ClaveRecurso.LOGO, "archivo": falso})
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(RecursoGrafico.objects.exists())

    def test_accion_desconocida(self):
        self.assertRedirects(self.c.post(self.url, {"accion": "borrar_todo"}), self.url, fetch_redirect_response=False)
