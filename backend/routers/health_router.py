"""
Router de health check.
Endpoint de monitoreo que verifica que la API y la base de datos respondan.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from utils.db import db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Health check para monitoreo (Render, balanceadores, CI).

    Devuelve 200 si la base responde a un SELECT 1, o 503 si no.
    No expone detalles internos del error.
    """
    if db.ping():
        return {"status": "healthy", "database": "up"}
    return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "down"})
