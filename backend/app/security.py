import hashlib
import os

PEPPER = os.getenv("SECRET_PEPPER", "unsafe-dev-pepper")


def hash_government_id(raw_id: str) -> str:
    """Hash the government ID with an application pepper.

    Raw IDs are never persisted.
    """
    normalized = "".join(ch for ch in raw_id.strip().upper() if ch.isalnum())
    digest = hashlib.sha256(f"{normalized}:{PEPPER}".encode("utf-8")).hexdigest()
    return digest
