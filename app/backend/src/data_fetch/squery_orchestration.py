#This module orchestrate the flow
#Flow
"""
Top level=>
userquery=>get_table_schema=>get_table_prompt=>get_tables=>=>get_db_schema=>get_query_prompt=>get_query=>query_validation=>get_data=>Summary of data
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.src.utils.app_logger import logger
from backend.src.data_fetch.prompts import get_table_prompt, get_query_prompt, get_conversational_prompt, get_final_sumarizer_prompt
from backend.src.data_fetch.db_schema import get_table_schema, get_db_schema
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

async def sorchestrator(user_query:str, table_names:list[str], session:Session, chat_history:list[BaseMessage], chosen_db:str | None=None):
    """This function creates the flow of execution"""
    logger.info("----STARTING WORKFLOW----")
    fetched_conversational_prompt=get_conversational_prompt(chat_history=chat_history)
    fetched_conversation=await get_conversation(conversation_prompt=fetched_conversational_prompt)
    if fetched_conversation==1 or fetched_conversation== "1":
        fetched_db_schema=await get_db_schema(table_names=table_names, target_db=chosen_db)
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
    result_fields={"mysql_query":None,
                       "data200":None,
                       "row_count":None,
                       "business_metrics":None,
                       "csv_file":" ",
                       "ai_msg":fetched_conversation}
    return result_fields 
