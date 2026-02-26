#This module has the prompts to feed LLM
from langchain_core.prompts import ChatPromptTemplate
from backend.src.core.config import configured_attributes
from backend.src.data_fetch.db_schema import get_table_schema, get_db_schema
from backend.src.utils.app_logger import logger
from pydantic import BaseModel, Field
from typing import Annotated
import asyncio

#Pydantic model for the schema filtration response
class SchemaFiltrationModel(BaseModel):
    table_names:Annotated[list[str], Field(..., description="Shall include the tables required to write mysql query to get the data from database to answer user query", examples=["employees","countries"])]


#prompt to filter schema and get tables
table_prompt_template=ChatPromptTemplate([
    ("system", 
     """
     you are a database schema analyzer.
     Task: Select ONLY the tables required to answer the user query.
     Rules:
     - Preserve user intent.
     - Use ONLY tables present in schema.
     - Do NOT invent tables.
     - Do NOT explain reasoning.
     """),
    ("human",
    """
    USER_QUERY:{user_query}
    TARGET_DB:{target_db}
    DB_SCHEMA:{table_schema}
    """)])

def get_table_prompt(user_query:str, table_schema:dict, target_db:str | None=None):
    """This function provides the prompt for the schema filtration"""
    if target_db is None:
        target_db=configured_attributes().DB_NAME
    logger.info("Invoking table prompt")
    table_prompt_value=table_prompt_template.invoke(input=
                                                    {
                                                        "user_query":user_query,
                                                        "target_db":target_db,
                                                        "table_schema":table_schema
                                                        })
    logger.info("Table Prompt ready, its now a prompt value")
    return table_prompt_value

#pydantic model to get query
class QueryModel(BaseModel):
    query:Annotated[str, Field(..., description="A single valid executable MySQL SELECT query only. No explanation or text")]

# prompt to generate query from llm
query_prompt_template = ChatPromptTemplate([
    ("system",
     """
     You are an expert MySQL developer.
     Task:
     Generate a valid MySQL query that answers the user question.
     Rules:
     - Use ONLY tables and columns present in DB_SCHEMA.
     - Follow MySQL syntax strictly.
     - Always prefix tables with database name (database.table).
     - NAME FILTERS: Always use the `LIKE` operator with wildcards for name or other search term when required. 
       Example: select * from hr.employees where last_name like "%Haan%";
     - Use explicit JOIN conditions based on relations.
     - Do NOT invent tables or columns if required information not present then return SELECT 1.
     - Generate ONLY a SELECT query.
     - Decide using SELECT * based on users query otherwise only use necessary columns.
     Example:
     user_query: list employees data whose salary>20000
     mysql_query: SELECT * FROM DATABASENAME.TABLENAME WHERE SALARY>20000
     """),
     ("human",
      """
      USER_QUERY:{user_query}
      DATABASE:{target_db}
      DB_SCHEMA:{db_schema}""")])

def get_query_prompt(user_query:str, db_schema:dict, target_db:str | None=None):
    """This function provides prompt to get the mysql query"""
    if target_db is None:
        target_db=configured_attributes().DB_NAME
    logger.info("Invoking query prompt")
    query_prompt_value=query_prompt_template.invoke(input=
                                                    {
                                                        "user_query":user_query,
                                                        "target_db":target_db,
                                                        "db_schema":db_schema
                                                        })
    logger.info("Query prompt ready, It's now a prompt value")
    return query_prompt_value

if __name__=="__main__":
    try:
        async def main():
            table_schema = await get_table_schema()
            print("\n")
            print("Table Prompt:",get_table_prompt(user_query="list employees and their salery",table_schema=table_schema), sep="\n")
            print("\n")
            db_schema= await get_db_schema(table_names=["employees", "countries"])
            print("\n")
            print("Query Promt:",get_query_prompt(user_query="list employees and their salery",db_schema=db_schema),sep="\n")
    except Exception as e:
        print("ERROR MESSAGE:",e)
    
    asyncio.run(main())

