import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .routers.appointments import router as appointments_router
from .routers.auth import router as auth_router
from .routers.doctors import router as doctors_router
from .routers.records import router as records_router
from .seed import seed_data

load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "Patient Side API"), version="1.0.0")

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
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


app.include_router(auth_router)
app.include_router(doctors_router)
app.include_router(appointments_router)
app.include_router(records_router)


@app.get("/")
def health():
    return {"status": "ok", "service": "patient-side-api"}
