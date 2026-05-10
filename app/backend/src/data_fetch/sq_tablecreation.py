from app.backend.src.db_connect.sq_db_creation import get_useruploads_db
from backend.src.utils.app_logger import logger
import pandas as pd
from io import BytesIO
import re
import asyncio
    
# Table creation
def sdata_preparation(a_file_bytes, a_file_type):
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

def sdatacleaning(file_bytes, file_type):
    """This function assigns the datatype of sample dataframe to main dataframe"""
    prepared_data=sdata_preparation(a_file_bytes=file_bytes, a_file_type=file_type)
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

async def ssave_to_db(df, table_name):
    """Saves the cleaned dataframe to SQLite"""
    try:
        logger.info(f"Initiating {table_name} table creation from excel or csv file into user_uploads database")
        engine=get_useruploads_db()
        loop=asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: df.to_sql(table_name, con=engine, if_exists='replace', index=False)
        )
        logger.info(f"Table {table_name} created successfully i-n user_uploads_database")
        return True
    except Exception as e:
        logger.exception(f"Error while creating table {table_name} into user_uploads database")
        return False
