# db/session.py
from config.bot_config import SQLALCHEMY_URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(SQLALCHEMY_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
