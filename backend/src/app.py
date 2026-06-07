from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from src.config import CONFIG
from src.db.mongo_db import MongoClient
from src.api.routes.auth_routes import auth_router
from src.api.routes.app_integration_routes import integration_router
from src.domains.workflows.routes import workflow_router
from src.core.response import AppError
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_db = MongoClient(CONFIG.MONGO_DB_URI)
    app.state.mongo_db = mongo_db
    await mongo_db.get_database(CONFIG.DATABASE_NAME)
    await mongo_db.init_beanie_odm()

    yield

app = FastAPI(
    title="wFlow ---- AI Workflow Automation Tool",
    version=CONFIG.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(
    integration_router, prefix="/api/integration", tags=["App Integration"]
)
app.include_router(workflow_router, prefix="/api/workflows", tags=["Workflows"])


from src.core.exc_handlers import app_error_handler, validation_exception_handler

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler) 