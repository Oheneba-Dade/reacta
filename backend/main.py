from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.routers import auth, clips, search, tags
from backend.services.embeddings import embedding_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    embedding_service._get_model()
    yield


app = FastAPI(title="Reacta API", version="1.0.0", lifespan=lifespan)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(clips.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")


_STATUS_CODES = {
    400: "validation_error",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    500: "processing_error",
}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        body = detail
    else:
        error_code = _STATUS_CODES.get(exc.status_code, "error")
        body = {"error": error_code, "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=body)
