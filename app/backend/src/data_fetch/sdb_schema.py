#This module fetch databases, build table schema, and builds database schema
from backend.src.core.config import configured_attributes
from backend.src.utils.app_logger import logger
from backend.src.db_connect.sq_db_creation import sget_useruploads_db
from sqlalchemy import inspect
from typing import List

_databases_cache:List[str] | None=None
# _databases_lock=asyncio.Lock()

_databases_cache: List[str] | None = None

class DBSchema(Exception):
    pass

class DBNotFoundError(DBSchema):
    pass

# get databases    
def get_db_schema(table_names: list[str], target_db: str | None = None):
    """ This function provides the db_schema for the provided database and tables """
    engine = sget_useruploads_db()
    
    if target_db is None:
        # Assuming configured_attributes is a callable returning an object with SDB_NAME
        target_db = configured_attributes().SDB_NAME
        
    with engine.connect() as conn:    
        logger.info(f"Triggering functions to build db_schema for target_db: {target_db}")
        inspector = inspect(conn)
        
        # In SQLite, the internal schema name is usually None. 
        # Using the target_db name here can cause 'table not found' errors in SQLite.
        sqlite_internal_schema = None 
        
        # Fetch actual table names present in the DB to validate the requested list
        fetched_table_names = inspector.get_table_names(schema=sqlite_internal_schema)
        
        db_schema = {}
        for table in table_names:
            if table not in fetched_table_names:
                logger.warning(f"Table {table} not found in {target_db}. Skipping.")
                continue
                
            db_schema[table] = {}
            
            # Fetch Columns
            db_schema[table]["columns"] = {
                column["name"]: str(column["type"]) 
                for column in inspector.get_columns(schema=sqlite_internal_schema, table_name=table)
            }
            
            # Fetch Primary Key
            pk_data = inspector.get_pk_constraint(schema=sqlite_internal_schema, table_name=table)
            db_schema[table]["primary_key"] = pk_data.get("constrained_columns", [])
            
            # Fetch Relations (Foreign Keys)
            db_schema[table]["relations"] = [
                {
                    "local_columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"], 
                    "referred_columns": fk["referred_columns"]
                } 
                for fk in inspector.get_foreign_keys(schema=sqlite_internal_schema, table_name=table)
            ]
            
        logger.info("db_schema built successfully")
        return {target_db: db_schema}