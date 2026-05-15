#This Module configure the env variables
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, computed_field
from typing import Annotated, ClassVar
from pathlib import Path
from sqlalchemy import URL
from functools import lru_cache
from backend.src.utils.app_logger import logger

class Settings(BaseSettings):
    """Class to configure env variables"""
    DB_HOST:Annotated[str, Field(..., title="DB_Host", description="The host address of the database")]
    DB_PORT:Annotated[int, Field(...,title="DB_PORT",description="The exact location, where our Dialect(mysql) is hosted", gt=0, le=65535)]
    DB_USERNAME:Annotated[str,Field(..., title="DB_USERNAME",description="The user who has permission to access database")]
    DB_PASSWORD:Annotated[SecretStr,Field(..., title="DB_PASSWORD",description="The password required to login to Dialect(mysql) software")]
    DB_DRIVER:Annotated[str, Field(...,title="DRIVER_NAME",description="Driver who takes query to the mysql software and get database response back")]
    DB_DIALECT:Annotated[str, Field(...,title="DIALECT_NAME",description="Dialect who is responsible for creating syntatically correct Dialect(mysql) query")]
    JWT_SECRET_KEY:Annotated[SecretStr,Field(..., title="Secret Key", description="The secret key to manage session")]
    DB_NAME:Annotated[str,Field(default="hr",title="DB_NAME",description="Default database to interact")]
    MODEL_NAME:Annotated[str,Field(default="sqlcoder-7b", title="LLM", description="Default model to use to generate query")]
    GEMINI_API_KEY:Annotated[SecretStr,Field(..., title="API_key", description="API key to Interact with Gemini Models")]

    module_path:ClassVar[Path]=Path(__file__).resolve()
    root_path:ClassVar[Path]=module_path.parent.parent.parent.parent.parent
    env_path:ClassVar[Path]=root_path/".env"
    model_config=SettingsConfigDict(env_file=env_path, env_file_encoding="utf-8", extra="ignore")

    @computed_field
    @property
    def db_url(self)->URL:
        """This function creates the db_url to connect to database"""
        db_url=URL.create(
            drivername=f"{self.DB_DIALECT}+{self.DB_DRIVER}",
            host=self.DB_HOST,
            port=self.DB_PORT,
            username=self.DB_USERNAME,
            password=self.DB_PASSWORD.get_secret_value(),
        )
        return db_url
    
@lru_cache(maxsize=2)
def configured_attributes()->URL:
    # print("checking url cache status")
    logger.info(":starting env variales configuration")
    try:
        settings=Settings()
        logger.info("configured variables successfully")
        return settings
    except Exception as e:
        logger.exception("Error Message: %s",e)
        raise 

if __name__=="__main__":
    for i in range(2):
        settings=configured_attributes()
        print(settings.db_url) 
        '''
        checking url cache status
        mysql+aiomysql://root:***@localhost:3306
        mysql+aiomysql://root:***@localhost:3306
        '''

# python -m backend.src.core.config