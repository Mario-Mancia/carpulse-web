from apps.core.services import plataforma as servicio


def plataforma(request):
    configuracion = servicio.configuracion()
    return {
        "plataforma": configuracion,
        "nombre_plataforma": configuracion.nombre_plataforma if configuracion else "CarPulse",
        "recursos": servicio.recursos(),
    }
