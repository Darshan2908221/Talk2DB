from sqlalchemy import Integer, String, Text, DateTime, func, create_engine, URL
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy_utils import create_database, database_exists
from backend.src.core.config import configured_attributes
from backend.src.utils.app_logger import logger

def _mysql_url(database: str | None = None) -> URL:
    settings = configured_attributes()
    driver = settings.DB_DRIVER
    if driver == "aiomysql":
        driver = "pymysql"

    return URL.create(
        drivername=f"{settings.DB_DIALECT}+{driver}",
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        username=settings.DB_USERNAME,
        password=settings.DB_PASSWORD.get_secret_value(),
        database=database,
    )


def _create_database_if_missing(database: str) -> URL:
    db_url = _mysql_url(database)
    if not database_exists(db_url):
        create_database(db_url)
        print(f"----{database.upper()} DATABASE CREATED SUCCESSFULLY----")
    return db_url


# CHATHISTORY Database 
# BASE CLASS INHERITANCE
class Base1(DeclarativeBase):
    pass

class ChatHistoryTable(Base1):
    __tablename__="user_chat_history"
    id:Mapped[int]=mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:Mapped[int]=mapped_column(Integer, nullable=False)
    chat_id:Mapped[str]=mapped_column(String(50), nullable=False)
    chat_name:Mapped[str]=mapped_column(String(50), nullable=False)
    database_name:Mapped[str]=mapped_column(String(50), nullable=True)
    role:Mapped[str]=mapped_column(String(50), nullable=False)
    message:Mapped[str]=mapped_column(Text, nullable=False)
    sql_query:Mapped[str]=mapped_column(Text, nullable=True)
    created_at:Mapped[DateTime]=mapped_column(DateTime, server_default=func.now())

# DATABASE CREATION UTILITY FUNCTION
def chathistory_db_creation():
    """This function creates the chat history database and a user_chat_history table"""
    db_url = _create_database_if_missing("chathistory")
    engine=create_engine(url=db_url)

    Base1.metadata.create_all(engine)
    print("----TABLE CREATED SUCCESSFULLY----")

"""
Session creation
session_provider=sessionmaker(bind=engine)

Chat history temporary and Data_creation
chathistory_temp=[]

#Data retrieval using and converting to langchain message objects
with session_provider() as session:
    data=session.execute(select(Chattable).order_by(Chattable.created_at.asc()).limit(100)).scalars().all()
    for row in data:
        if row.role=="user":
            chathistory_temp.append(HumanMessage(content=row.message))
        else:
            chathistory_temp.append(AIMessage(content=row.message)) 
"""

# USERUPLOADSREGISTRY Database

# BASE CLASS INHERITANCE
class Base2(DeclarativeBase):
    pass

class UserUploadsRegistryTable(Base2):
    """This class creates the tables for user_uploads"""
    logger.info("Initiating table creation")

    __tablename__="files_metadata"
    id:Mapped[int]=mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:Mapped[int]=mapped_column(Integer, nullable=False)
    database_name:Mapped[str]=mapped_column(String(50), nullable=True)
    chat_id:Mapped[str]=mapped_column(String(50), nullable=False)
    table_name:Mapped[str]=mapped_column(String(50), nullable=False)  #fle_name==table_name
    created_at:Mapped[DateTime]=mapped_column(DateTime, server_default=func.now())

# DATABASE CREATION UTILITY FUNCTION
def useruploadsregistry_db_creation():
    """This function creates the useruploadsregistry database and files_metadata table"""
    db_url = _create_database_if_missing("useruploadsregistry")
    engine=create_engine(url=db_url)
    Base2.metadata.create_all(bind=engine)
    print("FILES_METADATA TABLE IN USERUPLOADS DATABASE CREATED SUCCESSFULLY")

# USERUPLOADS Database

# DATABASE CREATION UTILITY FUNCTION
def user_uploads_creation():
    """This function creates the user_uploads database"""
    _create_database_if_missing("useruploads")

if __name__=="__main__":
    def main():
        print("----INITIATING DATABASE CREATION----")
        chathistory_db_creation()
        print("----CHATHISTORY DATABASE AND TABLE CREATED SUCCESSFLLY")
        useruploadsregistry_db_creation()
        print("----USERUPLOADSREGISTRY DATABASE AND TABLE CREATED SUCCESSFULLY")
        user_uploads_creation()
        print("----ALL DONE----")

    main()
        

#python -m backend.src.db_connect.db_creation