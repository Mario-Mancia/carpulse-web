from django.conf import settings
from django.db import models

from apps.core.constraints import en_lista
from apps.core.models.base import ModeloValidado
from apps.core.validators import validar_ruta_relativa


class ClaveRecurso(models.TextChoices):
    LOGO = "LOGO", "Logo"
    LOGO_OSCURO = "LOGO_OSCURO", "Logo para tema oscuro"
    FAVICON = "FAVICON", "Icono de la pestaña"
    HERO_INICIO = "HERO_INICIO", "Imagen principal del inicio"
    IMAGEN_ACCESO = "IMAGEN_ACCESO", "Imagen de acceso y registro"


class RecursoGrafico(ModeloValidado):
    clave = models.CharField(max_length=40, unique=True, choices=ClaveRecurso.choices)
    ruta = models.TextField(validators=[validar_ruta_relativa])
    texto_alternativo = models.CharField(max_length=150, null=True, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="id_actualizado_por",
        related_name="recursos_graficos_actualizados",
    )

    campos_texto_opcional = ("texto_alternativo",)

    class Meta:
        db_table = "recursos_graficos"
        verbose_name = "recurso gráfico"
        verbose_name_plural = "recursos gráficos"
        constraints = [en_lista("ck_recursos_graficos_clave", "clave", ClaveRecurso.values)]

    def __str__(self):
        return self.clave

    @property
    def url(self):
        from django.core.files.storage import default_storage

        return default_storage.url(self.ruta)
