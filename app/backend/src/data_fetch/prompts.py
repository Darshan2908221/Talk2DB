#This module has the prompts to feed LLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
from backend.src.core.config import configured_attributes
from backend.src.data_fetch.db_schema import get_table_schema, get_db_schema
from backend.src.utils.app_logger import logger
from pydantic import BaseModel, Field
from typing import Annotated, Optional
import json

#Pydantic model to classify the intent of question
class ConversationalModel(BaseModel):
    reply:Annotated[str | int, Field("...", description="""
                                    DECISION LOGIC:
                                    1. ANALYZE: Examine the last message which is the user query in CHAT_HISTORY.
                                    2. CHAT: If the query is a greeting, general knowledge, or can be answered using existing info in CHAT_HISTORY, provide a concise, professional response.
                                    3. DATABASE: If the query requires internal metrics (e.g., NPS, Utilization, Capacity, Employee data , etc..) NOT present in the chat history for the same question,
                                    return ONLY the integer 1.
                                    STRICT RULES:
                                    - No preambles (e.g., do NOT say 'I think the answer is...').
                                    - If database retrieval is needed, output '1' and nothing else.""")]

#prompt to classify question
conversational_prompt_template=ChatPromptTemplate([
    ("system", 
    """Act as a normal conversational patner and helpful assistant.
    The provided CHAT_HISTORY contains the current conversation. 
    The VERY LAST message is the new User Query. 
    Firstly, understand the intent of the question wheather they are seeking 
    data from database or its a normal question.
    If you can answer the user question from the chathistory provided below or
    from your general knowledge then give a professional, concise response.
    else,
    if the question requires extra knowledge that is data from database then 
    just reply 1, I mean strictly 1, Do NOT explain your choice. Do NOT say "I think the answer is 1" just reply with 1"""),
    ("human",
    """CHAT_HISTORY:{chat_history}""")
])

def get_conversational_prompt(chat_history:list[BaseMessage]):
    logger.info("Invoking conversational_propmpt_template")
    conv_pv=conversational_prompt_template.invoke(chat_history)
    logger.info("Table Prompt ready, its now a prompt value")
    return conv_pv

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
     The very last question or message in the chat history is the new user query, understand the context from chat history
     and select the tables required to answer the user query
     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS Score
     these fields are to be calculated, not present directly in the database thus I mention below the column names from pulsedb table 
     that are required to calculate the above fields, therefore include pulsedb table name in response along with
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
    CHAT_HISTORY:{chat_history}
    TARGET_DB:{target_db}
    DB_SCHEMA:{table_schema}
    """)])

def get_table_prompt(chat_history:list[BaseMessage], table_schema:dict, target_db:str | None=None):
    """This function provides the prompt for the schema filtration"""
    if target_db is None:
        target_db=configured_attributes().DB_NAME
    logger.info("Invoking table prompt")
    table_prompt_value=table_prompt_template.invoke(input=
                                                    {
                                                        # "user_query":user_query,
                                                        "chat_history":chat_history,
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
     The very last question in the chat_history is the new user query thus understand context and requirement
     from the chat history and Generate a valid MySQL query that answers the user question which is the very last message or question in 
     chat history.
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

     EXCEPTION & MANDATORY BEHAVIOR:
     If the user query references 'Utilization', 'NPS', or 'Capacity':
     1. DO NOT use SUM, AVG, or any mathematical operators (+, -, /, *) in the SQL.
     2. DO NOT use GROUP BY. 
     3. You MUST only return the RAW rows.
     4. You MUST include these exact columns from pulsedb: 
     [sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps, sClientName]
     5. Your job ends at FETCHING. The Python layer will handle the math.

    Example for exception:
    User: "Calculate utilization for Mariadas"
    Correct SQL: SELECT T1.emp_name, T2.sBilledHours, T2.sAttendanceCapacityForWastage 
                FROM enventure.employeedetails T1 
                JOIN enventure.pulsedb T2 ON T1.emp_code = T2.sEmployeeCode 
                WHERE T1.sRM1 LIKE "%Mariadas%"
     
     Example for a normal query:
     user_query: list employees data whose salary>20000
     mysql_query: SELECT * FROM DATABASENAME.TABLENAME WHERE SALARY>20000
     """),
     ("human",
      """
      CHAT_HISTORY:{chat_history}
      DATABASE:{target_db}
      DB_SCHEMA:{db_schema}""")])

def get_query_prompt(chat_history:list[BaseMessage], db_schema:dict, target_db:str | None=None):
    """This function provides prompt to get the mysql query"""
    if target_db is None:
        target_db=configured_attributes().DB_NAME
    logger.info("Invoking query prompt")
    query_prompt_value=query_prompt_template.invoke(input=
                                                    {
                                                        # "user_query":user_query,
                                                        "chat_history":chat_history,
                                                        "target_db":target_db,
                                                        "db_schema":db_schema
                                                        })
    logger.info("Query prompt ready, It's now a prompt value")
    return query_prompt_value

