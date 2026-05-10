#This module orchestrate the flow
#Flow
"""
Top level=>
userquery=>get_table_schema=>get_table_prompt=>get_tables=>=>get_db_schema=>get_query_prompt=>get_query=>query_validation=>get_data=>Summary of data
"""
from sqlalchemy import text
from backend.src.utils.app_logger import logger
from backend.src.db_connect.connection import AsyncSessionLocal, engine
from backend.src.data_fetch.prompts import get_table_prompt, get_query_prompt, get_conversational_prompt, get_final_sumarizer_prompt
from backend.src.data_fetch.db_schema import get_table_schema, get_db_schema, get_uploads_tables
from backend.src.data_fetch.llms import get_tables, get_query, get_conversation, get_final_summary
from backend.src.data_fetch.sql_guard import query_validation
from backend.src.data_fetch.businessmetrics import get_capacity_billed_hours, get_nps_score, get_internal_utilization
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from decimal import Decimal
from datetime import datetime, date
import asyncio
import time
import pandas as pd
import json

class REQUIREDCOLUMNSNOTFOUND(Exception):
    pass

class CAPACITYBILLEDHOUR(Exception):
    pass


async def get_data_formatted(user_query:str, session:AsyncSession, mysql_query:str):
    """This function executes the query against the database and fetch results"""
    try:
        logger.info("Executing query against the database")
        data=await session.execute(text(mysql_query))
        logger.info("Query executed and result are fetched successfully")
        mapped_data=data.mappings().all()
        data_framed=pd.DataFrame(data=mapped_data)
        csv_datafile=data_framed.to_csv(
            index=False,
            encoding="utf-8",
        )
        if data_framed.empty:
            return {
                "mysql_query":mysql_query,
                "data":[],
                "sample_data":json.dumps("No smaple data available"),
                "row_count":0,
                "business_metrics":"No specific business metrics were calculated for this request",
                "csv_file":str(csv_datafile)
            }
        
        required_columns={"sRole","sDesignation","sBilledHours","sAttendanceCapacityForWastage","sNps"} 
        target_phrases=["Utilization Internal", "Utilisation Client", "Capacity Billed Hour", "NPS Score"]
        # business_metrics_results:{}

        try:
            if required_columns.issubset(data_framed.columns) and any(phrase.upper() in user_query.upper() for phrase in target_phrases):
                logger.info("All required columns found. Calculating metrics...")
                capacity_billed_hours_results=get_capacity_billed_hours(data_framed_ip=data_framed, 
                                                                        user_query_ip=user_query
                                                                        )  
                NPS_rating_results=get_nps_score(data_framed_ip=data_framed)
                internal_utilization_results=get_internal_utilization(data_framed_ip=data_framed)
                logger.info("Business metrics calculated successfully")
                
                data_framed_json=data_framed.to_json(orient="records", date_format="iso")
                data_framed_dict=json.loads(data_framed_json)
                sample_data_sliced_dict=data_framed_dict[:10]
                sample_data_sliced_json=json.dumps(sample_data_sliced_dict)

                return {
                    "mysql_query":mysql_query,
                    "data":data_framed_dict,
                    "sample_data":sample_data_sliced_json,
                    "row_count":len(data_framed_dict),
                    "csv_file":str(csv_datafile),
                    "business_metrics":{
                    "Capacity_Billed_Hours":capacity_billed_hours_results,
                    "NPS_rating":NPS_rating_results,
                    "Internal_Utilization":internal_utilization_results
                }
                }
            
            else:
                data_framed_json=data_framed.to_json(orient="records", date_format="iso")
                data_framed_dict=json.loads(data_framed_json)
                sample_data_sliced_dict=data_framed_dict[:10]
                sample_data_sliced_json=json.dumps(sample_data_sliced_dict)
                return {
                    "mysql_query":mysql_query,
                    "data":data_framed_dict,
                    "sample_data":sample_data_sliced_json,
                    "row_count":len(data_framed_dict),
                    "csv_file":str(csv_datafile),
                    "business_metrics":"No specific business metrics were calculated for this request"
        }
        except Exception as e:
            logger.exception("Error in Metrics calculation or data conversion: %s",e)
            raise
        
    except Exception as e:
        logger.exception("Error in executing query against database: %s",e)
        raise


