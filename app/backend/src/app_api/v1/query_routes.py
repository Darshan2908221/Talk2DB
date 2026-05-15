#This module creates the routers for the backend app
from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, UploadFile
from backend.src.db_connect.connection import engine, get_session
from backend.src.data_fetch.query_orchestration import orchestrator, uploads_orchestrator
from backend.src.data_fetch.db_schema import get_database_catalog, get_databases, refresh_databases, DBNotFoundError
from backend.src.data_fetch.chat_history import get_database_names, get_chat, save_chathistory, get_chat_names, delete_chat
from backend.src.data_fetch.tablecreation import datacleaning, delete_useruploads_metadata, normalize_table_name, save_to_useruploadsdb, save_useruploads_metadata
from backend.src.utils.app_logger import logger
from backend.src.app_api.v1.query_ip_validation import UserInputValidation, ChatInsertInputValidation, ChatHistoryInputValidation
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
import asyncio

class NotEnoughInformation(Exception):
    pass

#Router Defination
data_router=APIRouter(
    prefix="/sql",
    tags=["Natural-language-to-DB-Engine"]
)

#TO GET DATABASES
@data_router.get("/databases", response_model=List[str])
async def get_db(refresh: bool=False):
    """
    This Route Handler Fetches all non-system MySQL databases to populate the frontend dropdown.
    """
    try:
        if refresh:
            databases=await refresh_databases()
        else:
            databases=await get_databases()
        return databases
    except DBNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail=f"No datatbases found"
        )
    except Exception as e:
        logger.exception("Failed to fetch database schemas %s",e)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch database schemas, Internal server error"
        )

@data_router.get("/database_catalog")
async def scan_database_catalog(refresh: bool=False):
    """Scans all available databases and returns table/column metadata."""
    try:
        return await get_database_catalog(refresh=refresh)
    except DBNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail=f"No datatbases found"
        )
    except Exception as e:
        logger.exception("Failed to scan database catalog %s", e)
        raise HTTPException(status_code=500, detail="Failed to scan database catalog")


# TO ASK QUESTIONS
@data_router.post("/ask")
async def get_data(request:UserInputValidation, db_session:AsyncSession=Depends(get_session)):
    """This Route Handler Fetches data that the user asked"""
    chat_history_build:list[BaseMessage]=[]
    try:  
        for row in request.chat_history:
            if row["role"]=="user":
                chat_history_build.append(HumanMessage(row["message"]))
            else:
                chat_history_build.append(AIMessage(row["message"]))
        
        if request.database=="useruploads":
            logger.info("Invoking uploads_orchestrator")
            results=await uploads_orchestrator(
                user_query=request.user_query,
                user_id=request.user_id,
                chat_id=request.chat_id,
                chosen_db=request.database,
                chat_history=chat_history_build,
                session=db_session
                )
            logger.info("uploads_orchestrator worked successfully")
            
        else:
            logger.info("Invoking Database_orchestrator")
            results=await orchestrator(
                user_query=request.user_query,
                chosen_db=request.database,
                chat_history=chat_history_build,
                session=db_session
                )
            logger.info("uploads_orchestrator worked successfully")

        return results
    
        # if results.get("mysql_query","").strip().upper()=="SELECT 1":
        #     raise NotEnoughInformation
    
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

# ---- NAME FETCHING ----

# TO GET DATABASE NAME
@data_router.get("/db_name/{user_id}", response_model=dict[str, str])
async def get_userselected_db_names(db_session:AsyncSession=Depends(get_session), user_id:int=Path(..., description="user_id to fetch userchosen database names")):
    """This router fetches userchosen database names"""
    try:
        result=await get_database_names(session=db_session, p_user_id=user_id)
        return {r["chat_id"]:r["database_name"] for r in result}
    except Exception as e:
        logger.exception("Error in get_userselected_db_names %s",e)
        raise HTTPException(status_code=500, detail="Error in calling function to fetch userselected database names from chathistory database")

