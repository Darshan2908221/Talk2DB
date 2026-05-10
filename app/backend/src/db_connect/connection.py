from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.src.core.config import configured_attributes 
from backend.src.utils.app_logger import logger
import asyncio

#engine creation i.e connecting to mysql database
engine=create_async_engine(
    url=configured_attributes().db_url,
    pool_size=20,
    max_overflow=10,
    pool_timeout=10,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

AsyncSessionLocal=async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Providing session connection")
            yield session
            logger.info("Session connection received back successfully")
        except Exception as e:
            logger.exception("Error Message: %s",e)
            raise

#Engine creation i.e to sqllite database



if __name__=="__main__":
    async def main():
        """This function is to test the engine and session connection"""
        try:
            logger.info("Launching engine unit test")
            async with engine.connect() as conn:
                logger.info("Engine connected successfully: %s",conn)
            try:
                logger.info("Launching session creation checks")
                async with AsyncSessionLocal() as session:
                    logger.info("Session received successfully: %s",session)
            except Exception as e:
                logger.exception("Error, Failed to get session: %s",e)
                raise
        except Exception as e:
            logger.exception("Error while connecting to engine: %s",e)
            raise
        finally:
            await engine.dispose()

    asyncio.run(main())


# python -m backend.src.db_connect.connection