from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from src.config import CONFIG
from src.db.models import Users, AppIntegrations, OAuthAccounts
from src.db.mongo_db import MongoClient
from src.api.routes.auth_routes import auth_router
from src.api.routes.app_integration_routes import integration_router
from src.core.exceptions import AppError
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_db = MongoClient(CONFIG.MONGO_DB_URI)
    app.state.mongo_db = mongo_db
    await mongo_db.get_database(CONFIG.DATABASE_NAME)
    await mongo_db.init_beanie_odm(models=[Users, AppIntegrations, OAuthAccounts])

    yield


app = FastAPI(
    title="wFlow ---- AI Workflow Automation Tool",
    version=CONFIG.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(integration_router, prefix="/api/integration", tags=["App Integration"])

@app.exception_handler(AppError)
async def handle_app_error(req: Request, exc: AppError):
    logger.error(
        f"Error occurred, {exc.detail.error} with status {exc.detail.status_code}, at {req.base_url}"
    )
    return JSONResponse(
        status_code=exc.detail.status_code,
        content={
            "status_code": exc.detail.status_code,
            "message": exc.detail.message,
            "data": exc.data,
            "error": exc.detail.error,
        },
    )
