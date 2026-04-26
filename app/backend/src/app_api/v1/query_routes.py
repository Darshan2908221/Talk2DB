#This module creates the routers for the backend app
from fastapi import APIRouter, Depends, HTTPException, Path
from backend.src.db_connect.connection import get_session
from backend.src.data_fetch.query_orchestration import orchestrator
from backend.src.data_fetch.db_schema import get_databases
from backend.src.data_fetch.chat_history import get_chat, save_chathistory, get_chat_names
from backend.src.utils.app_logger import logger
from backend.src.app_api.v1.query_ip_validation import UserInputValidation, ChatHistoryInputValidation, ChatInsertInputValidation
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse


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
    """This Route Handler Fetches data that the user asked"""
    chat_history_build=[]
    try:  
        for row in request.chat_history:
            if row["role"]=="user":
                chat_history_build.append(HumanMessage(row["message"]))
            else:
                chat_history_build.append(AIMessage(row["message"]))

        results=await orchestrator(
            user_query=request.user_query,
            chosen_db=request.database,
            chat_history=chat_history_build,
            session=db_session
            )
        
        # if isinstance(results, str):
        #     return {"final_response": results}

        # if results.get("mysql_query","").strip().upper()=="SELECT 1":
        #     raise NotEnoughInformation

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
            detail=f"Natural-Language-TO-DB-Engine-Error,{e}"
        )

@data_router.post("/chat_history", response_model=list[dict])
async def get_chathistory(request:ChatHistoryInputValidation, db_session:AsyncSession=Depends(get_session)):
    """This router fetches the chathistory"""
    try:
        result=await get_chat(session=db_session, user_id=request.user_id, session_id=request.session_id)
        return result
    except Exception as e:
        logger.exception("Error in get_chathistory route handler %s", e)
        raise HTTPException(status_code=500, detail="Error in calling function to fetch chat history")

@data_router.post("/insert_conversation")
async def insert_chat(request:ChatInsertInputValidation, db_session:AsyncSession=Depends(get_session)):
    "Router to save a new chat message. Validates the role as either 'human' or 'ai'."
    try:
        result=await save_chathistory(session=db_session, chat_name=request.chat_name, user_id=request.user_id, session_id=request.session_id, role=request.role, message=request.message)
        return JSONResponse(status_code=200, content="Successfully_Inserted")
    except Exception as e:
        logger.exception("Error in insert_chat route handler %s", e)
        raise HTTPException(status_code=500, detail="Error in calling function to insert conversation into chathistory")     

@data_router.get("/chatnames/{user_id}")
async def fetch_chatnames(user_id:int=Path(description="userid to fetch chatnames"), db_session:AsyncSession=Depends(get_session)):
    """This router handler is to fetch chatnames for a given user"""
    try:
        result=await get_chat_names(session=db_session, user_id=user_id)
        return {s['session_id']: s['chat_name'] for s in result}
    except Exception as e:
        logger.exception("Error in fetch_chat_names route handler %s",e)
        raise HTTPException(status_code=500, detail="Error in calling function to fetch chatnames from chathistory")



