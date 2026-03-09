
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .core.config import settings
from .database.mongo import init_indexes
from .middleware.idempotency import IdempotencyMiddleware
from .routers import auth
from .modules.admin import router as admin
from .modules.customer import router as customer
from .modules.manager import router as manager
from .modules.payments import router as payments
from .modules.transactions import router as transactions
from .modules.verification import router as verification
from .modules.wallet import router as wallet

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(IdempotencyMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_indexes()

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(customer, prefix=settings.API_PREFIX)
app.include_router(manager, prefix=settings.API_PREFIX)
app.include_router(verification, prefix=settings.API_PREFIX)
app.include_router(admin, prefix=settings.API_PREFIX)
app.include_router(transactions, prefix=settings.API_PREFIX)
app.include_router(wallet, prefix=settings.API_PREFIX)
app.include_router(payments, prefix=settings.API_PREFIX)


def _friendly_validation_errors(exc: RequestValidationError) -> list[dict]:
    try:
        raw_errors = exc.errors(include_url=False)
    except TypeError:
        raw_errors = exc.errors()

    friendly: list[dict] = []
    for err in raw_errors:
        loc = err.get("loc") or ()
        field_parts = [str(part) for part in loc if str(part) not in {"body", "query", "path"}]
        field = ".".join(field_parts) if field_parts else "request"
        message = str(err.get("msg") or "Invalid value")
        friendly.append(
            {
                "field": field,
                "message": message,
            }
        )
    return friendly


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = _friendly_validation_errors(exc)
    first = errors[0] if errors else {"field": "request", "message": "Validation failed. Please check your input."}
    prefix = "Validation failed"
    if first["field"] != "request":
        prefix = f"{first['field'].replace('_', ' ').capitalize()}"
    detail = f"{prefix}: {first['message']}"
    return JSONResponse(
        status_code=422,
        content={
            "detail": detail,
            "errors": errors,
        },
    )

@app.get('/')
async def health():
    return {"status": "ok"}
