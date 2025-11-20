from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .errors import AgentError, ConfigurationError, ExternalServiceError, ToolExecutionError


def _build_payload(exception: AgentError) -> dict:
    payload = {"error": str(exception)}
    if getattr(exception, "detail", None):
        payload["detail"] = exception.detail
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(_: Request, exc: ConfigurationError) -> JSONResponse:
        return JSONResponse(status_code=500, content=_build_payload(exc))

    @app.exception_handler(ExternalServiceError)
    async def external_service_error_handler(_: Request, exc: ExternalServiceError) -> JSONResponse:
        return JSONResponse(status_code=502, content=_build_payload(exc))

    @app.exception_handler(ToolExecutionError)
    async def tool_execution_error_handler(_: Request, exc: ToolExecutionError) -> JSONResponse:
        return JSONResponse(status_code=500, content=_build_payload(exc))

    @app.exception_handler(AgentError)
    async def generic_agent_error_handler(_: Request, exc: AgentError) -> JSONResponse:
        return JSONResponse(status_code=500, content=_build_payload(exc))

