#This module provides the LLM models to interact with
from langchain_ollama import ChatOllama
from backend.src.utils.app_logger import logger
from backend.src.data_fetch.prompts import SchemaFiltrationModel, QueryModel
from backend.src.core.config import configured_attributes
from langchain_google_genai import ChatGoogleGenerativeAI


# "sqlcoder-7b"
model=ChatOllama(
    model=configured_attributes().MODEL_NAME,
    keep_alive="2m",
    temperature=0.1,
    top_p=0.9,
    num_predict=500
)

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
table_generation_model=genai_model.with_structured_output(schema=SchemaFiltrationModel)
query_generation_model=genai_model.with_structured_output(schema=QueryModel)

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
    

#to unload from ram
"""
curl http://localhost:11434/api/generate -d '{
  "model": "sqlcoder-7b",
  "prompt": "",
  "keep_alive": 0
}'
"""
# ollama rm sqlcoder-7b (To remove model from machine not just ram)

# python -m backend.src.data_fetch.query_orchestration