"""
2026-02-25 15:36:08,105-logtalk2db-INFO-MainThread-:starting env variales configuration
2026-02-25 15:36:08,109-logtalk2db-INFO-MainThread-configured variables successfully
2026-02-25 15:36:08,317-logtalk2db-INFO-MainThread-Trigering functions to build table schema
2026-02-25 15:36:08,375-logtalk2db-INFO-MainThread-Table Schema built successfully


2026-02-25 15:36:08,375-logtalk2db-INFO-MainThread-Invoking table prompt
Table Prompt:
2026-02-25 15:36:08,410-logtalk2db-INFO-MainThread-Table Prompt ready, its now a prompt value
messages=[SystemMessage(content='\n     you are a database schema analyzer.\n     Task: Select ONLY the tables required to answer the user query.\n     Rules:\n     - Preserve user intent.\n     - Use ONLY tables present in schema.\n     - Do NOT invent tables.\n     - Do NOT explain reasoning.\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n    USER_QUERY:list employees and their salery\n    TARGET_DB:hr\n    DB_SCHEMA:{'hr': {'countries': {'columns': {'country_id': 'CHAR(2)', 'country_name': 'VARCHAR(40)', 'region_id': 'INTEGER'}}, 'departments': {'columns': {'department_id': 'INTEGER', 'department_name': 'VARCHAR(30)', 'manager_id': 'INTEGER', 'location_id': 'INTEGER'}}, 'employees': {'columns': {'employee_id': 'INTEGER', 'first_name': 'VARCHAR(20)', 'last_name': 'VARCHAR(25)', 'email': 'VARCHAR(25)', 'phone_number': 'VARCHAR(20)', 'hire_date': 'DATE', 'job_id': 'VARCHAR(10)', 'salary': 'DECIMAL(8, 2)', 'commission_pct': 'DECIMAL(2, 2)', 'manager_id': 'INTEGER', 'department_id': 'INTEGER'}}, 'job_history': {'columns': {'employee_id': 'INTEGER', 'start_date': 'DATE', 'end_date': 'DATE', 'job_id': 'VARCHAR(10)', 'department_id': 'INTEGER'}}, 'jobs': {'columns': {'job_id': 'VARCHAR(10)', 'job_title': 'VARCHAR(35)', 'min_salary': 'DECIMAL(8, 0)', 'max_salary': 'DECIMAL(8, 0)'}}, 'locations': {'columns': {'location_id': 'INTEGER', 'street_address': 'VARCHAR(40)', 'postal_code': 'VARCHAR(12)', 'city': 'VARCHAR(30)', 'state_province': 'VARCHAR(25)', 'country_id': 'CHAR(2)'}}, 'regions': {'columns': {'region_id': 'INTEGER', 'region_name': 'VARCHAR(25)'}}}}\n    ", additional_kwargs={}, response_metadata={})]


2026-02-25 15:36:08,410-logtalk2db-INFO-MainThread-Triggering functions to build db_schema
2026-02-25 15:36:08,448-logtalk2db-INFO-MainThread-db_schema built successfully


Query Promt:
messages=[SystemMessage(content='\n     You are an expert MySQL developer.\n     Task:\n     Generate a valid MySQL query that answers the user question.\n     Rules:\n     - Use ONLY tables and columns present in DB_SCHEMA.\n     - Follow MySQL syntax strictly.\n     - Always prefix tables with database name (database.table).\n     - NAME FILTERS: Always use the `LIKE` operator with wildcards for name or other search term when required. \n       Example: select * from hr.employees where last_name like "%Haan%";\n     - Use explicit JOIN conditions based on relations.\n     - Do NOT invent tables or columns if required information not present then return SELECT 1.\n     - Generate ONLY a SELECT query.\n     - Decide using SELECT * based on users query otherwise only use necessary columns.\n     Example:\n     user_query: list employees data whose salary>20000\n     mysql_query: SELECT * FROM DATABASENAME.TABLENAME WHERE SALARY>20000\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n      USER_QUERY:list employees and their salery\n      DATABASE:hr\n      DB_SCHEMA:{'hr': {'employees': {'columns': {'employee_id': 'INTEGER', 'first_name': 'VARCHAR(20)', 'last_name': 'VARCHAR(25)', 'email': 'VARCHAR(25)', 'phone_number': 'VARCHAR(20)', 'hire_date': 'DATE', 'job_id': 'VARCHAR(10)', 'salary': 'DECIMAL(8, 2)', 'commission_pct': 'DECIMAL(2, 2)', 'manager_id': 'INTEGER', 'department_id': 'INTEGER'}, 'primary_key': ['employee_id'], 'relations': [{'local_columns': ['job_id'], 'referred_table': 'jobs', 'referred_columns': ['job_id']}, {'local_columns': ['department_id'], 'referred_table': 'departments', 'referred_columns': ['department_id']}, {'local_columns': ['manager_id'], 'referred_table': 'employees', 'referred_columns': ['employee_id']}]}, 'countries': {'columns': {'country_id': 'CHAR(2)', 'country_name': 'VARCHAR(40)', 'region_id': 'INTEGER'}, 'primary_key': ['country_id'], 'relations': [{'local_columns': ['region_id'], 'referred_table': 'regions', 'referred_columns': ['region_id']}]}}}", additional_kwargs={}, response_metadata={})]
2026-02-25 15:36:08,453-logtalk2db-INFO-MainThread-Invoking query prompt
2026-02-25 15:36:08,454-logtalk2db-INFO-MainThread-Query prompt ready, It's now a prompt value
"""

#  python -m backend.src.data_fetch.prompts