# TO GET CHAT NAMES
@data_router.get("/chatnames/{user_id}")
async def fetch_chatnames(user_id:int=Path(..., description="userid to fetch chatnames"), db_session:AsyncSession=Depends(get_session)):
    """This router handler is to fetch chatnames for a given user"""
    try:
        result=await get_chat_names(session=db_session, user_id=user_id)
        return {s['chat_id']: s['chat_name'] for s in result}
    except Exception as e:
        logger.exception("Error in fetch_chat_names route handler %s",e)
        raise HTTPException(status_code=500, detail="Error in calling function to fetch chatnames from chathistory")
    
# ---- CHAT HISTORY ----

# TO GET CHAT HISTORY
@data_router.post("/chat_history", response_model=list[dict])
async def get_chathistory(request:ChatHistoryInputValidation, db_session:AsyncSession=Depends(get_session)):
    """This router fetches the chathistory"""
    try:
        result=await get_chat(session=db_session, user_id=request.user_id, chat_id=request.chat_id)
        return result
    except Exception as e:
        logger.exception("Error in get_chathistory route handler %s", e)
        raise HTTPException(status_code=500, detail="Error in calling function to fetch chat history")

# TO INSERT CONVERSATION
@data_router.post("/insert_conversation")
async def insert_chat(request:ChatInsertInputValidation, db_session:AsyncSession=Depends(get_session)):
    "Router to save a new chat message. Validates the role as either 'human' or 'ai'."
    try:
        result=await save_chathistory(session=db_session, chat_name=request.chat_name, user_id=request.user_id, chat_id=request.chat_id, db_name=request.database, role=request.role, message=request.message, sql_query=request.sql_query)
        return JSONResponse(status_code=200, content="Successfully_Inserted")
    except Exception as e:
        logger.exception("Error in insert_chat route handler %s", e)
        raise HTTPException(status_code=500, detail="Error in calling function to insert conversation into chathistory")     

# TO DELETE CHAT HISTORY
@data_router.delete("/delete_chathistory")
async def delete_chathistory(request:ChatHistoryInputValidation, db_session:AsyncSession=Depends(get_session)):
    """This route handler delete chat_history"""
    try:
        result=await delete_chat(session=db_session, user_id=request.user_id, chat_id=request.chat_id)
        await delete_useruploads_metadata(session=db_session, user_id=request.user_id, chat_id=request.chat_id)
        return JSONResponse(status_code=200, content="Successfully deleted chathistory")
    except Exception as e:
        logger.exception("Error in delete_chathistory route handler")
        raise HTTPException(status_code=500, detail="Error in calling function to delete chat history")
    
# FILE UPLOAD FEATURE
@data_router.post("/upload_file")
async def file_uploader(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    chat_id: str = Form(...),
    database: str = Form("useruploads"),
    table_name: str = Form(...),
    file_type: str = Form(...),
    db_session: AsyncSession = Depends(get_session),
):
    """This route handler creates database table from the given excel or csv file"""
    try:
        normalized_file_type = file_type.lower().strip(".")
        if normalized_file_type not in {"csv", "xlsx"}:
            raise HTTPException(status_code=400, detail="Only csv and xlsx files are supported")

        file_bytes = await file.read()
        normalized_table_name = normalize_table_name(table_name)
        cleaned_df_result = await asyncio.to_thread(
            datacleaning, 
            file_bytes=file_bytes, 
            file_type=normalized_file_type
        )
        
        if not cleaned_df_result:
            raise HTTPException(status_code=400, detail="Data cleaning failed")

        _df = cleaned_df_result["dataframe"]
        success= await save_to_useruploadsdb(df=_df, table_name=normalized_table_name)

        if not success:
            raise Exception("Database insertion returned False")

        metadata_saved = await save_useruploads_metadata(
            session=db_session,
            user_id=user_id,
            database_name=database,
            chat_id=chat_id,
            table_name=normalized_table_name,
        )

        if not metadata_saved:
            raise Exception("Upload metadata insertion returned False")
        
        return {
            "success": True,
            "file_name": file.filename,
            "table_name": normalized_table_name,
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception("Error Message: Errow while creating database table from the uploaded file")
        raise HTTPException(status_code=500, detail="Error while creating database table from the file")
    
    
