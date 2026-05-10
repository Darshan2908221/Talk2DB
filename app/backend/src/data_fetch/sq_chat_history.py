# This module has the code for upating user_uploads_registry database, uploading chats to chat_history database
from backend.src.utils.app_logger import logger
from backend.src.db_connect.sq_db_creation import UserUploadsRegistryTable
from sqlalchemy import text
from sqlalchemy.orm import Session


def supdate_user_uploads_registry(session:Session, user_id:int, database_name:str, chat_id:str, file_name:str):
    """This function updates the file name and other metadata to user_uploads_registry database"""
    try:
        logger.info("Initiating metadata update to user_files table in user_uploads_registry database")
        query=text("""
                   INSERT INTO user_files(user_id, database_name, chat_id, file_name)
                   VALUES(:u_id, :db_name, :c_id, :f_name)""")
        parameters={"u_id":user_id, "db_name":database_name, "c_id":chat_id, "f_name":file_name}

        with session:
            session.execute(statement=query, params=parameters)
            session.commit()
        logger.info("Inserted values to user_files in user_uploads_registry")
        return True

    except Exception as e:
        session.rollback()
        logger.exception("Error while updating metadata to user_files in user uploads registry database %s",e)
        return False
    
def supdate_chat_history(session:Session, user_id:int, chat_id:str, chat_name:str, database_name:str, role:str, message:str, sql_query:str):
    """This functions updates the user chat to chat_history database"""
    try:
        logger.info("Inserting conversation into chathistory database")
        query = text("""
            INSERT INTO user_chathistory (user_id, chat_id, chat_name, database_name, role, message, sql_query) 
            VALUES (:u_id, :c_id, :ch_name, :db_name, :role, :msg, :sql_query)
        """)
        
        with session:
            session.execute(
                query, 
                {
                    "u_id": user_id, 
                    "c_id": chat_id, 
                    "ch_name":chat_name,
                    "db_name":database_name,
                    "role": role, 
                    "msg": message,
                    "sql_query":sql_query
                }
                )
            session.commit()
            logger.info("Inserted Conversation into chathistory database successfully")
            return True
    
    except Exception as e:
        session.rollback()
        logger.exception("Error Message: Error while inserting conversation in to chathistory database %s",e)
        return False

#To get database_name for userid and chat_id
def get_sdatabase_names(session:Session, p_user_id:int):
    """This functions gets the database names for the given userid and"""
    try:
        logger.info("Getting database names for the userid and chatid")
        db_names_fetched=session.execute(text(f"select distinct chat_id, database_name from user_chathistory where user_id={p_user_id}"))
        db_names_fetched_formatted= db_names_fetched.mappings().all()
        logger.info("fetched chat_id, database_name successfully from chathistory database for a given user_id")
        db_names_fetched_formatted_dict=[dict(row) for row in db_names_fetched_formatted]
        return db_names_fetched_formatted_dict
    
    except Exception as e:
        session.rollback()
        logger.exception("Error Message: %s",e)
        return False
    
#To get user_id and chat_name
def get_schat_names(session:Session, user_id:int):
    """This function fetches the chatnames for the given user_id"""
    try:
        logger.info("Fetching chatnames from chathistory database")
        data=session.execute(text(f"select distinct chat_id, chat_name from user_chathistory where user_id={user_id}"))
        data_formatted=data.mappings().all()
        logger.info("Fetched chatnames successfully from chathistory database for a given user_id")
        data_formatted_dict=[dict(row) for row in data_formatted]
        return data_formatted_dict

    except Exception as e:
        session.rollback()
        logger.exception("Error Message: %s",e)
        return False

#To retrieve chat history
def get_schat(session:Session, user_id:int, chat_id:str):
    """This function fetches the chathistory from database"""
    logger.info("Fetching chat history")
  
    try:
        query=text("select role, message from user_chathistory where user_id=:u_id and chat_id=:ch_id order by created_at asc limit 100")
        data_fetched=session.execute(query, {"u_id":user_id,"ch_id":chat_id})
        data_transformed=data_fetched.mappings().all()
        data_transformed_list=[dict(row) for row in data_transformed]
        logger.info("Chat history fetched and transformed successfully")
        return data_transformed_list
    
    except Exception as e:
        session.rollback()
        logger.exception("Error Message: %s",e)
        return False
        
#To delete chat_history
def delete_schat(session:Session, user_id:int, chat_id:str):
    """This function deletes the chathistory for the given user_id and chat_id"""
    try:
        logger.info("Initiating chat history deletion")
        query=text("delete from user_chathistory where user_id=:u_id and chat_id=:ch_id")
        session.execute(
            query,
            {
                "u_id":user_id,
                "ch_id":chat_id
            }
        )
        session.commit()
        logger.info("Successfully deleted chat_history")
        return True
    
    except Exception as e:
        session.rollback()
        logger.exception("Error Message: Error while deleting chathistory from database %s",e)
        return False
    

    
