"""
Punto de entrada de la aplicación FastAPI.
Solo configuración de la app y registro de middleware/routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import settings
from utils.logger import logger
from utils.db import db
from middleware.error_handler import global_error_handler
from middleware.auth import auth_middleware
from middleware.cors_policy import is_origin_allowed, cors_headers
from middleware.rate_limit import limiter, rate_limit_handler
from slowapi.errors import RateLimitExceeded

# Routers
from routers.health_router import router as health_router
from routers.auth_router import router as auth_router
from routers.onboarding_router import router as onboarding_router
from routers.business_router import router as business_router
from routers.services_router import router as services_router
from routers.branches_router import router as branches_router
from routers.professionals_router import router as professionals_router
from routers.availability_router import router as availability_router, blocks_router as schedule_blocks_router
from routers.booking_router import router as booking_router
from routers.booking_public_router import router as booking_public_router
from routers.dashboard_router import router as dashboard_router
from routers.upload_router import router as upload_router
from routers.google_oauth_router import router as google_oauth_router
from migrations.run_migrations import run_migrations


# Crear aplicación
app = FastAPI(
    title="Sistema de Turnos y Reservas",
    description="API para gestión de turnos y reservas de negocios",
    version="1.0.1"
)

# Registrar handler global de errores
app.add_exception_handler(Exception, global_error_handler)

# Rate limiting (slowapi): limiter compartido + respuesta 429 con el formato de error de la API
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


# Middleware de headers de seguridad
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Agrega headers de seguridad HTTP a todas las respuestas."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if "server" in response.headers:
            del response.headers["server"]
        return response


# CORS: solo orígenes exactos de ALLOWED_ORIGINS (localhost solo fuera de producción)
class FlexibleCORSMiddleware(BaseHTTPMiddleware):
    """Aplica la política de CORS definida en middleware/cors_policy.py."""

    async def dispatch(self, request, call_next):
        from fastapi.responses import Response

        origin = request.headers.get("origin", "")
        is_allowed = is_origin_allowed(origin)

        # Manejar preflight requests (OPTIONS)
        if request.method == "OPTIONS":
            return Response(status_code=200, headers=cors_headers(origin) if is_allowed else {})

        response = await call_next(request)

        if is_allowed:
            response.headers.update(cors_headers(origin))

        return response


# Middlewares
app.add_middleware(FlexibleCORSMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)


# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Inicializa la aplicación al arrancar."""
    logger.info("Iniciando aplicación...")
    run_migrations()
    db.connect()
    logger.info("Aplicación iniciada correctamente")


@app.on_event("shutdown")
async def shutdown_event():
    """Limpia recursos al cerrar la aplicación."""
    logger.info("Cerrando aplicación...")
    db.disconnect()
    logger.info("Aplicación cerrada")


# Root
@app.get("/")
async def root():
    """Root endpoint - información básica de la API."""
    return {
        "name": "Sistema de Turnos y Reservas API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Registrar routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(business_router)
app.include_router(services_router)
app.include_router(branches_router)
app.include_router(professionals_router)
app.include_router(availability_router)
app.include_router(schedule_blocks_router)
app.include_router(booking_router)
app.include_router(booking_public_router)
app.include_router(dashboard_router)
app.include_router(upload_router)
app.include_router(google_oauth_router)
