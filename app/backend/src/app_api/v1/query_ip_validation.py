from pydantic import BaseModel, Field
from typing import Annotated, List, Dict, Literal, Any
from backend.src.core.config import configured_attributes
from langchain_core.messages import BaseMessage


class UserInputValidation(BaseModel):
    user_query:Annotated[str, Field(..., examples=["Who are the top 5 highest paid employees?"], min_length=1, max_length=500, description="question to ask the database")]
    user_id:Annotated[int, Field(..., examples=[5458, 5641], description="User id of the user")]
    chat_id:Annotated[str, Field(..., description="Chat id for uploaded-file/created chat tab")]
    database:Annotated[str, Field(..., description="The target database schema to query")]
    chat_history:Annotated[List[Dict[str, str]], Field(..., description="This chat history contains conversation between user and AI over a database")]


class ChatHistoryInputValidation(BaseModel):
    user_id:Annotated[int, Field(..., description="Id to recognise the user")]
    chat_id:Annotated[str, Field(..., description="Auto-generatedid to determine the session")]
    
class ChatInsertInputValidation(BaseModel):
    user_id:Annotated[int, Field(..., description="Id to recognise the user")]
    chat_id:Annotated[str, Field(..., description="Auto-generatedid to determine the session")]
    chat_name:Annotated[str, Field(..., description="Name of the chat given by the user")]
    database:Annotated[str, Field(..., description="Name of the database that user has chosen to interact with")]
    role:Annotated[Literal["user","assistant"], Field(...)]
    message:Annotated[str, Field(..., description="User message")]
    sql_query:Annotated[str, Field(default="null", description="MYSQL query generated to answer user query")]

class UserFileUploadInputValidation(BaseModel):
    file_bytes: Annotated[bytes, Field(..., description="Raw bytes of the uploaded file")]
    file_type: Literal["csv", "xlsx"]
    table_name: Annotated[str, Field(..., description="table name required to create table")]
