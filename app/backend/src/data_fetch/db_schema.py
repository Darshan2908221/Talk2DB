#This module fetch databases, build table schema, and builds database schema
from backend.src.core.config import configured_attributes
from backend.src.utils.app_logger import logger
from backend.src.db_connect.connection import engine
from sqlalchemy import inspect
from typing import List
import asyncio

_databases_cache:List[str] | None=None
_databases_lock=asyncio.Lock()

class DBSchema(Exception):
    pass

class DBNotFoundError(DBSchema):
    pass

class TableNotFoundError(DBSchema):
    pass

#get databases
async def get_databases()->List[str]:
    """This function get databases from the database"""
    global _databases_cache
    async with _databases_lock:
        if _databases_cache is None:
            async with engine.connect() as conn:
                def fetch_db_schema(connection):
                    inspector=inspect(connection)
                    logger.info("Fetching databases from the database")
                    return inspector.get_schema_names()
                schemas=await conn.run_sync(fetch_db_schema)
                system_dbs = {'information_schema', 'performance_schema', 'mysql', 'sys'}
                _databases_cache=[db for db in schemas if db not in system_dbs ]
                try:
                    if not _databases_cache:
                        _databases_cache=None
                        raise DBNotFoundError
                except DBNotFoundError:
                    logger.warning("No Database exists, Recheck!!")
                    raise DBNotFoundError("No Database exists, Recheck!!")
    logger.info("Databases fetched successfully")
    return _databases_cache

_table_schema:dict={}
_table_schema_lock=asyncio.Lock()

'''
{db_name:{table_name:{columns:{column_name : column_type}}}}
'''

async def get_table_schema(target_db:str | None=None)->dict:
    """ This function provides the table schema for the provided database"""
    logger.info("Trigering functions to build table schema")
    if target_db is None:
        target_db=configured_attributes().DB_NAME
    async with _table_schema_lock:
        if target_db not in _table_schema:
            await _fetch_table_schema(target_db)
    return {target_db:_table_schema[target_db]}

async def _fetch_table_schema(target_db:str)->dict:
    async with engine.connect() as conn:
        def table_schema_build(connection):
            inspector=inspect(connection)
            tables=inspector.get_table_names(schema=target_db)
            local_schema_build={}
            for table in tables:
                local_schema_build[table]={}
                columns= inspector.get_columns(schema=target_db, table_name=table)
                local_schema_build[table]["columns"]={column["name"]:str(column["type"]) for column in columns}
            _table_schema[target_db]=local_schema_build 
            logger.info("Table Schema built successfully")
            return _table_schema[target_db]
        return await conn.run_sync(table_schema_build)    


'''
{
 "employees": {
    "columns": {
        "emp_id": "INTEGER",
        "dept_id": "INTEGER"
    },
    "primary_key": ["emp_id"],
    "relations": [
        {
     "local_column": "...",
     "referred_table": "...",
     "referred_column": "..."
   }
]
 }
}
'''
    
async def get_db_schema(table_names:list[str], target_db:str | None=None):
    """ This function provides the db schema for the provided database and tables"""
    if target_db is None:
        target_db=configured_attributes().DB_NAME
    async with engine.connect() as conn:
        def tables_validation(fetched_table_names):           
            for table in table_names:
                if table not in fetched_table_names:
                    raise TableNotFoundError(f"Table: '{table}' not found in database: '{target_db}'")

        def db_schema_build(connection):
            logger.info("Triggering functions to build db_schema")
            inspector=inspect(connection)
            fetched_table_names=inspector.get_table_names(schema=target_db)
            # fetched_table_names_set=set(fetched_table_names)
            tables_validation(fetched_table_names)
            db_schema={}
            for table in table_names:
                db_schema[table]={}
                db_schema[table]["columns"]={column["name"]:str(column["type"]) for column in inspector.get_columns(schema=target_db,table_name=table)}
                db_schema[table]["primary_key"]=inspector.get_pk_constraint(schema=target_db, table_name=table)["constrained_columns"]
                db_schema[table]["relations"]=[{"local_columns":fk["constrained_columns"],"referred_table":fk["referred_table"], "referred_columns":fk["referred_columns"]} for fk in inspector.get_foreign_keys(schema=target_db, table_name=table)]
            logger.info("db_schema built successfully")  
            # print(db_schema)
            return {target_db:db_schema}             
        return await conn.run_sync(db_schema_build)
    

if __name__=="__main__":
    async def main():
        try:
            print("databases:", await get_databases(), sep="\n")
            print("\n")
            print("table_schema:", await get_table_schema(), sep="\n")
            print("\n")
            print("db_schema:",await get_db_schema(table_names=["employees","countries","departments"]))
        except Exception as e:
            print("Error:",e)
        
        finally:
            await engine.dispose()
        
    asyncio.run(main())

