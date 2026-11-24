import io
import shutil
import tempfile

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.core.models import ClaveRecurso, ConfiguracionPlataforma, RecursoGrafico
from apps.core.services import plataforma as servicio


def imagen_png(ancho=64, alto=32, nombre="logo.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (ancho, alto), (15, 76, 129)).save(buffer, format="PNG")
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/png")


class ServicioPlataformaTests(TestCase):
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
        cache.clear()

    def test_configuracion_se_cachea_y_se_invalida_al_guardar(self):
        self.assertEqual(servicio.configuracion().nombre_plataforma, "CarPulse")
        cfg = ConfiguracionPlataforma.objects.get()
        cfg.nombre_plataforma = "CarPulse Demo"
        cfg.save()
        self.assertEqual(servicio.configuracion().nombre_plataforma, "CarPulse Demo")

    def test_asignar_recurso_guarda_archivo_y_registro(self):
        with self.captureOnCommitCallbacks(execute=True):
            recurso = servicio.asignar_recurso(ClaveRecurso.LOGO, imagen_png(), texto_alternativo="Logo")
        self.assertTrue(default_storage.exists(recurso.ruta))
        self.assertTrue(recurso.ruta.startswith("plataforma/"))
        self.assertEqual(servicio.recursos()["logo"].alt, "Logo")

    def test_reemplazar_recurso_elimina_el_archivo_anterior(self):
        with self.captureOnCommitCallbacks(execute=True):
            primero = servicio.asignar_recurso(ClaveRecurso.FAVICON, imagen_png())
        ruta_anterior = primero.ruta
        with self.captureOnCommitCallbacks(execute=True):
            segundo = servicio.asignar_recurso(ClaveRecurso.FAVICON, imagen_png())
        self.assertNotEqual(ruta_anterior, segundo.ruta)
        self.assertFalse(default_storage.exists(ruta_anterior))
        self.assertTrue(default_storage.exists(segundo.ruta))
        self.assertEqual(RecursoGrafico.objects.filter(clave=ClaveRecurso.FAVICON).count(), 1)

    def test_quitar_recurso(self):
        with self.captureOnCommitCallbacks(execute=True):
            recurso = servicio.asignar_recurso(ClaveRecurso.HERO_INICIO, imagen_png())
        ruta = recurso.ruta
        with self.captureOnCommitCallbacks(execute=True):
            self.assertTrue(servicio.quitar_recurso(ClaveRecurso.HERO_INICIO))
        self.assertFalse(default_storage.exists(ruta))
        self.assertFalse(servicio.quitar_recurso(ClaveRecurso.HERO_INICIO))
        self.assertNotIn("hero_inicio", servicio.recursos())

    def test_clave_inexistente(self):
        with self.assertRaises(ValidationError):
            servicio.asignar_recurso("NO_EXISTE", imagen_png())

    def test_archivo_que_no_es_imagen(self):
        falso = SimpleUploadedFile("x.png", b"esto no es una imagen", content_type="image/png")
        with self.assertRaises(ValidationError):
            servicio.asignar_recurso(ClaveRecurso.LOGO, falso)
        self.assertFalse(RecursoGrafico.objects.exists())

    def test_imagen_grande_se_reduce_al_maximo_de_la_clave(self):
        with self.captureOnCommitCallbacks(execute=True):
            recurso = servicio.asignar_recurso(ClaveRecurso.FAVICON, imagen_png(1000, 800))
        with default_storage.open(recurso.ruta) as archivo:
            imagen = Image.open(archivo)
            self.assertLessEqual(max(imagen.size), 256)
