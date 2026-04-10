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
    # user_query:Annotated[str, Field(..., description="User Modified query")]


#prompt to filter schema and get tables
table_prompt_template=ChatPromptTemplate([
    ("system", 
     """
     you are a database schema analyzer.
     Task: Select ONLY the tables required to answer the user query.
     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS
     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required
     to calculate the above fields, If you found any of those columns in any table then include that table name as well along with
     other table names that are required to answer the user query.
     Below are the columns name:
     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps, sClientName]>>
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
     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS
     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required
     to calculate the above fields therefore in a MYSQL query along with other columns required to answer user query
     include the following columns as well.
     Below are the columns name:
     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps, sClientName]>>
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
            # table_schema = await get_table_schema(target_db="enventure")
            # print("\n")
            # print("Table Prompt normal:",get_table_prompt(user_query="list employees working from hubli business unit",table_schema=table_schema, target_db="enventure"), sep="\n")
            # print("\n")
            # table_schema = await get_table_schema(target_db="enventure")
            # print("\n")
            # print("Table Prompt with utilisation:",get_table_prompt(user_query="list employees working from hubli business unit and their utilisation",table_schema=table_schema, target_db="enventure"), sep="\n")
            # print("\n")
            
            db_schema= await get_db_schema(target_db="enventure", table_names=['employeedetails'])
            print("\n")
            print("Query Promt normal:",get_query_prompt(user_query="list employees working from hubli business unit",db_schema=db_schema),sep="\n")
            print("\n")
            db_schema= await get_db_schema(target_db="enventure", table_names=['employeedetails', 'pulsedb'])
            print("\n")
            print("Query Promt with utilization:",get_query_prompt(target_db="enventure",user_query="list employees working from hubli business unit and their utilisation",db_schema=db_schema),sep="\n")
    except Exception as e:
        print("ERROR MESSAGE:",e)
    
    asyncio.run(main())

"""
2026-04-04 14:36:58,767-logtalk2db-INFO-MainThread-:starting env variales configuration
2026-04-04 14:36:58,767-logtalk2db-INFO-MainThread-configured variables successfully                                                                  
2026-04-04 14:36:58,913-logtalk2db-INFO-MainThread-Trigering functions to build table schema
2026-04-04 14:36:58,945-logtalk2db-INFO-MainThread-Table Schema built successfully


2026-04-04 14:36:58,946-logtalk2db-INFO-MainThread-Invoking table prompt
Table Prompt normal:
messages=[SystemMessage(content='\n     you are a database schema analyzer.\n     Task: Select ONLY the tables required to answer the user query.\n     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS score \n     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required\n     to calculate the above fields, If you found any of those columns in any table then include that table name as well along with\n     other table names that are required to answer the user query.\n     Below are the columns name:\n     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps]>>\n     Rules:\n     - Preserve user intent.\n     - Use ONLY tables present in schema.\n     - Do NOT invent tables.\n     - Do NOT explain reasoning.\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n    USER_QUERY:list employees working from hubli business unit\n    TARGET_DB:enventure\n    DB_SCHEMA:{'enventure': {'employeedetails': {'columns': {'ï»¿ID': 'INTEGER', 'dtDate': 'TEXT', 'emp_id': 'INTEGER', 'emp_code': 'INTEGER', 'emp_name': 'TEXT', 'iSBU': 'INTEGER', 'sSBU': 'TEXT', 'iRM1': 'INTEGER', 'sRM1': 'TEXT', 'iRoleID': 'INTEGER', 'sRMRole': 'TEXT', 'sResourceRole': 'TEXT', 'isGET': 'INTEGER', 'isConsultant': 'INTEGER', 'iCTC': 'INTEGER', 'sDesignation': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'iOnsite': 'INTEGER', 'dtDateUpdatedOn': 'TEXT', 'tempdate': 'TEXT'}}, 'pulsedb': {'columns': {'ID': 'BIGINT', 'dtDate': 'TEXT', 'sTaskName': 'TEXT', 'sPIRNo': 'TEXT', 'sClientName': 'TEXT', 'sProjectName': 'TEXT', 'sContractType': 'TEXT', 'sSBU': 'TEXT', 'sBusinessUnit': 'TEXT', 'sProjectManager': 'TEXT', 'sCustomerProjectManager': 'TEXT', 'sTotalEstimate': 'DOUBLE', 'dtTaskCreatedDate': 'TEXT', 'dtDueDate': 'TEXT', 'dtDeliveryDueDate': 'TEXT', 'dtCompletedDate': 'TEXT', 'iNoofMinorErrors': 'TEXT', 'iNoofMajorErrors': 'TEXT', 'sWorkType': 'TEXT', 'sResourceName': 'TEXT', 'sEstimate': 'DOUBLE', 'sBilledHours': 'DOUBLE', 'sLogHours': 'DOUBLE', 'sCumProgress': 'BIGINT', 'sDesignUserForErrorCalculation': 'TEXT', 'sBilledHoursForErrorCalc': 'DOUBLE', 'iUserType': 'BIGINT', 'sDesignStream': 'TEXT', 'iExternalMinorErrors': 'BIGINT', 'iExternalMajorErrors': 'BIGINT', 'iMonth': 'BIGINT', 'iYear': 'BIGINT', 'dtUpdatedOn': 'TEXT', 'sService': 'TEXT', 'sService_Task': 'TEXT', 'sService_Difficulty': 'TEXT', 'sService_Code': 'TEXT', 'sParentSBU': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'sParentRM': 'TEXT', 'sRole': 'TEXT', 'sOnsite': 'TEXT', 'sDesignation': 'TEXT', 'sUnit': 'TEXT', 'sAttendanceCapacity': 'DOUBLE', 'sAttendanceSBU': 'TEXT', 'sAttendanceBusinessUnit': 'TEXT', 'sPMRole': 'TEXT', 'sPMDesignation': 'TEXT', 'sRMRole': 'TEXT', 'sRMDesignation': 'TEXT', 'sAttendanceCapacityForWastage': 'DOUBLE', 'sNPSRespondent': 'TEXT', 'sEmployeeCode': 'DOUBLE', 'sNps': 'TEXT', 'sNPSRespondentEmail': 'TEXT', 'noofpqcfiles': 'BIGINT', 'noofsqcfiles': 'BIGINT', 'noofsqcchecklist': 'TINYINT', 'noofpqcchecklist': 'TINYINT', 'task_description': 'TEXT'}}}}\n    ", additional_kwargs={}, response_metadata={})]
2026-04-04 14:57:04,361-logtalk2db-INFO-MainThread-Table Prompt ready, its now a prompt value


2026-04-04 14:57:04,362-logtalk2db-INFO-MainThread-Trigering functions to build table schema
Table Prompt with utilisation:
2026-04-04 14:57:04,362-logtalk2db-INFO-MainThread-Invoking table prompt
messages=[SystemMessage(content='\n     you are a database schema analyzer.\n     Task: Select ONLY the tables required to answer the user query.\n     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS score \n     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required\n     to calculate the above fields, If you found any of those columns in any table then include that table name as well along with\n     other table names that are required to answer the user query.\n     Below are the columns name:\n     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps]>>\n     Rules:\n     - Preserve user intent.\n     - Use ONLY tables present in schema.\n     - Do NOT invent tables.\n     - Do NOT explain reasoning.\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n    USER_QUERY:list employees working from hubli business unit and their utilisation\n    TARGET_DB:enventure\n    DB_SCHEMA:{'enventure': {'employeedetails': {'columns': {'ï»¿ID': 'INTEGER', 'dtDate': 'TEXT', 'emp_id': 'INTEGER', 'emp_code': 'INTEGER', 'emp_name': 'TEXT', 'iSBU': 'INTEGER', 'sSBU': 'TEXT', 'iRM1': 'INTEGER', 'sRM1': 'TEXT', 'iRoleID': 'INTEGER', 'sRMRole': 'TEXT', 'sResourceRole': 'TEXT', 'isGET': 'INTEGER', 'isConsultant': 'INTEGER', 'iCTC': 'INTEGER', 'sDesignation': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'iOnsite': 'INTEGER', 'dtDateUpdatedOn': 'TEXT', 'tempdate': 'TEXT'}}, 'pulsedb': {'columns': {'ID': 'BIGINT', 'dtDate': 'TEXT', 'sTaskName': 'TEXT', 'sPIRNo': 'TEXT', 'sClientName': 'TEXT', 'sProjectName': 'TEXT', 'sContractType': 'TEXT', 'sSBU': 'TEXT', 'sBusinessUnit': 'TEXT', 'sProjectManager': 'TEXT', 'sCustomerProjectManager': 'TEXT', 'sTotalEstimate': 'DOUBLE', 'dtTaskCreatedDate': 'TEXT', 'dtDueDate': 'TEXT', 'dtDeliveryDueDate': 'TEXT', 'dtCompletedDate': 'TEXT', 'iNoofMinorErrors': 'TEXT', 'iNoofMajorErrors': 'TEXT', 'sWorkType': 'TEXT', 'sResourceName': 'TEXT', 'sEstimate': 'DOUBLE', 'sBilledHours': 'DOUBLE', 'sLogHours': 'DOUBLE', 'sCumProgress': 'BIGINT', 'sDesignUserForErrorCalculation': 'TEXT', 'sBilledHoursForErrorCalc': 'DOUBLE', 'iUserType': 'BIGINT', 'sDesignStream': 'TEXT', 'iExternalMinorErrors': 'BIGINT', 'iExternalMajorErrors': 'BIGINT', 'iMonth': 'BIGINT', 'iYear': 'BIGINT', 'dtUpdatedOn': 'TEXT', 'sService': 'TEXT', 'sService_Task': 'TEXT', 'sService_Difficulty': 'TEXT', 'sService_Code': 'TEXT', 'sParentSBU': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'sParentRM': 'TEXT', 'sRole': 'TEXT', 'sOnsite': 'TEXT', 'sDesignation': 'TEXT', 'sUnit': 'TEXT', 'sAttendanceCapacity': 'DOUBLE', 'sAttendanceSBU': 'TEXT', 'sAttendanceBusinessUnit': 'TEXT', 'sPMRole': 'TEXT', 'sPMDesignation': 'TEXT', 'sRMRole': 'TEXT', 'sRMDesignation': 'TEXT', 'sAttendanceCapacityForWastage': 'DOUBLE', 'sNPSRespondent': 'TEXT', 'sEmployeeCode': 'DOUBLE', 'sNps': 'TEXT', 'sNPSRespondentEmail': 'TEXT', 'noofpqcfiles': 'BIGINT', 'noofsqcfiles': 'BIGINT', 'noofsqcchecklist': 'TINYINT', 'noofpqcchecklist': 'TINYINT', 'task_description': 'TEXT'}}}}\n    ", additional_kwargs={}, response_metadata={})]
2026-04-04 14:36:58,996-logtalk2db-INFO-MainThread-Table Prompt ready, its now a prompt value


2026-04-04 15:03:20,053-logtalk2db-INFO-MainThread-Invoking query prompt
Query Promt normal:
messages=[SystemMessage(content='\n     You are an expert MySQL developer.\n     Task:\n     Generate a valid MySQL query that answers the user question.\n     Rules:\n     - Use ONLY tables and columns present in DB_SCHEMA.\n     - Follow MySQL syntax strictly.\n     - Always prefix tables with database name (database.table).\n     - NAME FILTERS: Always use the `LIKE` operator with wildcards for name or other search term when required. \n       Example: select * from hr.employees where last_name like "%Haan%";\n     - Use explicit JOIN conditions based on relations.\n     - Do NOT invent tables or columns if required information not present then return SELECT 1.\n     - Generate ONLY a SELECT query.\n     - Decide using SELECT * based on users query otherwise only use necessary columns.\n     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS score \n     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required\n     to calculate the above fields therefore in a MYSQL query along with other columns required to answer user query\n     include the following columns as well.\n     Below are the columns name:\n     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps]>>\n     Example:\n     user_query: list employees data whose salary>20000\n     mysql_query: SELECT * FROM DATABASENAME.TABLENAME WHERE SALARY>20000\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n      USER_QUERY:list employees working from hubli business unit\n      DATABASE:enventure\n      DB_SCHEMA:{'enventure': {'employeedetails': {'columns': {'ï»¿ID': 'INTEGER', 'dtDate': 'TEXT', 'emp_id': 'INTEGER', 'emp_code': 'INTEGER', 'emp_name': 'TEXT', 'iSBU': 'INTEGER', 'sSBU': 'TEXT', 'iRM1': 'INTEGER', 'sRM1': 'TEXT', 'iRoleID': 'INTEGER', 'sRMRole': 'TEXT', 'sResourceRole': 'TEXT', 'isGET': 'INTEGER', 'isConsultant': 'INTEGER', 'iCTC': 'INTEGER', 'sDesignation': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'iOnsite': 'INTEGER', 'dtDateUpdatedOn': 'TEXT', 'tempdate': 'TEXT'}, 'primary_key': [], 'relations': []}}}", additional_kwargs={}, response_metadata={})]
2026-04-04 15:03:20,104-logtalk2db-INFO-MainThread-Query prompt ready, It's now a prompt value


2026-04-04 15:03:20,106-logtalk2db-INFO-MainThread-Triggering functions to build db_schema
2026-04-04 15:03:20,112-logtalk2db-INFO-MainThread-db_schema built successfully


Query Promt with utilization:
messages=[SystemMessage(content='\n     You are an expert MySQL developer.\n     Task:\n     Generate a valid MySQL query that answers the user question.\n     Rules:\n     - Use ONLY tables and columns present in DB_SCHEMA.\n     - Follow MySQL syntax strictly.\n     - Always prefix tables with database name (database.table).\n     - NAME FILTERS: Always use the `LIKE` operator with wildcards for name or other search term when required. \n       Example: select * from hr.employees where last_name like "%Haan%";\n     - Use explicit JOIN conditions based on relations.\n     - Do NOT invent tables or columns if required information not present then return SELECT 1.\n     - Generate ONLY a SELECT query.\n     - Decide using SELECT * based on users query otherwise only use necessary columns.\n     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS score \n     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required\n     to calculate the above fields therefore in a MYSQL query along with other columns required to answer user query\n     include the following columns as well.\n     Below are the columns name:\n     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps]>>\n     Example:\n     user_query: list employees data whose salary>20000\n     mysql_query: SELECT * FROM DATABASENAME.TABLENAME WHERE SALARY>20000\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n      USER_QUERY:list employees working from hubli business unit and their utilisation\n      DATABASE:enventure\n      DB_SCHEMA:{'enventure': {'employeedetails': {'columns': {'ï»¿ID': 'INTEGER', 'dtDate': 'TEXT', 'emp_id': 'INTEGER', 'emp_code': 'INTEGER', 'emp_name': 'TEXT', 'iSBU': 'INTEGER', 'sSBU': 'TEXT', 'iRM1': 'INTEGER', 'sRM1': 'TEXT', 'iRoleID': 'INTEGER', 'sRMRole': 'TEXT', 'sResourceRole': 'TEXT', 'isGET': 'INTEGER', 'isConsultant': 'INTEGER', 'iCTC': 'INTEGER', 'sDesignation': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'iOnsite': 'INTEGER', 'dtDateUpdatedOn': 'TEXT', 'tempdate': 'TEXT'}, 'primary_key': [], 'relations': []}, 'pulsedb': {'columns': {'ID': 'BIGINT', 'dtDate': 'TEXT', 'sTaskName': 'TEXT', 'sPIRNo': 'TEXT', 'sClientName': 'TEXT', 'sProjectName': 'TEXT', 'sContractType': 'TEXT', 'sSBU': 'TEXT', 'sBusinessUnit': 'TEXT', 'sProjectManager': 'TEXT', 'sCustomerProjectManager': 'TEXT', 'sTotalEstimate': 'DOUBLE', 'dtTaskCreatedDate': 'TEXT', 'dtDueDate': 'TEXT', 'dtDeliveryDueDate': 'TEXT', 'dtCompletedDate': 'TEXT', 'iNoofMinorErrors': 'TEXT', 'iNoofMajorErrors': 'TEXT', 'sWorkType': 'TEXT', 'sResourceName': 'TEXT', 'sEstimate': 'DOUBLE', 'sBilledHours': 'DOUBLE', 'sLogHours': 'DOUBLE', 'sCumProgress': 'BIGINT', 'sDesignUserForErrorCalculation': 'TEXT', 'sBilledHoursForErrorCalc': 'DOUBLE', 'iUserType': 'BIGINT', 'sDesignStream': 'TEXT', 'iExternalMinorErrors': 'BIGINT', 'iExternalMajorErrors': 'BIGINT', 'iMonth': 'BIGINT', 'iYear': 'BIGINT', 'dtUpdatedOn': 'TEXT', 'sService': 'TEXT', 'sService_Task': 'TEXT', 'sService_Difficulty': 'TEXT', 'sService_Code': 'TEXT', 'sParentSBU': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'sParentRM': 'TEXT', 'sRole': 'TEXT', 'sOnsite': 'TEXT', 'sDesignation': 'TEXT', 'sUnit': 'TEXT', 'sAttendanceCapacity': 'DOUBLE', 'sAttendanceSBU': 'TEXT', 'sAttendanceBusinessUnit': 'TEXT', 'sPMRole': 'TEXT', 'sPMDesignation': 'TEXT', 'sRMRole': 'TEXT', 'sRMDesignation': 'TEXT', 'sAttendanceCapacityForWastage': 'DOUBLE', 'sNPSRespondent': 'TEXT', 'sEmployeeCode': 'DOUBLE', 'sNps': 'TEXT', 'sNPSRespondentEmail': 'TEXT', 'noofpqcfiles': 'BIGINT', 'noofsqcfiles': 'BIGINT', 'noofsqcchecklist': 'TINYINT', 'noofpqcchecklist': 'TINYINT', 'task_description': 'TEXT'}, 'primary_key': [], 'relations': []}}}", additional_kwargs={}, response_metadata={})]
2026-04-04 15:03:20,112-logtalk2db-INFO-MainThread-Invoking query prompt
2026-04-04 15:03:20,114-logtalk2db-INFO-MainThread-Query prompt ready, It's now a prompt value
"""

#  python -m backend.src.data_fetch.prompts