"""
2026-02-25 14:50:34,435-logtalk2db-INFO-MainThread-:starting env variales configuration
2026-02-25 14:50:34,443-logtalk2db-INFO-MainThread-configured variables successfully
2026-02-25 14:50:34,636-logtalk2db-INFO-MainThread-Fetching databases from the database
databases:
2026-02-25 14:50:34,646-logtalk2db-INFO-MainThread-Databases fetched successfully
['bumble', 'delay', 'enventure', 'functions', 'hr', 'netflix', 'newschema', 'northwind', 'ola', 'pizzahut', 'practice_dataset', 'sakila', 'school', 'student', 'walmart', 'world']


2026-02-25 14:50:34,650-logtalk2db-INFO-MainThread-Trigering functions to build table schema
2026-02-25 14:50:34,691-logtalk2db-INFO-MainThread-Table Schema built successfully
table_schema:
{'hr': {'countries': {'columns': {'country_id': 'CHAR(2)', 'country_name': 'VARCHAR(40)', 'region_id': 'INTEGER'}}, 'departments': {'columns': {'department_id': 'INTEGER', 'department_name': 'VARCHAR(30)', 'manager_id': 'INTEGER', 'location_id': 'INTEGER'}}, 'employees': {'columns': {'employee_id': 'INTEGER', 'first_name': 'VARCHAR(20)', 'last_name': 'VARCHAR(25)', 'email': 'VARCHAR(25)', 'phone_number': 'VARCHAR(20)', 'hire_date': 'DATE', 'job_id': 'VARCHAR(10)', 'salary': 'DECIMAL(8, 2)', 'commission_pct': 'DECIMAL(2, 2)', 'manager_id': 'INTEGER', 'department_id': 'INTEGER'}}, 'job_history': {'columns': {'employee_id': 'INTEGER', 'start_date': 'DATE', 'end_date': 'DATE', 'job_id': 'VARCHAR(10)', 'department_id': 'INTEGER'}}, 'jobs': {'columns': {'job_id': 'VARCHAR(10)', 'job_title': 'VARCHAR(35)', 'min_salary': 'DECIMAL(8, 0)', 'max_salary': 'DECIMAL(8, 0)'}}, 'locations': {'columns': {'location_id': 'INTEGER', 'street_address': 'VARCHAR(40)', 'postal_code': 'VARCHAR(12)', 'city': 'VARCHAR(30)', 'state_province': 'VARCHAR(25)', 'country_id': 'CHAR(2)'}}, 'regions': {'columns': {'region_id': 'INTEGER', 'region_name': 'VARCHAR(25)'}}}}


2026-02-25 14:50:34,694-logtalk2db-INFO-MainThread-Triggering functions to build db_schema
2026-02-25 14:50:34,721-logtalk2db-INFO-MainThread-db_schema built successfully
db_schema: {'hr': {'employees': {'columns': {'employee_id': 'INTEGER', 'first_name': 'VARCHAR(20)', 'last_name': 'VARCHAR(25)', 'email': 'VARCHAR(25)', 'phone_number': 'VARCHAR(20)', 'hire_date': 'DATE', 'job_id': 'VARCHAR(10)', 'salary': 'DECIMAL(8, 2)', 'commission_pct': 'DECIMAL(2, 2)', 'manager_id': 'INTEGER', 'department_id': 'INTEGER'}, 'primary_key': ['employee_id'], 'relations': [{'local_columns': ['job_id'], 'referred_table': 'jobs', 'referred_columns': ['job_id']}, {'local_columns': ['department_id'], 'referred_table': 'departments', 'referred_columns': ['department_id']}, {'local_columns': ['manager_id'], 'referred_table': 'employees', 'referred_columns': ['employee_id']}]}, 'countries': {'columns': {'country_id': 'CHAR(2)', 'country_name': 'VARCHAR(40)', 'region_id': 'INTEGER'}, 'primary_key': ['country_id'], 'relations': [{'local_columns': ['region_id'], 'referred_table': 'regions', 'referred_columns': ['region_id']}]}, 'departments': {'columns': {'department_id': 'INTEGER', 'department_name': 'VARCHAR(30)', 'manager_id': 'INTEGER', 'location_id': 'INTEGER'}, 'primary_key': ['department_id'], 'relations': [{'local_columns': ['location_id'], 'referred_table': 'locations', 'referred_columns': ['location_id']}, {'local_columns': ['manager_id'], 'referred_table': 'employees', 'referred_columns': ['employee_id']}]}}}
"""

# python -m backend.src.data_fetch.db_schema