# chat_history:list[BaseMessage]

async def orchestrator(user_query:str, session:AsyncSession, chat_history:list[BaseMessage], chosen_db:str | None=None):
    """This function creates the flow of execution"""
    logger.info("----STARTING WORKFLOW----")
    fetched_conversational_prompt=get_conversational_prompt(chat_history=chat_history)
    fetched_conversation=await get_conversation(conversation_prompt=fetched_conversational_prompt)
    if fetched_conversation==1 or fetched_conversation== "1":
        fetched_table_schema=await get_table_schema(target_db=chosen_db)
        fetched_table_prompt=get_table_prompt(chat_history=chat_history,target_db=chosen_db,table_schema=fetched_table_schema)
        fetched_tables=await get_tables(tableprompt=fetched_table_prompt)
        if not fetched_tables:
            return {
                "mysql_query": None,
                "data200": None,
                "row_count": 0,
                "business_metrics": None,
                "csv_file": " ",
                "ai_msg": "It looks like you haven't uploaded any files yet. Please upload an Excel or CSV file to start chatting with your data!"
            }
        fetched_db_schema=await get_db_schema(table_names=fetched_tables, target_db=chosen_db)
        fetched_query_prompt=get_query_prompt(chat_history=chat_history, db_schema=fetched_db_schema, target_db=chosen_db)
        fetched_query=await get_query(queryprompt=fetched_query_prompt)
        validated_sql=query_validation(mysql_query=fetched_query)
        data=await get_data_formatted(user_query=user_query, session=session, mysql_query=validated_sql)
        summary_promptvalue=get_final_sumarizer_prompt(business_metrics=data["business_metrics"], chat_history=chat_history, total_records=data["row_count"], sample_data=data["sample_data"])
        final_response2user=await get_final_summary(summary_prompt=summary_promptvalue)
        logger.info("----WORKFLOW EXECUTED SUCCESSFULLY----")
        result_fields={"mysql_query":data["mysql_query"],
                       "data200":data["data"][:200],
                       "row_count":data["row_count"],
                       "business_metrics":data["business_metrics"],
                       "csv_file":data["csv_file"],
                       "ai_msg":final_response2user}
        return result_fields 

    logger.info("----WORKFLOW EXECUTED SUCCESSFULLY----")
    result_fields={
        "mysql_query":None,
        "data200":None,
        "row_count":None,
        "business_metrics":None,
        "csv_file":" ",
        "ai_msg":fetched_conversation
        }
    return result_fields 




async def get_user_data_formatted(user_query:str, session:AsyncSession, mysql_query:str):
    """This function executes the query against the database and fetch results"""
    try:
        logger.info("Executing query against the database")
        data=await session.execute(text(mysql_query))
        logger.info("Query executed and result are fetched successfully")
        mapped_data=data.mappings().all()
        data_framed=pd.DataFrame(data=mapped_data)
        csv_datafile=data_framed.to_csv(
            index=False,
            encoding="utf-8",
        )
        if data_framed.empty:
            return {
                "mysql_query":mysql_query,
                "data":[],
                "sample_data":json.dumps("No smaple data available"),
                "row_count":0,
                "business_metrics":"No specific business metrics were calculated for this request",
                "csv_file":str(csv_datafile)
            }
        else:
            data_framed_json=data_framed.to_json(orient="records", date_format="iso")
            data_framed_dict=json.loads(data_framed_json)
            sample_data_sliced_dict=data_framed_dict[:10]
            sample_data_sliced_json=json.dumps(sample_data_sliced_dict)
            return {
                "mysql_query":mysql_query,
                "data":data_framed_dict,
                "sample_data":sample_data_sliced_json,
                "row_count":len(data_framed_dict),
                "business_metrics":"No specific business metrics were calculated for this request",
                "csv_file":str(csv_datafile)
            }
        
    except Exception as e:
        logger.exception("Error in executing query against database: %s",e)
        raise
        

