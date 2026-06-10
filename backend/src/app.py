from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from src.config import CONFIG
from src.domains.users.routes import auth_router

# from src.domains.app_integrations.routes import integration_router
from src.domains.workflows.routes import workflow_router
from src.domains.webhooks.routes import webhooks_router
from src.core.response import AppError
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="wFlow ---- AI Workflow Automation Tool",
    version=CONFIG.APP_VERSION,
    lifespan=lifespan,
)


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CONFIG.FRONTEND_URL],  # Allows specific domains
    allow_credentials=True,  # Allows cookies and auth headers
    allow_methods=["*"],  # Allows all standard HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all request headers
)

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(
#     integration_router, prefix="/api/integration", tags=["App Integration"]
# )
app.include_router(workflow_router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])

from src.core.exc_handlers import app_error_handler, validation_exception_handler

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
