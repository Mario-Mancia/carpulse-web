from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models.base import ModeloValidado
from apps.core.validators import validar_telefono

CLAVE_CACHE = "configuracion_plataforma"


class ConfiguracionPlataforma(ModeloValidado):
    nombre_plataforma = models.CharField(max_length=150, default="CarPulse")
    correo_contacto = models.EmailField(max_length=150, null=True, blank=True)
    telefono_contacto = models.CharField(max_length=25, null=True, blank=True, validators=[validar_telefono])
    sitio_web = models.URLField(max_length=200, null=True, blank=True)
    max_vehiculos_por_cliente = models.PositiveSmallIntegerField(
        default=3, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    retencion_sincronizaciones_dias = models.PositiveSmallIntegerField(
        default=90, validators=[MinValueValidator(7), MaxValueValidator(365)]
    )
    recordatorio_anticipacion_dias = models.PositiveSmallIntegerField(
        default=7, validators=[MaxValueValidator(60)]
    )
    recordatorio_anticipacion_km = models.PositiveIntegerField(default=500, validators=[MaxValueValidator(5000)])
    actualizado_en = models.DateTimeField(auto_now=True)

    campos_texto_opcional = ("correo_contacto", "telefono_contacto", "sitio_web")

    class Meta:
        db_table = "configuracion_plataforma"
        verbose_name = "configuración de la plataforma"
        verbose_name_plural = "configuración de la plataforma"

    def __str__(self):
        return self.nombre_plataforma

    def clean(self):
        super().clean()
        if self._state.adding and ConfiguracionPlataforma.objects.exists():
            raise ValidationError("Solo puede existir un registro de configuración de la plataforma.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete(CLAVE_CACHE)

    def delete(self, *args, **kwargs):
        resultado = super().delete(*args, **kwargs)
        cache.delete(CLAVE_CACHE)
        return resultado
