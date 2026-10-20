"""
Política de CORS compartida.
Decide si un origen puede llamar a la API, para el middleware de CORS y el de autenticación.
"""
import re
from config.settings import settings

LOCAL_ORIGIN = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")

CORS_ALLOW_METHODS = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
CORS_ALLOW_HEADERS = "Authorization, Content-Type"


def is_origin_allowed(origin: str) -> bool:
    """
    Indica si el origen está permitido.

    Solo acepta coincidencias exactas con ALLOWED_ORIGINS. Los orígenes locales
    (localhost, 127.0.0.1) se aceptan únicamente fuera de producción.
    """
    if not origin:
        return False
    allowed = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
    if origin in allowed:
        return True
    return settings.app_env != "production" and bool(LOCAL_ORIGIN.match(origin))


def cors_headers(origin: str) -> dict:
    """Devuelve los headers CORS para un origen ya validado."""
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": CORS_ALLOW_METHODS,
        "Access-Control-Allow-Headers": CORS_ALLOW_HEADERS,
        "Vary": "Origin",
    }
