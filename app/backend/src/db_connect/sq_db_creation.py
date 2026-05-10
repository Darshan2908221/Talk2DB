#Creating sqlite database

from sqlalchemy import create_engine, Integer, String, DateTime, func, Text
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, DeclarativeBase
from backend.src.utils.app_logger import logger
from functools import lru_cache

# User Uploads databasecreation
class Base(DeclarativeBase):
    pass

class Base1(DeclarativeBase):
    pass

class sDatabases():
    """This class creates the sqlite Databases"""
    user_uploads="user_uploads.db"
    user_uploads_registry="user_uploads_registry.db"
    chat_history="chat_history.db"

    #Database creation
    @classmethod
    def _user_uploads_db(cls):
        logger.info("Trigering function to create user_uploads database")
        db_url=f"sqlite:///D:/ENGINEER/AIENGINEER/PROJECTS/Talk2DB/app/backend/src/sq_databases/{cls.user_uploads}"
        engine=create_engine(url=db_url, connect_args={"check_same_thread": False},
                          pool_size=5, max_overflow=10, pool_timeout=30,
                          pool_recycle=3600, pool_pre_ping=True, echo=True)
        logger.info("user_uploads database created successfully")
        return engine
    
    @classmethod
    def _user_uploads_registry_db(cls):
        logger.info("Trigering function to create user_uploads_registry database")
        db_url=f"sqlite:///D:/ENGINEER/AIENGINEER/PROJECTS/Talk2DB/app/backend/src/sq_databases/{cls.user_uploads_registry}"
        engine=create_engine(url=db_url, connect_args={"check_same_thread": False},
                          pool_size=5, max_overflow=10, pool_timeout=30,
                          pool_recycle=3600, pool_pre_ping=True, echo=True)
        logger.info("user_uploads_registry database created successfully")
        return engine
    
    @classmethod
    def _chat_history_db(cls):
        logger.info("Trigering function to create chat_history database")
        db_url=f"sqlite:///D:/ENGINEER/AIENGINEER/PROJECTS/Talk2DB/app/backend/src/sq_databases/{cls.chat_history}"
        engine=create_engine(url=db_url, connect_args={"check_same_thread": False},
                          pool_size=5, max_overflow=10, pool_timeout=30,
                          pool_recycle=3600, pool_pre_ping=True, echo=True)
        logger.info("chat_history database created successfully")
        return engine
    
class sUserUploadsRegistryTable(Base):
    """This class creates the tables for user_uploads"""
    logger.info("Initiating table creation")

    __tablename__="user_files"
    id:Mapped[int]=mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:Mapped[int]=mapped_column(Integer, nullable=False)
    database_name:Mapped[str]=mapped_column(String, nullable=True)
    chat_id:Mapped[str]=mapped_column(String(50), nullable=False)
    file_name:Mapped[str]=mapped_column(String(50), nullable=False)
    created_at:Mapped[DateTime]=mapped_column(DateTime, server_default=func.now())
   

class sChatHistoryTable(Base1):
    __tablename__="user_chathistory"
    id:Mapped[int]=mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:Mapped[int]=mapped_column(Integer, nullable=False)
    chat_id:Mapped[str]=mapped_column(String(50), nullable=False)
    chat_name:Mapped[str]=mapped_column(String(50), nullable=False)
    database_name:Mapped[str]=mapped_column(String, nullable=False)
    role:Mapped[str]=mapped_column(String(50), nullable=False)
    message:Mapped[str]=mapped_column(Text, nullable=False)
    sql_query:Mapped[str]=mapped_column(Text, nullable=True)
    created_at:Mapped[DateTime]=mapped_column(DateTime, server_default=func.now())


# Creating a clean initialization function
def init_db():
    db_tools = sDatabases()
    
    logger.info("Initializing Registry Database")
    registry_engine = db_tools._user_uploads_registry_db()
    Base.metadata.create_all(registry_engine)

    logger.info("Initializing Chat History Database")
    history_engine = db_tools._chat_history_db()
    Base1.metadata.create_all(history_engine)

    logger.info("All databases created successfully")

#User uploads database
@lru_cache(maxsize=2)
def sget_useruploads_db():
    engine=sDatabases()._user_uploads_db()
    return engine

#User upload registry database
@lru_cache(maxsize=2)
def sget_user_uploads_registry_db():
    engine=sDatabases()._user_uploads_registry_db()
    return engine 

#Chat history database
@lru_cache(maxsize=2)
def sget_chat_history_db():
    engine=sDatabases()._chat_history_db()
    return engine

# Session Generators 

def sget_user_uploads_registry_db_session():
    engine = sget_user_uploads_registry_db() 
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        logger.info("Providing session to user_uploads_registry")
        yield session
    except Exception as e:
        logger.exception("Session error in registry database: %s", e)
        session.rollback() 
        raise
    finally:
        session.close() 
        logger.info("Registry session closed")

def sget_chat_history_db_session():
    engine = sget_chat_history_db() 
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        logger.info("Providing session to chat_history database")
        yield session
    except Exception as e:
        logger.exception("Session error in chat history database: %s", e)
        session.rollback()
        raise
    finally:
        session.close()
        logger.info("Chat history session closed")
    
def sget_useruploads_db_session():
    engine = sget_useruploads_db() 
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        logger.info("Providing session to useruploads database")
        yield session
    except Exception as e:
        logger.exception("Session error in useruploads database: %s", e)
        session.rollback()
        raise
    finally:
        session.close()
        logger.info("Useruploads session closed")

if __name__=="__main__":
    init_db()
    

#python -m backend.src.db_connect.sq_db_creation  

