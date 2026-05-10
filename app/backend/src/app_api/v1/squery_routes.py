#This module creates the routers for the backend app
from fastapi import APIRouter, Depends, HTTPException, Path
from backend.src.db_connect.sq_db_creation import sget_user_uploads_registry_db_session, sget_chat_history_db_session, sget_useruploads_db_session
from backend.src.data_fetch.squery_orchestration import 
from backend.src.data_fetch.sq_chat_history import supdate_chat_history, supdate_user_uploads_registry, get_sdatabase_names, get_schat_names, get_schat, delete_schat
from backend.src.utils.app_logger import logger
from backend.src.app_api.v1.query_ip_validation import sUserInputValidation, sChatHistoryInputValidation, sChatInsertInputValidation
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse


class NotEnoughInformation(Exception):
    pass

#Router Defination
data_router=APIRouter(
    prefix="/sql",
    tags=["Natural-language-to-DB-Engine"]
)

@data_router.post("/sask")
def get_data(request:sUserInputValidation, db_session:Session=Depends(get_session)):
    """This Route Handler Fetches data that the user asked"""
    chat_history_build:list[BaseMessage]=[]
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

@data_router.get("/db_name/{user_id}", response_model=dict[str, str])
async def get_userselected_db_names(db_session:AsyncSession=Depends(get_session), user_id:int=Path(..., description="user_id to fetch userchosen database names")):
    """This router fetches userchosen database names"""
    try:
        result=await get_database_names(session=db_session, p_user_id=user_id)
        return {r["chat_id"]:r["chat_name"] for r in result}
    except Exception as e:
        logger.exception("Error in get_userselected_db_names %s",e)
        raise HTTPException(status_code=500, detail="Error in calling function to fetch userselected database names from chathistory database")
    

@data_router.post("/chat_history", response_model=list[dict])
async def get_chathistory(request:ChatHistoryInputValidation, db_session:AsyncSession=Depends(get_session)):
    """This router fetches the chathistory"""
    try:
        result=await get_chat(session=db_session, user_id=request.user_id, chat_id=request.chat_id)
        return result
    except Exception as e:
        logger.exception("Error in get_chathistory route handler %s", e)
        raise HTTPException(status_code=500, detail="Error in calling function to fetch chat history")

@data_router.post("/insert_conversation")
async def insert_chat(request:ChatInsertInputValidation, db_session:AsyncSession=Depends(get_session)):
    "Router to save a new chat message. Validates the role as either 'human' or 'ai'."
    try:
        result=await save_chathistory(session=db_session, chat_name=request.chat_name, user_id=request.user_id, chat_id=request.chat_id, db_name=request.database, role=request.role, message=request.message, sql_query=request.sql_query)
        return JSONResponse(status_code=200, content="Successfully_Inserted")
    except Exception as e:
        logger.exception("Error in insert_chat route handler %s", e)
        raise HTTPException(status_code=500, detail="Error in calling function to insert conversation into chathistory")     

@data_router.get("/chatnames/{user_id}")
async def fetch_chatnames(user_id:int=Path(..., description="userid to fetch chatnames"), db_session:AsyncSession=Depends(get_session)):
    """This router handler is to fetch chatnames for a given user"""
    try:
        result=await get_chat_names(session=db_session, user_id=user_id)
        return {s['chat_id']: s['chat_name'] for s in result}
    except Exception as e:
        logger.exception("Error in fetch_chat_names route handler %s",e)
        raise HTTPException(status_code=500, detail="Error in calling function to fetch chatnames from chathistory")

@data_router.delete("/delete_chathistory")
async def delete_chathistory(request:ChatHistoryInputValidation, db_session:AsyncSession=Depends(get_session)):
    """This route handler delete chat_history"""
    try:
        result=await delete_chat(session=db_session, user_id=request.user_id, chat_id=request.chat_id)
        return JSONResponse(status_code=200, content="Successfully deleted chathistory")
    except Exception as e:
        logger.exception("Error in delete_chathistory route handler")
        raise HTTPException(status_code=500, detail="Error in calling function to delete chat history")
    