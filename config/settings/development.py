import os

from .base import *  # noqa: F401,F403

DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"

DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["CONN_HEALTH_CHECKS"] = False
