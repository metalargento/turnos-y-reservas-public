"""
Rate limiting con slowapi.
Limita los intentos sobre endpoints sensibles (login y registro) por IP.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("rate_limit")


def client_ip(request: Request) -> str:
    """
    Obtiene la IP del cliente para agrupar los intentos.

    Detrás de un proxy (Render, Vercel) request.client es la IP del proxy, así que se
    usa el primer valor de X-Forwarded-For si existe.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip)


def auth_limit() -> str:
    """Límite para login y registro, configurable con AUTH_RATE_LIMIT (ej: 5/minute)."""
    return settings.auth_rate_limit


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Responde 429 con el mismo formato de error que el resto de la API."""
    logger.warning("Rate limit excedido", extra={"path": request.url.path})
    return JSONResponse(
        status_code=429,
        content={"error": True, "message": "Demasiados intentos. Probá de nuevo en un minuto.", "code": "RATE_LIMITED"},
        headers={"Retry-After": "60"},
    )
