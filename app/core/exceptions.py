import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    code = "app_error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.code.replace("_", " ")
        super().__init__(self.message)


class MemoryNotFoundError(AppError):
    code = "memory_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class PatternNotFoundError(AppError):
    code = "pattern_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class TaskNotFoundError(AppError):
    code = "task_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class RiskDetectionError(AppError):
    code = "risk_detection_error"


class MongoConnectionError(AppError):
    code = "mongo_connection_error"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class VectorStoreError(AppError):
    code = "vector_store_error"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class LLMServiceError(AppError):
    code = "llm_service_error"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class PromptNotFoundError(AppError):
    code = "prompt_not_found"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class FeatureNotImplementedError(AppError):
    code = "feature_not_implemented"
    status_code = status.HTTP_501_NOT_IMPLEMENTED


def error_payload(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    logger.warning("AppError: %s %s", exc.code, exc.message, exc_info=exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message),
    )


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("Validation error: %s", exc, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "validation_error", "message": str(exc)}},
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload("internal_server_error", "Internal server error"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
