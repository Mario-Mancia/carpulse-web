from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.core.validators import (
    validar_codigo,
    validar_nombre_persona,
    validar_nombre_archivo,
    validar_objeto_json,
    validar_ruta_relativa,
    validar_telefono,
)


class ValidadoresTests(SimpleTestCase):
    def test_nombre_persona(self):
        for valor in ("Ana", "José María", "O'Brien", "Ana-Lucía", "Jr."):
            validar_nombre_persona(valor)
        for valor in ("Ana3", "", "123", "Ana_", "<b>"):
            with self.assertRaises(ValidationError):
                validar_nombre_persona(valor)

    def test_telefono(self):
        for valor in ("+503 7000-0000", "70000000", "(503) 2222 3333"):
            validar_telefono(valor)
        for valor in ("abc", "12", "+", "7000-abc"):
            with self.assertRaises(ValidationError):
                validar_telefono(valor)

    def test_codigo(self):
        for valor in ("EMP-001", "ab_c/12"):
            validar_codigo(valor)
        for valor in ("ab", "-abc", "a b c", "x" * 41):
            with self.assertRaises(ValidationError):
                validar_codigo(valor)

    def test_ruta_relativa(self):
        validar_ruta_relativa("plataforma/logo.webp")
        for valor in ("../x", "/etc/passwd", "a//b", "C:\\x", "http://x/y", "a/./b", " a/b", "~/x"):
            with self.assertRaises(ValidationError):
                validar_ruta_relativa(valor)

    def test_nombre_archivo(self):
        validar_nombre_archivo("foto.png")
        for valor in (".oculto", "a/b.png", "a\\b.png", ""):
            with self.assertRaises(ValidationError):
                validar_nombre_archivo(valor)

    def test_objeto_json(self):
        validar_objeto_json(None)
        validar_objeto_json({"a": 1})
        with self.assertRaises(ValidationError):
            validar_objeto_json([1, 2])
        with self.assertRaises(ValidationError):
            validar_objeto_json({"a": "x" * 200000})
