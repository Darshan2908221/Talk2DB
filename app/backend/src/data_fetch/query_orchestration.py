#This module orchestrate the flow
#Flow
"""
Top level=>
userquery=>get_table_schema=>get_table_prompt=>get_tables=>=>get_db_schema=>get_query_prompt=>get_query=>query_validation=>get_data=>prepare data
"""
from sqlalchemy import text
from backend.src.utils.app_logger import logger
from backend.src.db_connect.connection import AsyncSessionLocal, engine
from backend.src.data_fetch.prompts import get_table_prompt, get_query_prompt
from backend.src.data_fetch.db_schema import get_table_schema, get_db_schema
from backend.src.data_fetch.llms import get_tables, get_query
from backend.src.data_fetch.sql_guard import query_validation
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import datetime, date
import asyncio
import time

async def get_data_formatted(session:AsyncSession, mysql_query:str):
    """This function executes the query against the database and fetch results"""
    try:
        logger.info("Executing query against the database")
        data=await session.execute(text(mysql_query))
        logger.info("Query executed and result are fetched successfully")
        mapped_data=data.mappings().all()
        data_rows=[]
        for row in mapped_data:
            clean_rows:dict={}
            for key, value in row.items():
                if isinstance(value,Decimal):
                    clean_rows[key]=float(value)
                elif isinstance(value, (datetime, date)):
                    clean_rows[key]=value.isoformat()
                else:
                    clean_rows[key]=value
            data_rows.append(clean_rows)
        return {
            "mysql_query":mysql_query,
            "data":data_rows,
            "row_count":len(data_rows)
        }
    except Exception as e:
        logger.exception("Error in executing query against database: %s",e)
        raise
    finally:
        await session.close()

async def orchestrator(user_query:str , session:AsyncSession, chosen_db:str | None=None):
    """This function creates the flow of execution"""
    logger.info("----STARTING WORKFLOW----")
    fetched_table_schema=await get_table_schema(target_db=chosen_db)
    fetched_table_prompt=get_table_prompt(user_query=user_query,target_db=chosen_db,table_schema=fetched_table_schema)
    fetched_tables=await get_tables(tableprompt=fetched_table_prompt)
    fetched_db_schema=await get_db_schema(table_names=fetched_tables, target_db=chosen_db)
    fetched_query_prompt=get_query_prompt(user_query=user_query, db_schema=fetched_db_schema, target_db=chosen_db)
    fetched_query=await get_query(queryprompt=fetched_query_prompt)
    validated_sql=query_validation(mysql_query=fetched_query)
    data=await get_data_formatted(session=session,mysql_query=validated_sql)
    logger.info("----WORKFLOW EXECUTED SUCCESSFULLY----")
    return data

if __name__=="__main__":
    async def main():
        try:
            async with AsyncSessionLocal() as session:
                for i in range(1,3):
                    print(f"EXECUTION ROUND {i}")
                    start_time=time.time()
                    result=await orchestrator(
                        user_query="List all employees whose salary is greater than 15000",
                        session=session,
                        chosen_db="hr"
                        )
                    print("\n")
                    print(result)
                    print(f"Total_Time_Taken:{round((time.time()-start_time),3)}")
                    print("\n")
        except Exception as e:
            print("Error Message:",e)
        finally:
            await engine.dispose()

    
    asyncio.run(main())

# python -m backend.src.data_fetch.query_orchestration
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


