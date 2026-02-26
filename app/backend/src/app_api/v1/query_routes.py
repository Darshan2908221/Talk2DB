#This module creates the routers for the backend app
from fastapi import APIRouter, Depends, HTTPException
from backend.src.db_connect.connection import get_session
from backend.src.data_fetch.query_orchestration import orchestrator
from backend.src.data_fetch.db_schema import get_databases
from backend.src.utils.app_logger import logger
from backend.src.app_api.v1.query_ip_validation import UserInputValidation
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

class NotEnoughInformation(Exception):
    pass

#Router Defination
data_router=APIRouter(
    prefix="/sql",
    tags=["Natural-language-to-DB-Engine"]
)

@data_router.get("/databases", response_model=List[str])
async def get_db():
    """
    This Route Handler Fetches all non-system MySQL databases to populate the frontend dropdown.
    """
    try:
        databases=await get_databases()
        return databases
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch database schemas %s",e)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch database schemas"
        )

@data_router.post("/ask")
async def get_data(request:UserInputValidation, db_session:AsyncSession=Depends(get_session)):
    """
    This Route Handler Fetches data that the user asked for
    """
    try:
        results=await orchestrator(
            user_query=request.user_query,
            chosen_db=request.database,
            session=db_session
            )
        if results.get("mysql_query","").strip().upper()=="SELECT 1":
            raise NotEnoughInformation
        
        return results
    
    except NotEnoughInformation:
        logger.warning("Information was not enough to generate valid sql to answer user query," \
        "LLM1 not generated enough tables")
        raise HTTPException(status_code=422,
                            detail="Information was not enough to generate valid sql to answer user query," \
        "LLM1 not generated enough tables")
    
    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Natural Language to DB Engine Error %s",e)
        raise HTTPException(
            status_code=500,
            detail="Natural-Language-TO-DB-Engine-Error"
        )
        




