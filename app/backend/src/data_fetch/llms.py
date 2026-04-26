#This module provides the LLM models to interact with
# from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from backend.src.utils.app_logger import logger
from backend.src.data_fetch.prompts import ConversationalModel, SchemaFiltrationModel, QueryModel, FinalResponseModel
from backend.src.core.config import configured_attributes
from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio

# "sqlcoder-7b"
"""
model=ChatOllama(
    model=configured_attributes().MODEL_NAME,
    keep_alive="2m",
    temperature=0.1,
    top_p=0.9,
    num_predict=500
)
"""

"""
models_v2=[
  "gemini-2.5-pro",
  "gemini-2.5-flash",
  "gemini-2.5-flash-lite"
]

models_v3=[
  "gemini-3-pro-preview",
  "gemini-3-flash-preview",
  "gemini-3-deep-think",
]
"""

genai_model=ChatGoogleGenerativeAI(model="gemini-2.5-flash",
                                   api_key=configured_attributes().GEMINI_API_KEY)

# table_generation_model=model.with_structured_output(schema=SchemaFiltrationModel)
# query_generation_model=model.with_structured_output(schema=QueryModel)
conversation_model=genai_model.with_structured_output(schema=ConversationalModel)
table_generation_model=genai_model.with_structured_output(schema=SchemaFiltrationModel)
query_generation_model=genai_model.with_structured_output(schema=QueryModel)
final_response_model=genai_model.with_structured_output(schema=FinalResponseModel)

async def get_conversation(conversation_prompt):
   """This function invoke llm and provide its reponse i.e Answer to user question or 1 if content not available to answer the question"""
   try:
      logger.info("Invoking conversation model")
      response=await conversation_model.ainvoke(input=conversation_prompt)
      logger.info("Conversational model provided response successfully")
      return response.reply
   except Exception as e:
      logger.exception("Error while invoking Conversational Model: %s",e)
      raise

async def get_tables(tableprompt):
   """This function invoke llm and provide its response i.e tables"""
   try:
      logger.info("Invoking tables generation model")
      response=await table_generation_model.ainvoke(input=tableprompt)
      logger.info("tables generation model provided response successfully")
      return response.table_names
   except Exception as e:
      logger.exception("Error while invoking Table generation model: %s",e)
      raise

async def get_query(queryprompt):
   """This function invoke llm and provide its response i.e query"""
   try:
      logger.info("Invoking query generation model")
      response=await query_generation_model.ainvoke(input=queryprompt)
      logger.info("query generation model provided response successfully")
      return response.query
   except Exception as e:
      logger.exception("Error while invoking query generation model: %s",e)
      raise
    
async def get_final_summary(summary_prompt):
   """This function invoke llm and provide summary of the data"""
   try:
      logger.info("Invoking Final response model")
      response=await final_response_model.ainvoke(input=summary_prompt)
      logger.info("Final response model invoked successfully")
      return response.reply
   except Exception as e:
      logger.exception("Error while invoking Final response model: %s", e)
      raise

#To unload from ram
"""
curl http://localhost:11434/api/generate -d '{
  "model": "sqlcoder-7b",
  "prompt": "",
  "keep_alive": 0
}'
"""
# ollama rm sqlcoder-7b (To remove model from machine not just ram)

# python -m backend.src.data_fetch.llms

