from collections import namedtuple

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core.imagenes import eliminar_imagen, guardar_imagen_publica, normalizar_imagen
from apps.core.models import CLAVE_CACHE, ClaveRecurso, ConfiguracionPlataforma, RecursoGrafico

CARPETA_RECURSOS = "plataforma"
LADO_MAXIMO = {
    ClaveRecurso.FAVICON: 256,
    ClaveRecurso.LOGO: 800,
    ClaveRecurso.LOGO_OSCURO: 800,
    ClaveRecurso.HERO_INICIO: 1920,
    ClaveRecurso.IMAGEN_ACCESO: 1280,
}
CLAVE_CACHE_RECURSOS = "recursos_graficos"

RecursoVista = namedtuple("RecursoVista", "url alt")


def configuracion():
    valor = cache.get(CLAVE_CACHE)
    if valor is None:
        valor = ConfiguracionPlataforma.objects.first()
        if valor is not None:
            cache.set(CLAVE_CACHE, valor, 300)
    return valor


def recursos():
    valor = cache.get(CLAVE_CACHE_RECURSOS)
    if valor is None:
        valor = {r.clave.lower(): RecursoVista(r.url, r.texto_alternativo or "") for r in RecursoGrafico.objects.all()}
        cache.set(CLAVE_CACHE_RECURSOS, valor, 300)
    return valor


def _limpiar_cache():
    cache.delete(CLAVE_CACHE_RECURSOS)
    cache.delete(CLAVE_CACHE)


@transaction.atomic
def asignar_recurso(clave, archivo, usuario=None, texto_alternativo=""):
    if clave not in ClaveRecurso.values:
        raise ValidationError("El recurso gráfico indicado no existe.")
    if archivo.size > getattr(settings, "IMAGEN_MAX_BYTES", 2097152):
        raise ValidationError("La imagen supera el tamaño máximo permitido.")
    contenido, extension = normalizar_imagen(archivo, maximo=LADO_MAXIMO[clave])
    nueva_ruta = guardar_imagen_publica(CARPETA_RECURSOS, contenido, extension)
    existente = RecursoGrafico.objects.filter(clave=clave).first()
    ruta_anterior = existente.ruta if existente else None
    try:
        if existente is None:
            existente = RecursoGrafico(clave=clave)
        existente.ruta = nueva_ruta
        existente.texto_alternativo = texto_alternativo
        existente.actualizado_por = usuario
        existente.save()
    except Exception:
        eliminar_imagen(nueva_ruta)
        raise
    if ruta_anterior and ruta_anterior != nueva_ruta:
        transaction.on_commit(lambda: eliminar_imagen(ruta_anterior))
    transaction.on_commit(_limpiar_cache)
    return existente


@transaction.atomic
def quitar_recurso(clave):
    recurso = RecursoGrafico.objects.filter(clave=clave).first()
    if recurso is None:
        return False
    ruta = recurso.ruta
    recurso.delete()
    transaction.on_commit(lambda: eliminar_imagen(ruta))
    transaction.on_commit(_limpiar_cache)
    return True
