from pydantic import BaseModel, Field
from typing import Annotated
from backend.src.core.config import configured_attributes

class UserInputValidation(BaseModel):
    user_query:Annotated[str, Field(..., examples=["Who are the top 5 highest paid employees?"], min_length=5, max_length=500, description="question to ask the database")]
    database:Annotated[str, Field(default=configured_attributes().DB_NAME, description="The target database schema to query")]
