#This module starts our app and manage its life cycle

from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.src.app_api.v1.query_routes import data_router
from backend.src.utils.app_logger import custom_logging, shutdown_logging
from backend.src.db_connect.connection import engine

#Lifespan Management
@asynccontextmanager
async def lifespan(app:FastAPI):
    logger=custom_logging()
    logger.info("Talk2DB in service for you!!")
    yield
    logger.info("cleaning up DB connections")
    await engine.dispose()
    logger.info("All DB Connections closed successfully")
    logger.info("Talk2DB shutting down...")
    shutdown_logging()

#App Creation
app=FastAPI(title="Talk2DB",
            description="AI Powered that enables interaction with database using natural language",
            version="1.0.0",
            lifespan=lifespan
            )

#Router Integration
app.include_router(data_router)

#Base EndPoint
@app.get("/health")
def health_check():
    return{
        "status":"Online",
        "App":"Talk2DB",
        "docs":"/docs"
    }

#Creator
@app.get("/developer")
def creator():
    return{
        "APP_Creator":"Darshan Rajeev Naik",
        "Company":"Enventure Engineering Pvt Ltd",
        "employee_code":5452
    }

#uvicorn backend.src.main:app --reload
#uvicorn backend.src.main:app --host 127.0.0.1 --port 8000


