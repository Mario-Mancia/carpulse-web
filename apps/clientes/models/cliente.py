from django.conf import settings
from django.db import models

from apps.core.constraints import en_lista
from apps.core.models.base import ModeloValidado
from apps.core.validators import validar_nombre_persona, validar_telefono


class UnidadDistancia(models.TextChoices):
    KILOMETROS = "KM", "Kilómetros"
    MILLAS = "MI", "Millas"


class UnidadVolumen(models.TextChoices):
    LITROS = "L", "Litros"
    GALONES = "GAL", "Galones"


class Cliente(ModeloValidado):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="id_usuario",
        related_name="cliente",
    )
    nombres = models.CharField(max_length=100, validators=[validar_nombre_persona])
    apellidos = models.CharField(max_length=100, validators=[validar_nombre_persona])
    correo = models.EmailField(max_length=150)
    telefono = models.CharField(max_length=25, null=True, blank=True, validators=[validar_telefono])
    unidad_distancia = models.CharField(max_length=2, choices=UnidadDistancia.choices, default=UnidadDistancia.KILOMETROS)
    unidad_volumen = models.CharField(max_length=3, choices=UnidadVolumen.choices, default=UnidadVolumen.LITROS)
    notificar_correo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    campos_texto_opcional = ("telefono",)

    class Meta:
        db_table = "clientes"
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        constraints = [
            en_lista("ck_clientes_unidad_distancia", "unidad_distancia", UnidadDistancia.values),
            en_lista("ck_clientes_unidad_volumen", "unidad_volumen", UnidadVolumen.values),
        ]
        indexes = [models.Index(fields=["correo"], name="idx_clientes_correo")]

    def __str__(self):
        return self.nombre_visible

    @property
    def nombre_visible(self):
        return f"{self.nombres} {self.apellidos}".strip() or self.correo

    def clean(self):
        super().clean()
        if self.correo:
            self.correo = self.correo.strip().lower()
