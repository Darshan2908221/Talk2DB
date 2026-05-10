from backend.src.db_connect.db_creation import _mysql_url
from backend.src.utils.app_logger import logger
from backend.src.db_connect.connection import engine
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
from io import BytesIO
import re
import asyncio
    
# Table creation
def data_preparation(a_file_bytes, a_file_type):
    """This function preapres the data for data preparation i.e creates two dataframes one is sample and another is cleaned original file"""
    try:
        logger.info("Initiating sample df creation")
        #file type checking
        if "csv" in a_file_type:
            df=pd.read_csv(BytesIO(a_file_bytes))
        else:
            df=pd.read_excel(BytesIO(a_file_bytes))
        
        #column headername cleaning
        df.columns = df.columns = [re.sub(r'[^a-zA-Z0-9]+', '_', str(col)).strip('_').lower() for col in df.columns]

        # Scan Data (Top 20%, Mid 20%, Last 20%)
        total_rows=len(df)

        if total_rows>=5:
            #first 20% of rows
            segment= int(total_rows*0.2)

            # Identify segments
            first_part= df.head(segment)
            middle_start=(total_rows//2)-(segment//2)
            middle_part=df.iloc[middle_start:(middle_start+segment)]
            last_part=df.tail(segment)

            #concatinating slices of data 
            sample_df=pd.concat([first_part, middle_part, last_part])

        else:
            sample_df=df

        logger.info("Sample df created successfully")   
        return {"dataframe":df, "sample_df":sample_df}
    
    except Exception as e:
        logger.exception("Error while creating sample df %s",e)
        return False

def datacleaning(file_bytes, file_type):
    """This function assigns the datatype of sample dataframe to main dataframe"""
    prepared_data=data_preparation(a_file_bytes=file_bytes, a_file_type=file_type)
    if not prepared_data:
        return False
    df=prepared_data["dataframe"]
    sample_df=prepared_data["sample_df"]
    logger.info("Initiating assignment of sample dataframe datatype to original dataframe")
    for col in df.columns:
        try:
            target_dtype=sample_df[col].dtype
            df[col]=df[col].astype(target_dtype)

        except Exception as e:
            if pd.api.types.is_numeric_dtype(target_dtype):
                df[col]=pd.to_numeric(df[col], errors="coerce")
            
            elif "date" in col.lower() or "time" in col.lower():
                df[col]=pd.to_datetime(df[col], errors="coerce")
            
            else:
                df[col]=df[col].astype(str).str.strip()

    logger.info("Original dataframe is assigned the datatype from the sample dataframe")
    return {"dataframe":df}


def normalize_table_name(table_name):
    """Convert user/file supplied names into safe MySQL table names."""
    normalized_name = re.sub(r'[^a-zA-Z0-9]+', '_', str(table_name)).strip('_').lower()
    if not normalized_name:
        normalized_name = "uploaded_file"
    if normalized_name[0].isdigit():
        normalized_name = f"file_{normalized_name}"
    return normalized_name[:50]


async def save_to_useruploadsdb(df, table_name):
    """Saves the cleaned dataframe to user"""
    try:
        logger.info(f"Initiating {table_name} table creation from excel or csv file into user_uploads database")
        url=_mysql_url(database="useruploads")
        engine=create_engine(url=url)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: df.to_sql(table_name, con=engine, if_exists='replace', index=False)
        )
        logger.info(f"Table {table_name} created successfully i-n user_uploads_database")
        return True
    except Exception as e:
        logger.exception(f"Error while creating table {table_name} into user_uploads database")
        return False


async def save_useruploads_metadata(
    session: AsyncSession,
    user_id: int,
    database_name: str,
    chat_id: str,
    table_name: str,
):
    """Registers an uploaded table for a user's chat."""
    try:
        logger.info("Registering uploaded file metadata")
        query = text("""
            INSERT INTO useruploadsregistry.files_metadata
                (user_id, database_name, chat_id, table_name)
            VALUES
                (:user_id, :database_name, :chat_id, :table_name)
        """)
        await session.execute(
            query,
            {
                "user_id": user_id,
                "database_name": database_name,
                "chat_id": chat_id,
                "table_name": table_name,
            },
        )
        await session.commit()
        logger.info("Uploaded file metadata registered successfully")
        return True
    except Exception as e:
        await session.rollback()
        logger.exception("Error while registering uploaded file metadata %s", e)
        return False


async def delete_useruploads_metadata(session: AsyncSession, user_id: int, chat_id: str):
    """Removes uploaded table registrations for a deleted chat."""
    try:
        logger.info("Deleting uploaded file metadata for chat")
        query = text("""
            DELETE FROM useruploadsregistry.files_metadata
            WHERE user_id=:user_id AND chat_id=:chat_id
        """)
        await session.execute(query, {"user_id": user_id, "chat_id": chat_id})
        await session.commit()
        logger.info("Uploaded file metadata deleted successfully")
        return True
    except Exception as e:
        await session.rollback()
        logger.exception("Error while deleting uploaded file metadata %s", e)
        return False

