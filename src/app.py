from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.config import CONFIG
from src.db.mongo.schemas import Users, Nodes, Pipelines
from src.db.mongo.mongo_db import MongoClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_db = MongoClient(CONFIG.MONGO_DB_URI)
    app.state.mongo_db = mongo_db
    await mongo_db.get_database("wflow_db")
    await mongo_db.init_beanie_odm(models=[Users, Nodes, Pipelines])

    yield


app = FastAPI(
    title="wFlow ---- AI Workflow Automation Tool", version=CONFIG.APP_VERSION,
    lifespan=lifespan
)