if __name__=="__main__":
   try:
      async def main_tablefetch():
         tableprompt_normal="""messages=[SystemMessage(content='\n     you are a database schema analyzer.\n     Task: Select ONLY the tables required to answer the user query.\n     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS score \n     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required\n     to calculate the above fields, If you found any of those columns in any table then include that table name as well along with\n     other table names that are required to answer the user query.\n     Below are the columns name:\n     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps]>>\n     Rules:\n     - Preserve user intent.\n     - Use ONLY tables present in schema.\n     - Do NOT invent tables.\n     - Do NOT explain reasoning.\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n    USER_QUERY:list employees working from hubli business unit\n    TARGET_DB:enventure\n    DB_SCHEMA:{'enventure': {'employeedetails': {'columns': {'ï»¿ID': 'INTEGER', 'dtDate': 'TEXT', 'emp_id': 'INTEGER', 'emp_code': 'INTEGER', 'emp_name': 'TEXT', 'iSBU': 'INTEGER', 'sSBU': 'TEXT', 'iRM1': 'INTEGER', 'sRM1': 'TEXT', 'iRoleID': 'INTEGER', 'sRMRole': 'TEXT', 'sResourceRole': 'TEXT', 'isGET': 'INTEGER', 'isConsultant': 'INTEGER', 'iCTC': 'INTEGER', 'sDesignation': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'iOnsite': 'INTEGER', 'dtDateUpdatedOn': 'TEXT', 'tempdate': 'TEXT'}}, 'pulsedb': {'columns': {'ID': 'BIGINT', 'dtDate': 'TEXT', 'sTaskName': 'TEXT', 'sPIRNo': 'TEXT', 'sClientName': 'TEXT', 'sProjectName': 'TEXT', 'sContractType': 'TEXT', 'sSBU': 'TEXT', 'sBusinessUnit': 'TEXT', 'sProjectManager': 'TEXT', 'sCustomerProjectManager': 'TEXT', 'sTotalEstimate': 'DOUBLE', 'dtTaskCreatedDate': 'TEXT', 'dtDueDate': 'TEXT', 'dtDeliveryDueDate': 'TEXT', 'dtCompletedDate': 'TEXT', 'iNoofMinorErrors': 'TEXT', 'iNoofMajorErrors': 'TEXT', 'sWorkType': 'TEXT', 'sResourceName': 'TEXT', 'sEstimate': 'DOUBLE', 'sBilledHours': 'DOUBLE', 'sLogHours': 'DOUBLE', 'sCumProgress': 'BIGINT', 'sDesignUserForErrorCalculation': 'TEXT', 'sBilledHoursForErrorCalc': 'DOUBLE', 'iUserType': 'BIGINT', 'sDesignStream': 'TEXT', 'iExternalMinorErrors': 'BIGINT', 'iExternalMajorErrors': 'BIGINT', 'iMonth': 'BIGINT', 'iYear': 'BIGINT', 'dtUpdatedOn': 'TEXT', 'sService': 'TEXT', 'sService_Task': 'TEXT', 'sService_Difficulty': 'TEXT', 'sService_Code': 'TEXT', 'sParentSBU': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'sParentRM': 'TEXT', 'sRole': 'TEXT', 'sOnsite': 'TEXT', 'sDesignation': 'TEXT', 'sUnit': 'TEXT', 'sAttendanceCapacity': 'DOUBLE', 'sAttendanceSBU': 'TEXT', 'sAttendanceBusinessUnit': 'TEXT', 'sPMRole': 'TEXT', 'sPMDesignation': 'TEXT', 'sRMRole': 'TEXT', 'sRMDesignation': 'TEXT', 'sAttendanceCapacityForWastage': 'DOUBLE', 'sNPSRespondent': 'TEXT', 'sEmployeeCode': 'DOUBLE', 'sNps': 'TEXT', 'sNPSRespondentEmail': 'TEXT', 'noofpqcfiles': 'BIGINT', 'noofsqcfiles': 'BIGINT', 'noofsqcchecklist': 'TINYINT', 'noofpqcchecklist': 'TINYINT', 'task_description': 'TEXT'}}}}\n    ", additional_kwargs={}, response_metadata={})]"""
         result=await get_tables(tableprompt=tableprompt_normal)
         print("Tables_normal:",result,sep="\n") #['employeedetails'] #['pulsedb']

         print("\n")
         tableprompt_utilization="""[SystemMessage(content='\n     you are a database schema analyzer.\n     Task: Select ONLY the tables required to answer the user query.\n     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS score \n     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required\n     to calculate the above fields, If you found any of those columns in any table then include that table name as well along with\n     other table names that are required to answer the user query.\n     Below are the columns name:\n     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps]>>\n     Rules:\n     - Preserve user intent.\n     - Use ONLY tables present in schema.\n     - Do NOT invent tables.\n     - Do NOT explain reasoning.\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n    USER_QUERY:list employees working from hubli business unit and their utilisation\n    TARGET_DB:enventure\n    DB_SCHEMA:{'enventure': {'employeedetails': {'columns': {'ï»¿ID': 'INTEGER', 'dtDate': 'TEXT', 'emp_id': 'INTEGER', 'emp_code': 'INTEGER', 'emp_name': 'TEXT', 'iSBU': 'INTEGER', 'sSBU': 'TEXT', 'iRM1': 'INTEGER', 'sRM1': 'TEXT', 'iRoleID': 'INTEGER', 'sRMRole': 'TEXT', 'sResourceRole': 'TEXT', 'isGET': 'INTEGER', 'isConsultant': 'INTEGER', 'iCTC': 'INTEGER', 'sDesignation': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'iOnsite': 'INTEGER', 'dtDateUpdatedOn': 'TEXT', 'tempdate': 'TEXT'}}, 'pulsedb': {'columns': {'ID': 'BIGINT', 'dtDate': 'TEXT', 'sTaskName': 'TEXT', 'sPIRNo': 'TEXT', 'sClientName': 'TEXT', 'sProjectName': 'TEXT', 'sContractType': 'TEXT', 'sSBU': 'TEXT', 'sBusinessUnit': 'TEXT', 'sProjectManager': 'TEXT', 'sCustomerProjectManager': 'TEXT', 'sTotalEstimate': 'DOUBLE', 'dtTaskCreatedDate': 'TEXT', 'dtDueDate': 'TEXT', 'dtDeliveryDueDate': 'TEXT', 'dtCompletedDate': 'TEXT', 'iNoofMinorErrors': 'TEXT', 'iNoofMajorErrors': 'TEXT', 'sWorkType': 'TEXT', 'sResourceName': 'TEXT', 'sEstimate': 'DOUBLE', 'sBilledHours': 'DOUBLE', 'sLogHours': 'DOUBLE', 'sCumProgress': 'BIGINT', 'sDesignUserForErrorCalculation': 'TEXT', 'sBilledHoursForErrorCalc': 'DOUBLE', 'iUserType': 'BIGINT', 'sDesignStream': 'TEXT', 'iExternalMinorErrors': 'BIGINT', 'iExternalMajorErrors': 'BIGINT', 'iMonth': 'BIGINT', 'iYear': 'BIGINT', 'dtUpdatedOn': 'TEXT', 'sService': 'TEXT', 'sService_Task': 'TEXT', 'sService_Difficulty': 'TEXT', 'sService_Code': 'TEXT', 'sParentSBU': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'sParentRM': 'TEXT', 'sRole': 'TEXT', 'sOnsite': 'TEXT', 'sDesignation': 'TEXT', 'sUnit': 'TEXT', 'sAttendanceCapacity': 'DOUBLE', 'sAttendanceSBU': 'TEXT', 'sAttendanceBusinessUnit': 'TEXT', 'sPMRole': 'TEXT', 'sPMDesignation': 'TEXT', 'sRMRole': 'TEXT', 'sRMDesignation': 'TEXT', 'sAttendanceCapacityForWastage': 'DOUBLE', 'sNPSRespondent': 'TEXT', 'sEmployeeCode': 'DOUBLE', 'sNps': 'TEXT', 'sNPSRespondentEmail': 'TEXT', 'noofpqcfiles': 'BIGINT', 'noofsqcfiles': 'BIGINT', 'noofsqcchecklist': 'TINYINT', 'noofpqcchecklist': 'TINYINT', 'task_description': 'TEXT'}}}}\n    ", additional_kwargs={}, response_metadata={})]"""
         result=await get_tables(tableprompt=tableprompt_utilization)
         print("Tables_with_utilisation:",result,sep="\n") #['employeedetails', 'pulsedb']
         
   except Exception as e:
      print("----ERROR MESSAGE----",e)
   
   try:
      async def main_querygenerate():
         queryprompt_normal="""messages=[SystemMessage(content='\n     You are an expert MySQL developer.\n     Task:\n     Generate a valid MySQL query that answers the user question.\n     Rules:\n     - Use ONLY tables and columns present in DB_SCHEMA.\n     - Follow MySQL syntax strictly.\n     - Always prefix tables with database name (database.table).\n     - NAME FILTERS: Always use the `LIKE` operator with wildcards for name or other search term when required. \n       Example: select * from hr.employees where last_name like "%Haan%";\n     - Use explicit JOIN conditions based on relations.\n     - Do NOT invent tables or columns if required information not present then return SELECT 1.\n     - Generate ONLY a SELECT query.\n     - Decide using SELECT * based on users query otherwise only use necessary columns.\n     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS score \n     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required\n     to calculate the above fields therefore in a MYSQL query along with other columns required to answer user query\n     include the following columns as well.\n     Below are the columns name:\n     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps]>>\n     Example:\n     user_query: list employees data whose salary>20000\n     mysql_query: SELECT * FROM DATABASENAME.TABLENAME WHERE SALARY>20000\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n      USER_QUERY:list employees working from hubli business unit\n      DATABASE:enventure\n      DB_SCHEMA:{'enventure': {'employeedetails': {'columns': {'ï»¿ID': 'INTEGER', 'dtDate': 'TEXT', 'emp_id': 'INTEGER', 'emp_code': 'INTEGER', 'emp_name': 'TEXT', 'iSBU': 'INTEGER', 'sSBU': 'TEXT', 'iRM1': 'INTEGER', 'sRM1': 'TEXT', 'iRoleID': 'INTEGER', 'sRMRole': 'TEXT', 'sResourceRole': 'TEXT', 'isGET': 'INTEGER', 'isConsultant': 'INTEGER', 'iCTC': 'INTEGER', 'sDesignation': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'iOnsite': 'INTEGER', 'dtDateUpdatedOn': 'TEXT', 'tempdate': 'TEXT'}, 'primary_key': [], 'relations': []}}}", additional_kwargs={}, response_metadata={})]"""
         query=await get_query(queryprompt=queryprompt_normal)
         print("QUERY_NORMAL:",query) #SELECT * FROM enventure.employeedetails WHERE sParentBusinessUnit LIKE "%hubli%"
         print("\n")

         queryprompt_utilization="""messages=[SystemMessage(content='\n     You are an expert MySQL developer.\n     Task:\n     Generate a valid MySQL query that answers the user question.\n     Rules:\n     - Use ONLY tables and columns present in DB_SCHEMA.\n     - Follow MySQL syntax strictly.\n     - Always prefix tables with database name (database.table).\n     - NAME FILTERS: Always use the `LIKE` operator with wildcards for name or other search term when required. \n       Example: select * from hr.employees where last_name like "%Haan%";\n     - Use explicit JOIN conditions based on relations.\n     - Do NOT invent tables or columns if required information not present then return SELECT 1.\n     - Generate ONLY a SELECT query.\n     - Decide using SELECT * based on users query otherwise only use necessary columns.\n     Exception: <<If the user query includes fields such as Utilization Internal, Utilisation Client, Capacity Billed Hour, NPS score \n     these fields are to be calculated, not present directly in the database thus I mention below the columnnames that are required\n     to calculate the above fields therefore in a MYSQL query along with other columns required to answer user query\n     include the following columns as well.\n     Below are the columns name:\n     columns:[sRole, sDesignation, sBilledHours, sAttendanceCapacityForWastage, sNps]>>\n     Example:\n     user_query: list employees data whose salary>20000\n     mysql_query: SELECT * FROM DATABASENAME.TABLENAME WHERE SALARY>20000\n     ', additional_kwargs={}, response_metadata={}), HumanMessage(content="\n      USER_QUERY:list employees working from hubli business unit and their utilisation\n      DATABASE:enventure\n      DB_SCHEMA:{'enventure': {'employeedetails': {'columns': {'ï»¿ID': 'INTEGER', 'dtDate': 'TEXT', 'emp_id': 'INTEGER', 'emp_code': 'INTEGER', 'emp_name': 'TEXT', 'iSBU': 'INTEGER', 'sSBU': 'TEXT', 'iRM1': 'INTEGER', 'sRM1': 'TEXT', 'iRoleID': 'INTEGER', 'sRMRole': 'TEXT', 'sResourceRole': 'TEXT', 'isGET': 'INTEGER', 'isConsultant': 'INTEGER', 'iCTC': 'INTEGER', 'sDesignation': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'iOnsite': 'INTEGER', 'dtDateUpdatedOn': 'TEXT', 'tempdate': 'TEXT'}, 'primary_key': [], 'relations': []}, 'pulsedb': {'columns': {'ID': 'BIGINT', 'dtDate': 'TEXT', 'sTaskName': 'TEXT', 'sPIRNo': 'TEXT', 'sClientName': 'TEXT', 'sProjectName': 'TEXT', 'sContractType': 'TEXT', 'sSBU': 'TEXT', 'sBusinessUnit': 'TEXT', 'sProjectManager': 'TEXT', 'sCustomerProjectManager': 'TEXT', 'sTotalEstimate': 'DOUBLE', 'dtTaskCreatedDate': 'TEXT', 'dtDueDate': 'TEXT', 'dtDeliveryDueDate': 'TEXT', 'dtCompletedDate': 'TEXT', 'iNoofMinorErrors': 'TEXT', 'iNoofMajorErrors': 'TEXT', 'sWorkType': 'TEXT', 'sResourceName': 'TEXT', 'sEstimate': 'DOUBLE', 'sBilledHours': 'DOUBLE', 'sLogHours': 'DOUBLE', 'sCumProgress': 'BIGINT', 'sDesignUserForErrorCalculation': 'TEXT', 'sBilledHoursForErrorCalc': 'DOUBLE', 'iUserType': 'BIGINT', 'sDesignStream': 'TEXT', 'iExternalMinorErrors': 'BIGINT', 'iExternalMajorErrors': 'BIGINT', 'iMonth': 'BIGINT', 'iYear': 'BIGINT', 'dtUpdatedOn': 'TEXT', 'sService': 'TEXT', 'sService_Task': 'TEXT', 'sService_Difficulty': 'TEXT', 'sService_Code': 'TEXT', 'sParentSBU': 'TEXT', 'sParentBusinessUnit': 'TEXT', 'sParentRM': 'TEXT', 'sRole': 'TEXT', 'sOnsite': 'TEXT', 'sDesignation': 'TEXT', 'sUnit': 'TEXT', 'sAttendanceCapacity': 'DOUBLE', 'sAttendanceSBU': 'TEXT', 'sAttendanceBusinessUnit': 'TEXT', 'sPMRole': 'TEXT', 'sPMDesignation': 'TEXT', 'sRMRole': 'TEXT', 'sRMDesignation': 'TEXT', 'sAttendanceCapacityForWastage': 'DOUBLE', 'sNPSRespondent': 'TEXT', 'sEmployeeCode': 'DOUBLE', 'sNps': 'TEXT', 'sNPSRespondentEmail': 'TEXT', 'noofpqcfiles': 'BIGINT', 'noofsqcfiles': 'BIGINT', 'noofsqcchecklist': 'TINYINT', 'noofpqcchecklist': 'TINYINT', 'task_description': 'TEXT'}, 'primary_key': [], 'relations': []}}}", additional_kwargs={}, response_metadata={})]"""
         query=await get_query(queryprompt=queryprompt_utilization)
         print("QUERY_UTILISATION:",query)
         """
         SELECT enventure.employeedetails.*, enventure.pulsedb.sRole, enventure.pulsedb.sDesignation, enventure.pulsedb.sBilledHours, enventure.pulsedb.sAttendanceCapacityForWastage, enventure.pulsedb.sNps FROM enventure.employeedetails JOIN enventure.pulsedb ON enventure.employeedetails.emp_name = enventure.pulsedb.sResourceName WHERE enventure.pulsedb.sBusinessUnit LIKE "%hubli%"
         """
         print("\n")

   except Exception as e:
      print("----ERROR MESSAGE----")
   
   try:
      async def main_conversation():
         conversationprompt_normal="""
         2026-04-12 11:26:10,264-logtalk2db-INFO-MainThread-Invoking conversational_propmpt_template
         Conversational_prompt_value: messages=[SystemMessage(content='Act as a normal conversational patner and helpful assistant.\n    The provided CHAT_HISTORY contains the current conversation. \n    The VERY LAST message is the new User Query. \n    Firstly, understand the intent of the question wheather they are seeking \n    data from database or its a normal question.\n    If you can answer the user question from the chathistory provided below or\n    from your general knowledge then give a professional, concise response.\n    else,\n    if the question requires extra knowledge that is data from database then \n    just reply 1, I mean strictly 1, Do NOT explain your choice. Do NOT say "I think the answer is 1" just reply with 1', additional_kwargs={}, response_metadata={}), HumanMessage(content="CHAT_HISTORY:[('human', 'List employees and their reporting managers')]", additional_kwargs={}, response_metadata={})]"""
         response=await get_conversation(conversation_prompt=conversationprompt_normal)
         print("AI Response:",response,sep="\n")
         """
         AI Response:
         Hello!
         AI Response:
         Kangchenjunga is the highest peak in India.
         AI Response:
         1
         AI Response:
         1
         """
   except Exception as e:
      print("----ERROR MESSAGE----")

# asyncio.run(main_tablefetch())
   asyncio.run(main_conversation())
   