from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.models import ClaveRecurso, ConfiguracionPlataforma, RecursoGrafico


class ConfiguracionPlataformaTests(TestCase):
    def test_semilla_crea_un_registro_con_nombre_carpulse(self):
        self.assertEqual(ConfiguracionPlataforma.objects.count(), 1)
        self.assertEqual(ConfiguracionPlataforma.objects.get().nombre_plataforma, "CarPulse")
        self.assertEqual(ConfiguracionPlataforma.objects.get().max_vehiculos_por_cliente, 3)

    def test_no_permite_un_segundo_registro(self):
        with self.assertRaises(ValidationError):
            ConfiguracionPlataforma(nombre_plataforma="Otra").save()
        self.assertEqual(ConfiguracionPlataforma.objects.count(), 1)

    def test_valida_rangos(self):
        cfg = ConfiguracionPlataforma.objects.get()
        cfg.max_vehiculos_por_cliente = 0
        with self.assertRaises(ValidationError):
            cfg.save()
        cfg.max_vehiculos_por_cliente = 11
        with self.assertRaises(ValidationError):
            cfg.save()

    def test_textos_opcionales_vacios_se_guardan_como_nulos(self):
        cfg = ConfiguracionPlataforma.objects.get()
        cfg.correo_contacto = ""
        cfg.save()
        cfg.refresh_from_db()
        self.assertIsNone(cfg.correo_contacto)


class RecursoGraficoTests(TestCase):
    def test_clave_invalida_se_rechaza(self):
        with self.assertRaises(ValidationError):
            RecursoGrafico(clave="NO_EXISTE", ruta="plataforma/a.webp").save()

    def test_ruta_insegura_se_rechaza(self):
        with self.assertRaises(ValidationError):
            RecursoGrafico(clave=ClaveRecurso.LOGO, ruta="../a.webp").save()

    def test_clave_unica(self):
        RecursoGrafico(clave=ClaveRecurso.LOGO, ruta="plataforma/a.webp").save()
        with self.assertRaises(ValidationError):
            RecursoGrafico(clave=ClaveRecurso.LOGO, ruta="plataforma/b.webp").save()