async def uploads_orchestrator(user_query:str, user_id:int, session:AsyncSession, chat_history:list[BaseMessage], chosen_db:str, chat_id:str | None=None):
    """This function orchestrate for the user uploaded files"""
    try:
        logger.info("----STARTING WORKFLOW----")
        fetched_conversational_prompt=get_conversational_prompt(chat_history=chat_history)
        fetched_conversation=await get_conversation(conversation_prompt=fetched_conversational_prompt)
        if fetched_conversation==1 or fetched_conversation== "1":
            table_names=await get_uploads_tables(user_id=user_id, target_db=chosen_db, session=session, chat_id=chat_id)
            if not table_names:
                return {
                "mysql_query": None,
                "data200": None,
                "row_count": 0,
                "business_metrics": None,
                "csv_file": " ",
                "ai_msg": "It looks like you haven't uploaded any files yet. Please upload an Excel or CSV file to start chatting with your data!"
            }
            fetched_db_schema=await get_db_schema(table_names=table_names, target_db=chosen_db)
            fetched_query_prompt=get_query_prompt(chat_history=chat_history, db_schema=fetched_db_schema, target_db=chosen_db)
            fetched_query=await get_query(queryprompt=fetched_query_prompt)
            validated_sql=query_validation(mysql_query=fetched_query)
            data=await get_user_data_formatted(user_query=user_query, session=session, mysql_query=validated_sql)
            summary_promptvalue=get_final_sumarizer_prompt(business_metrics=data["business_metrics"], chat_history=chat_history, total_records=data["row_count"], sample_data=data["sample_data"])
            final_response2user=await get_final_summary(summary_prompt=summary_promptvalue)
            logger.info("----WORKFLOW EXECUTED SUCCESSFULLY----")
            result_fields={"mysql_query":data["mysql_query"],
                        "data200":data["data"][:200],
                        "row_count":data["row_count"],
                        "business_metrics":data["business_metrics"],
                        "csv_file":data["csv_file"],
                        "ai_msg":final_response2user}
            return result_fields 
        
        logger.info("----WORKFLOW EXECUTED SUCCESSFULLY----")
        result_fields={
            "mysql_query":None,
            "data200":None,
            "row_count":None,
            "business_metrics":None,
            "csv_file":" ",
            "ai_msg":fetched_conversation
            }
        
        return result_fields 
    
    except Exception as e:
        logger.exception("Error in the uploads workflow %s",e)
        raise

















# if __name__=="__main__":
#     async def main():
#         try:
#             async with AsyncSessionLocal() as session:
#                 i=1
#                 # for i in range(1,2):
#                     # print(f"EXECUTION ROUND {i}")
#                 while i:
#                     start_time=time.time()
#                     user_ip=input("USER:")
#                     if not user_ip.lower()=="exit":
#                         result=await orchestrator(
#                             # user_query="List all employees whose salary is greater than 15000",
#                             user_query=user_ip,
#                             session=session,
#                             chosen_db="enventure"
#                             )
#                         print("\n")
#                         print(result)
#                         print(f"Total_Time_Taken:{round((time.time()-start_time),3)}")
#                         print("\n")
#                     else:
#                         i=0       
#         except Exception as e:
#             print("Error Message:",e)
#         finally:
#             await engine.dispose()


    # asyncio.run(main())

# python -m backend.src.data_fetch.query_orchestration

