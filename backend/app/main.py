import os
import logging

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_security import require_app_api_key
from .database import ensure_indexes, get_database
from .exception_handlers import register_exception_handlers
from .exceptions import DatabaseConnectionError
from .routers.appointments import router as appointments_router
from .routers.auth import router as auth_router
from .routers.doctor_portal import router as doctor_portal_router
from .routers.doctors import router as doctors_router
from .routers.payments import router as payments_router
from .routers.records import router as records_router
from .seed import seed_data

logger = logging.getLogger(__name__)

load_dotenv(".env.local")

app = FastAPI(title=os.getenv("APP_NAME", "Patient Side API"), version="1.0.0")

# Register exception handlers
register_exception_handlers(app)

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
allow_credentials = "*" not in origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize database and seed data on startup."""
    try:
        db = get_database()
        ensure_indexes()
        seed_data(db)
        logger.info("✓ Application startup successful")
    except DatabaseConnectionError as e:
        logger.error(f"Database connection failed on startup: {e.message}")
        logger.warning("Server will still start but database operations will fail")
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}", exc_info=e)
        logger.warning("Server will still start but some features may not work")


protected = [Depends(require_app_api_key)]

app.include_router(auth_router, dependencies=protected)
app.include_router(doctors_router, dependencies=protected)
app.include_router(appointments_router, dependencies=protected)
app.include_router(payments_router, dependencies=protected)
app.include_router(records_router, dependencies=protected)
app.include_router(doctor_portal_router, dependencies=protected)


@app.get("/")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "patient-side-api"}
