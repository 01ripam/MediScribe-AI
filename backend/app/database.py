import os
import logging

from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient, ReturnDocument

from .exceptions import (
    DatabaseConnectionError,
    MissingEnvironmentVariableError,
    DatabaseOperationError,
)

logger = logging.getLogger(__name__)

load_dotenv(".env.local")
load_dotenv(".env")

MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME") or os.getenv("MONGODB_DB") or "patient_platform"

if not MONGO_URI:
    raise MissingEnvironmentVariableError("MONGODB_URI or MONGO_URI")

try:
    _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test the connection
    _client.admin.command('ping')
    db = _client[MONGO_DB_NAME]
    logger.info("✓ Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Could not connect to MongoDB: {e}")
    print("Warning: Could not connect to MongoDB")
    print("Server will run but database operations will fail")
    db = None


def get_database():
    """
    Get the database connection.
    
    Raises:
        DatabaseConnectionError: If database is not connected.
        
    Returns:
        MongoDB database instance.
    """
    if db is None:
        raise DatabaseConnectionError(
            connection_string=MONGO_URI or "not configured",
        )
    return db


def next_sequence(name: str) -> int:
    """
    Get next sequence number for a counter.
    
    Args:
        name: Name of the counter.
        
    Returns:
        Next sequence number.
        
    Raises:
        DatabaseOperationError: If sequence counter operation fails.
    """
    if db is None:
        raise DatabaseConnectionError(connection_string=MONGO_URI or "not configured")

    try:
        row = db.counters.find_one_and_update(
            {"_id": name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(row["seq"])
    except Exception as e:
        raise DatabaseOperationError(
            operation=f"get_next_sequence_{name}",
            original_error=e,
        )


def ensure_indexes() -> None:
    """
    Ensure all required database indexes exist.
    
    Raises:
        DatabaseOperationError: If index creation fails.
    """
    if db is None:
        raise DatabaseConnectionError(connection_string=MONGO_URI or "not configured")

    try:
        # Patient indexes
        db.patients.create_index([("id", ASCENDING)], unique=True)
        db.patients.create_index([("phone", ASCENDING)], unique=True)
        db.patients.create_index([("govt_id_hash", ASCENDING)], unique=True, sparse=True)

        # Doctor indexes
        db.doctors.create_index([("id", ASCENDING)], unique=True)
        db.doctors.create_index([("specialization", ASCENDING)])

        # Appointment indexes
        db.appointments.create_index([("id", ASCENDING)], unique=True)
        db.appointments.create_index([("patient_id", ASCENDING), ("created_at", ASCENDING)])
        db.appointments.create_index([("doctor_id", ASCENDING), ("slot", ASCENDING)])

        # Medical Records indexes
        db.medical_records.create_index([("id", ASCENDING)], unique=True)
        db.medical_records.create_index([("patient_id", ASCENDING), ("date", ASCENDING)])

        # Doctor Portal indexes
        db.doctor_portal_appointments.create_index([("doctorId", ASCENDING), ("appointmentDate", ASCENDING)])
        db.doctor_portal_appointments.create_index([("status", ASCENDING)])
        db.doctor_portal_consultations.create_index([("doctorId", ASCENDING), ("date", ASCENDING)])
        db.doctor_portal_consultations.create_index([("patientUserId", ASCENDING), ("date", ASCENDING)])
        db.doctor_portal_reports.create_index([("doctorId", ASCENDING), ("createdAt", ASCENDING)])
        db.doctor_portal_reports.create_index([("patientEmail", ASCENDING), ("createdAt", ASCENDING)])
        
        logger.info("✓ All database indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")
        raise DatabaseOperationError(
            operation="create_indexes",
            original_error=e,
        )