#NORMAL DICT CONVERSIOn
"""
2026-02-25 20:22:32,200-logtalk2db-INFO-MainThread-:starting env variales configuration
2026-02-25 20:22:32,206-logtalk2db-INFO-MainThread-configured variables successfully
EXECUTION ROUND 1
2026-02-25 20:22:38,351-logtalk2db-INFO-MainThread-----STARTING WORKFLOW----
2026-02-25 20:22:38,351-logtalk2db-INFO-MainThread-Trigering functions to build table schema
2026-02-25 20:22:38,403-logtalk2db-INFO-MainThread-Table Schema built successfully
2026-02-25 20:22:38,403-logtalk2db-INFO-MainThread-Invoking table prompt
2026-02-25 20:22:38,504-logtalk2db-INFO-MainThread-Table Prompt ready, its now a prompt value
2026-02-25 20:22:38,504-logtalk2db-INFO-MainThread-Invoking tables generation model
2026-02-25 20:22:40,687-logtalk2db-INFO-MainThread-tables generation model provided response successfully
2026-02-25 20:22:40,689-logtalk2db-INFO-MainThread-Triggering functions to build db_schema
2026-02-25 20:22:40,727-logtalk2db-INFO-MainThread-db_schema built successfully
2026-02-25 20:22:40,727-logtalk2db-INFO-MainThread-Invoking query prompt
2026-02-25 20:22:40,731-logtalk2db-INFO-MainThread-Query prompt ready, It's now a prompt value
2026-02-25 20:22:40,731-logtalk2db-INFO-MainThread-Invoking query generation model
2026-02-25 20:22:42,459-logtalk2db-INFO-MainThread-query generation model provided response successfully
2026-02-25 20:22:42,459-logtalk2db-INFO-MainThread-SQL validation started
2026-02-25 20:22:42,459-logtalk2db-INFO-MainThread-SQL Query is validated SELECT * FROM hr.employees WHERE salary > 15000
2026-02-25 20:22:42,459-logtalk2db-INFO-MainThread-Executing query against the database
2026-02-25 20:22:42,463-logtalk2db-INFO-MainThread-Query executed and result are fetched successfully


2026-02-25 20:22:42,465-logtalk2db-INFO-MainThread-----WORKFLOW EXECUTED SUCCESSFULLY----
{'mysql_query': 'SELECT * FROM hr.employees WHERE salary > 15000', 'data': [{'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'SKING', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 'AD_PRES', 'salary': 24000.0, 'commission_pct': None, 'manager_id': None, 'department_id': 90}, {'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'NKOCHHAR', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 'AD_VP', 'salary': 17000.0, 'commission_pct': None, 'manager_id': 100, 'department_id': 90}, {'employee_id': 102, 'first_name': 'Lex', 'last_name': 'De Haan', 'email': 'LDEHAAN', 'phone_number': '515.123.4569', 'hire_date': '1993-01-13', 'job_id': 'AD_VP', 'salary': 17000.0, 'commission_pct': None, 'manager_id': 100, 'department_id': 90}], 'row_count': 3}
Total_Time_Taken:4.114


EXECUTION ROUND 2
2026-02-25 20:22:42,465-logtalk2db-INFO-MainThread-----STARTING WORKFLOW----
2026-02-25 20:22:42,465-logtalk2db-INFO-MainThread-Trigering functions to build table schema
2026-02-25 20:22:42,465-logtalk2db-INFO-MainThread-Invoking table prompt
2026-02-25 20:22:42,468-logtalk2db-INFO-MainThread-Table Prompt ready, its now a prompt value
2026-02-25 20:22:42,468-logtalk2db-INFO-MainThread-Invoking tables generation model
2026-02-25 20:22:44,059-logtalk2db-INFO-MainThread-tables generation model provided response successfully
2026-02-25 20:22:44,061-logtalk2db-INFO-MainThread-Triggering functions to build db_schema
2026-02-25 20:22:44,071-logtalk2db-INFO-MainThread-db_schema built successfully
2026-02-25 20:22:44,071-logtalk2db-INFO-MainThread-Invoking query prompt
2026-02-25 20:22:44,073-logtalk2db-INFO-MainThread-Query prompt ready, It's now a prompt value
2026-02-25 20:22:44,073-logtalk2db-INFO-MainThread-Invoking query generation model
2026-02-25 20:22:45,649-logtalk2db-INFO-MainThread-query generation model provided response successfully
2026-02-25 20:22:45,649-logtalk2db-INFO-MainThread-SQL validation started
2026-02-25 20:22:45,651-logtalk2db-INFO-MainThread-SQL Query is validated SELECT * FROM hr.employees WHERE salary > 15000
2026-02-25 20:22:45,651-logtalk2db-INFO-MainThread-Executing query against the database
2026-02-25 20:22:45,653-logtalk2db-INFO-MainThread-Query executed and result are fetched successfully


2026-02-25 20:22:45,655-logtalk2db-INFO-MainThread-----WORKFLOW EXECUTED SUCCESSFULLY----
{'mysql_query': 'SELECT * FROM hr.employees WHERE salary > 15000', 'data': [{'employee_id': 100, 'first_name': 'Steven', 'last_name': 'King', 'email': 'SKING', 'phone_number': '515.123.4567', 'hire_date': '1987-06-17', 'job_id': 'AD_PRES', 'salary': 24000.0, 'commission_pct': None, 'manager_id': None, 'department_id': 90}, {'employee_id': 101, 'first_name': 'Neena', 'last_name': 'Kochhar', 'email': 'NKOCHHAR', 'phone_number': '515.123.4568', 'hire_date': '1989-09-21', 'job_id': 'AD_VP', 'salary': 17000.0, 'commission_pct': None, 'manager_id': 100, 'department_id': 90}, {'employee_id': 102, 'first_name': 'Lex', 'last_name': 'De Haan', 'email': 'LDEHAAN', 'phone_number': '515.123.4569', 'hire_date': '1993-01-13', 'job_id': 'AD_VP', 'salary': 17000.0, 'commission_pct': None, 'manager_id': 100, 'department_id': 90}], 'row_count': 3}
Total_Time_Taken:3.19


"""
#USING PANDAS + Additional check 
"""
2026-04-05 13:41:00,098-logtalk2db-INFO-MainThread-:starting env variales configuration
2026-04-05 13:41:00,105-logtalk2db-INFO-MainThread-configured variables successfully
EXECUTION ROUND 1
2026-04-05 13:41:06,543-logtalk2db-INFO-MainThread-----STARTING WORKFLOW----
2026-04-05 13:41:06,543-logtalk2db-INFO-MainThread-Trigering functions to build table schema
2026-04-05 13:41:06,610-logtalk2db-INFO-MainThread-Table Schema built successfully
2026-04-05 13:41:06,612-logtalk2db-INFO-MainThread-Invoking table prompt
2026-04-05 13:41:06,631-logtalk2db-INFO-MainThread-Table Prompt ready, its now a prompt value
2026-04-05 13:41:06,631-logtalk2db-INFO-MainThread-Invoking tables generation model
2026-04-05 13:41:09,974-logtalk2db-INFO-MainThread-tables generation model provided response successfully
2026-04-05 13:41:09,974-logtalk2db-INFO-MainThread-Triggering functions to build db_schema
2026-04-05 13:41:09,993-logtalk2db-INFO-MainThread-db_schema built successfully
2026-04-05 13:41:09,994-logtalk2db-INFO-MainThread-Invoking query prompt
2026-04-05 13:41:09,994-logtalk2db-INFO-MainThread-Query prompt ready, It's now a prompt value
2026-04-05 13:41:09,994-logtalk2db-INFO-MainThread-Invoking query generation model
2026-04-05 13:41:11,406-logtalk2db-INFO-MainThread-query generation model provided response successfully
2026-04-05 13:41:11,406-logtalk2db-INFO-MainThread-SQL validation started
2026-04-05 13:41:11,409-logtalk2db-INFO-MainThread-SQL Query is validated SELECT * FROM hr.employees WHERE salary > 15000
2026-04-05 13:41:11,409-logtalk2db-INFO-MainThread-Executing query against the database
2026-04-05 13:41:11,409-logtalk2db-INFO-MainThread-Query executed and result are fetched successfully


2026-04-05 13:41:11,415-logtalk2db-INFO-MainThread-----WORKFLOW EXECUTED SUCCESSFULLY----
{'mysql_query': 'SELECT * FROM hr.employees WHERE salary > 15000', 'data': [{'commission_pct': None, 'department_id': 90, 'email': 'SKING', 'employee_id': 100, 'first_name': 'Steven', 'hire_date': '1987-06-17T00:00:00.000', 'job_id': 'AD_PRES', 'last_name': 'King', 'manager_id': None, 'phone_number': '515.123.4567', 'salary': 24000.0}, {'commission_pct': None, 'department_id': 90, 'email': 'NKOCHHAR', 'employee_id': 101, 'first_name': 'Neena', 'hire_date': '1989-09-21T00:00:00.000', 'job_id': 'AD_VP', 'last_name': 'Kochhar', 'manager_id': 100.0, 'phone_number': '515.123.4568', 'salary': 17000.0}, {'commission_pct': None, 'department_id': 90, 'email': 'LDEHAAN', 'employee_id': 102, 'first_name': 'Lex', 'hire_date': '1993-01-13T00:00:00.000', 'job_id': 'AD_VP', 'last_name': 'De Haan', 'manager_id': 100.0, 'phone_number': '515.123.4569', 'salary': 17000.0}], 'row_count': 3}
Total_Time_Taken:4.876


EXECUTION ROUND 2
2026-04-05 13:41:11,419-logtalk2db-INFO-MainThread-----STARTING WORKFLOW----
2026-04-05 13:41:11,419-logtalk2db-INFO-MainThread-Trigering functions to build table schema
2026-04-05 13:41:11,419-logtalk2db-INFO-MainThread-Invoking table prompt
2026-04-05 13:41:11,419-logtalk2db-INFO-MainThread-Table Prompt ready, its now a prompt value
2026-04-05 13:41:11,419-logtalk2db-INFO-MainThread-Invoking tables generation model
2026-04-05 13:41:13,116-logtalk2db-INFO-MainThread-tables generation model provided response successfully
2026-04-05 13:41:13,116-logtalk2db-INFO-MainThread-Triggering functions to build db_schema
2026-04-05 13:41:13,123-logtalk2db-INFO-MainThread-db_schema built successfully
2026-04-05 13:41:13,129-logtalk2db-INFO-MainThread-Invoking query prompt
2026-04-05 13:41:13,129-logtalk2db-INFO-MainThread-Query prompt ready, It's now a prompt value
2026-04-05 13:41:13,129-logtalk2db-INFO-MainThread-Invoking query generation model
2026-04-05 13:41:14,711-logtalk2db-INFO-MainThread-query generation model provided response successfully
2026-04-05 13:41:14,711-logtalk2db-INFO-MainThread-SQL validation started
2026-04-05 13:41:14,711-logtalk2db-INFO-MainThread-SQL Query is validated SELECT * FROM hr.employees WHERE salary > 15000
2026-04-05 13:41:14,711-logtalk2db-INFO-MainThread-Executing query against the database
2026-04-05 13:41:14,716-logtalk2db-INFO-MainThread-Query executed and result are fetched successfully


2026-04-05 13:41:14,719-logtalk2db-INFO-MainThread-----WORKFLOW EXECUTED SUCCESSFULLY----
{'mysql_query': 'SELECT * FROM hr.employees WHERE salary > 15000', 'data': [{'commission_pct': None, 'department_id': 90, 'email': 'SKING', 'employee_id': 100, 'first_name': 'Steven', 'hire_date': '1987-06-17T00:00:00.000', 'job_id': 'AD_PRES', 'last_name': 'King', 'manager_id': None, 'phone_number': '515.123.4567', 'salary': 24000.0}, {'commission_pct': None, 'department_id': 90, 'email': 'NKOCHHAR', 'employee_id': 101, 'first_name': 'Neena', 'hire_date': '1989-09-21T00:00:00.000', 'job_id': 'AD_VP', 'last_name': 'Kochhar', 'manager_id': 100.0, 'phone_number': '515.123.4568', 'salary': 17000.0}, {'commission_pct': None, 'department_id': 90, 'email': 'LDEHAAN', 'employee_id': 102, 'first_name': 'Lex', 'hire_date': '1993-01-13T00:00:00.000', 'job_id': 'AD_VP', 'last_name': 'De Haan', 'manager_id': 100.0, 'phone_number': '515.123.4569', 'salary': 17000.0}], 'row_count': 3}
Total_Time_Taken:3.303
"""

#chatbot
# python -m backend.src.data_fetch.query_orchestration

if __name__=="__main__":
    async def main(target_db:str):
        chat_history:list[BaseMessage]=[]
        i=1
        while i:
            try:
                user_que=input("user:")
                if not user_que.upper()=="EXIT":
                    hm=HumanMessage(content=user_que)
                    chat_history.append(hm)
                    async with AsyncSessionLocal() as session:
                        result=await orchestrator(user_query=user_que, session=session, chosen_db=target_db, chat_history=chat_history)
                        print("AI:",result["ai_msg"])
                        chat_history.append(AIMessage(content=result["ai_msg"]))
                else:
                    print("Thank you! Happy to assist you")
                    print(chat_history)
                    i=0
            except Exception as e:
                print("Chat_history:",chat_history, e,sep="\n")
                raise


    asyncio.run(main(target_db="enventure"))
    
                

    
        
