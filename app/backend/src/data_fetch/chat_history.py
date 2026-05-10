#This module has the code to manage the chat history

from sqlalchemy import create_engine, URL, inspect, Integer, String, Text, DateTime, func, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from backend.src.db_connect.connection import AsyncSessionLocal
# from sqlalchemy_utils import database_exists, create_database
from langchain_core.messages import AIMessage, HumanMessage
from backend.src.utils.app_logger import logger
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
import json
import pandas as pd
import asyncio

#To get database_name for userid and chat_id
async def get_database_names(session:AsyncSession, p_user_id:int):
    """This functions gets the database names for the given userid and"""
    try:
        logger.info("Getting database names for the userid and chatid")
        db_names_fetched=await session.execute(text("select distinct chat_id, database_name from chathistory.user_chat_history where user_id=:u_id"), {"u_id": p_user_id})
        db_names_fetched_formatted= db_names_fetched.mappings().all()
        logger.info("fetched chat_id, database_name successfully from chathistory database for a given user_id")
        db_names_fetched_formatted_dict=[dict(row) for row in db_names_fetched_formatted]
        return db_names_fetched_formatted_dict
    
    except Exception as e:
        logger.exception("Error Message: %s",e)
        raise HTTPException(status_code=500, detail="Error, retrieving database_name for a given user_id")
    
#To get user_id and chat_name
async def get_chat_names(session:AsyncSession, user_id:int):
    """This function fetches the chatnames for the given user_id"""
    try:
        logger.info("Fetching chatnames from chathistory database")
        data=await session.execute(text("select distinct chat_id, chat_name from chathistory.user_chat_history where user_id=:u_id"), {"u_id": user_id})
        data_formatted=data.mappings().all()
        logger.info("Fetched chatnames successfully from chathistory database for a given user_id")
        data_formatted_dict=[dict(row) for row in data_formatted]
        return data_formatted_dict

    except Exception as e:
        logger.exception("Error Message: %s",e)
        raise HTTPException(status_code=500, detail="Chatnames retrieval error")


#To insert into chathistory
async def save_chathistory(session:AsyncSession, user_id:int, chat_id:str, db_name:str, role:str, message:str, chat_name:str, sql_query:str):
    """This function inserts the user conversation in to database"""
    try:
        logger.info("Inserting conversation into chathistory database")
        query = text("""
            INSERT INTO chathistory.user_chat_history (user_id, chat_id, chat_name, role, message, database_name, sql_query) 
            VALUES (:u_id, :c_id, :ch_name, :role, :msg, :db_name, :sql_query)
        """)
        
        await session.execute(
            query, 
            {
                "u_id": user_id, 
                "c_id": chat_id, 
                "ch_name":chat_name,
                "role": role, 
                "msg": message,
                "db_name":db_name,
                "sql_query":sql_query
            }
        )
        await session.commit()
        logger.info("Inserted Conversation into chathistory database successfully")
        return True
    
    except Exception as e:
        await session.rollback()
        logger.exception("Error Message: Error while inserting conversation in to chathistory database %s",e)
        raise HTTPException(status_code=500, detail="Database conversation insertion error")

#To retrieve chat history
async def get_chat(session:AsyncSession, user_id:int, chat_id:str):
    """This function fetches the chathistory from database"""
    logger.info("Fetching chat history")
    # async with AsyncSessionLocal() as session:

    try:
        query=text("select role, message from chathistory.user_chat_history where user_id=:u_id and chat_id=:ch_id order by created_at asc limit 100")
        data_fetched=await session.execute(query, {"u_id":user_id,"ch_id":chat_id})
        data_transformed=data_fetched.mappings().all()
        data_transformed_list=[dict(row) for row in data_transformed]
        logger.info("Chat history fetched and transformed successfully")
        return data_transformed_list
    
    except Exception as e:
        logger.exception("Error Message: %s",e)
        raise HTTPException(status_code=500, detail="Database retrieval error")
        
#To delete chat_history
async def delete_chat(session:AsyncSession, user_id:int, chat_id:str):
    """This function deletes the chathistory for the given user_id and chat_id"""
    try:
        logger.info("Initiating chat history deletion")
        query=text("delete from chathistory.user_chat_history where user_id=:u_id and chat_id=:ch_id")
        await session.execute(
            query,
            {
                "u_id":user_id,
                "ch_id":chat_id
            }
        )
        await session.commit()
        logger.info("Successfullydeleted chat_history")
        return True
    except Exception as e:
        await session.rollback()
        logger.exception("Error Message: Error while deleting chathistory from database %s",e)
        raise HTTPException(status_code=500, detail="Database deletion was not successfull")


if __name__=="__main__":
    result=asyncio.run(get_chat(user_id=5452, chat_id=1))
    print(result)

"""
[{'id': 1, 'user_id': 5452, 'chat_id': 1, 'role': 'user', 'message': 'What is the capital of France?', 'sql_query': None, 'created_at': datetime.datetime(2026, 4, 23, 23, 48, 9)}, {'id': 2, 'user_id': 5452, 'chat_id': 1, 'role': 'assistant', 'message': 'The capital of France is Paris.', 'sql_query': None, 'created_at': datetime.datetime(2026, 4, 23, 23, 48, 9)}, {'id': 11, 'user_id': 5452, 'chat_id': 1, 'role': 'user', 'message': 'What is the capital of France?', 'sql_query': None, 'created_at': datetime.datetime(2026, 4, 24, 0, 20, 22)}, {'id': 12, 'user_id': 5452, 'chat_id': 1, 'role': 'assistant', 'message': 'The capital of France is Paris.', 'sql_query': None, 'created_at': datetime.datetime(2026, 4, 24, 0, 20, 22)}]


#Pandas Dataframe

           created_at  id                          message       role  chat_id sql_query  user_id
0 2026-04-23 23:48:09   1   What is the capital of France?       user           1      None     5452
1 2026-04-23 23:48:09   2  The capital of France is Paris.  assistant           1      None     5452
2 2026-04-24 00:20:22  11   What is the capital of France?       user           1      None     5452
3 2026-04-24 00:20:22  12  The capital of France is Paris.  assistant           1      None     5452
"""

#Latest  (Dict)
"""
2026-04-25 13:14:36,578-logtalk2db-INFO-MainThread-configured variables successfully
2026-04-25 13:14:37,766-logtalk2db-INFO-MainThread-Fetching chat history
2026-04-25 13:14:37,782-logtalk2db-INFO-MainThread-Chat history fetched and transformed successfully
[{'role': 'user', 'message': 'What is the capital of France?'}, {'role': 'assistant', 'message': 'The capital of France is Paris.'}, {'role': 'user', 'message': 'What is the capital of France?'}, {'role': 'assistant', 'message': 'The capital of France is Paris.'}]
"""


#python -m backend.src.data_fetch.chat_history