#pydantic model to summarize results
class FinalResponseModel(BaseModel):
    reply: str = Field(..., description="The natural language summary of the data.")
    # has_data: bool = Field(..., description="True if rows were found, False if empty.")
    # csv_filename: Optional[str] = Field(None, description="The name of the generated file.")

final_summarizer_prompt_template=ChatPromptTemplate([("system",
                    """
                    You are a Data Analyst. You will receive a sample of database results.
                    Your goal is to summarize the findings naturally.
                    The last message in chat history is new user query.

                    RULES:
                    1. State the TOTAL number of records found.
                    2. Highlight a few examples or patterns from the sample provided.
                    3. If BUSINESS_METRICS provided, answer only for the asked metric by the user and in the end ask would user wants to see other business metrics, mention the names of other metrics that are keys in BUSINESS_METRICS except one that is asked.
                    3. Always conclude by directing the user to the CSV file for the full dataset.
                    4. If the total count is 0, politely inform the user no data was found.
                    """),

                    # Context provided to the LLM:
                    ("human",
                    """
                    chat_history:{chat_history},
                    total_records_found:{row_count},
                    sample_data:{sample_rows_json},
                    business_metrics:{business_metrics}
                    """)])

def get_final_sumarizer_prompt(business_metrics, chat_history:list[BaseMessage], total_records: int, sample_data:json):
    """Provides the prompt for final summarization of results to the LLM"""
    return final_summarizer_prompt_template.invoke(input={
        "chat_history":chat_history,
        "row_count":total_records,
        "sample_rows_json":sample_data,
        "business_metrics":business_metrics
    })


if __name__=="__main__":
    try:
        def main():
            # table_schema = await get_table_schema(target_db="enventure")
            # print("\n")
            # print("Table Prompt normal:",get_table_prompt(user_query="list employees working from hubli business unit",table_schema=table_schema, target_db="enventure"), sep="\n")
            # print("\n")
            # table_schema = await get_table_schema(target_db="enventure")
            # print("\n")
            # print("Table Prompt with utilisation:",get_table_prompt(user_query="list employees working from hubli business unit and their utilisation",table_schema=table_schema, target_db="enventure"), sep="\n")
            # print("\n")
            
            # db_schema= await get_db_schema(target_db="enventure", table_names=['employeedetails'])
            # print("\n")
            # print("Query Promt normal:",get_query_prompt(user_query="list employees working from hubli business unit",db_schema=db_schema),sep="\n")
            # print("\n")
            # db_schema= await get_db_schema(target_db="enventure", table_names=['employeedetails', 'pulsedb'])
            # print("\n")
            # print("Query Promt with utilization:",get_query_prompt(target_db="enventure",user_query="list employees working from hubli business unit and their utilisation",db_schema=db_schema),sep="\n")

            #converation_prompt_template invocation
            print("\n")
            conv_pv=get_conversational_prompt(chat_history=[("human","hi")])
            print("Conversational_prompt_value:",conv_pv)        

    except Exception as e:
        print("ERROR MESSAGE:",e)
    
    main()

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
"""
2026-04-12 10:29:18,686-logtalk2db-INFO-MainThread-Invoking conversational_propmpt_template
Conversational_prompt_value: messages=[SystemMessage(content='Act as a normal conversational patner and helpful assistant.\n    The provided CHAT_HISTORY contains the current conversation. \n    The VERY LAST message is the new User Query. \n    Firstly, understand the intent of the question wheather they are seeking \n    data from database or its a normal question.\n    If you can answer the user question from the chathistory provided below or\n    from your general knowledge then give a professional, concise response.\n    else,\n    if the question requires extra knowledge that is data from database then \n    just reply 1, I mean strictly 1, Do NOT explain your choice. Do NOT say "I think the answer is 1" just reply with 1', additional_kwargs={}, response_metadata={}), HumanMessage(content='"CHAT_HISTORY:[(\'human\', \'hi\')]', additional_kwargs={}, response_metadata={})]
2026-04-12 10:29:18,743-logtalk2db-INFO-MainThread-Table Prompt ready, its now a prompt value
"""
"""
2026-04-12 11:26:10,264-logtalk2db-INFO-MainThread-Invoking conversational_propmpt_template
Conversational_prompt_value: messages=[SystemMessage(content='Act as a normal conversational patner and helpful assistant.\n    The provided CHAT_HISTORY contains the current conversation. \n    The VERY LAST message is the new User Query. \n    Firstly, understand the intent of the question wheather they are seeking \n    data from database or its a normal question.\n    If you can answer the user question from the chathistory provided below or\n    from your general knowledge then give a professional, concise response.\n    else,\n    if the question requires extra knowledge that is data from database then \n    just reply 1, I mean strictly 1, Do NOT explain your choice. Do NOT say "I think the answer is 1" just reply with 1', additional_kwargs={}, response_metadata={}), HumanMessage(content="CHAT_HISTORY:[('human', 'hi')]", additional_kwargs={}, response_metadata={})]
2026-04-12 11:26:10,339-logtalk2db-INFO-MainThread-Table Prompt ready, its now a prompt value
"""
#  python -m backend.src.data_fetch.prompts

