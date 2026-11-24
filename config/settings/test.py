from .base import *  # noqa: F401,F403

DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["CONN_HEALTH_CHECKS"] = False

MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}

DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SESION_UNICA = False
