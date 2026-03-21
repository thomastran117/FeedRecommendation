from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import rabbitmq
from app.middleware import ErrorHandlingMiddleware
from app.routers import auth, events


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    yield
    await rabbitmq.disconnect()


app = FastAPI(title="API Server", lifespan=lifespan)

app.add_middleware(ErrorHandlingMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(events.router, prefix="/events", tags=["events"])


@app.get("/health")
def health():
    return {"status": "ok"}
