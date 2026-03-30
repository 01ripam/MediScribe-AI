import os

from fastapi import Header, HTTPException

APP_API_KEY = os.getenv("APP_API_KEY", "")


def require_app_api_key(x_api_key: str | None = Header(default=None)) -> None:
    # If APP_API_KEY is set, every client must include the same key in X-API-Key.
    if not APP_API_KEY:
        return
    if x_api_key != APP_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
