from pydantic import BaseModel, Field
from typing import Annotated, List, Dict, Literal
from backend.src.core.config import configured_attributes
from langchain_core.messages import BaseMessage


class UserInputValidation(BaseModel):
    user_query:Annotated[str, Field(..., examples=["Who are the top 5 highest paid employees?"], min_length=1, max_length=500, description="question to ask the database")]
    database:Annotated[str, Field(default=configured_attributes().DB_NAME, description="The target database schema to query")]
    chat_history:Annotated[List[Dict[str, str]], Field(..., description="This chat history contains conversation between user and AI over a database as a primary purpose")]

class ChatHistoryInputValidation(BaseModel):
    user_id:Annotated[int, Field(..., description="Id to recognise the user")]
    session_id:Annotated[str, Field(..., description="Auto-generatedid to determine the session")]
    
class ChatInsertInputValidation(BaseModel):
    user_id:Annotated[int, Field(..., description="Id to recognise the user")]
    session_id:Annotated[str, Field(..., description="Auto-generatedid to determine the session")]
    chat_name:Annotated[str, Field(..., description="Name of the chat given by the user")]
    role:Annotated[Literal["user","assistant"], Field(...)]
    message:Annotated[str, Field(..., description="User message")]
    
