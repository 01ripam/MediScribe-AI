"""
Exception handlers for FastAPI application.

This module provides centralized exception handling for all custom exceptions,
converting them to appropriate HTTP responses with consistent error formatting.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import PatientPlatformException, DatabaseException, AuthenticationException

logger = logging.getLogger(__name__)


class ExceptionResponseModel:
    """Format for standardized error responses."""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.request_id = request_id
    
    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        response = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }
        if self.request_id:
            response["request_id"] = self.request_id
        return response


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(PatientPlatformException)
    async def patient_platform_exception_handler(
        request: Request, exc: PatientPlatformException
    ) -> JSONResponse:
        """Handle custom Patient Platform exceptions."""
        
        # Log exception details
        log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
        logger_func = logger.warning if log_level == logging.WARNING else logger.error
        
        log_message = f"{exc.error_code}: {exc.message}"
        if exc.original_error:
            log_message += f" | Original error: {str(exc.original_error)}"
        logger_func(log_message, extra={"details": exc.details})
        
        # Create response
        response_model = ExceptionResponseModel(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=request.headers.get("X-Request-ID", None),
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_model.to_dict(),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
            exc_info=exc,
        )
        
        # Don't expose internal error details to client
        response_model = ExceptionResponseModel(
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            details={},
            request_id=request.headers.get("X-Request-ID", None),
        )
        
        return JSONResponse(
            status_code=500,
            content=response_model.to_dict(),
        )
