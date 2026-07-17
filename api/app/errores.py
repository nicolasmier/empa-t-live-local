from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ErrorAPI(Exception):
    """Error de dominio con envelope propio (Anexo B §1: `{ "error": { "code", "message" } }`)."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def _envelope(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def registrar_manejadores_error(app: FastAPI) -> None:
    @app.exception_handler(ErrorAPI)
    def _manejar_error_api(request: Request, exc: ErrorAPI) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_envelope(exc.code, exc.message))

    @app.exception_handler(HTTPException)
    def _manejar_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        detalle = exc.detail if isinstance(exc.detail, str) else "Error inesperado."
        return JSONResponse(status_code=exc.status_code, content=_envelope("error", detalle))

    @app.exception_handler(RequestValidationError)
    def _manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_envelope("validacion", "Los datos enviados no son válidos."),
        )
