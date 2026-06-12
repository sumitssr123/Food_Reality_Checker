from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Local Database File URL
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./healthy_india.db"

# Creating an asynchronous engine for high performance
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False 
)

# Session factory for handling database transactions
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Dependency to get the DB session in FastAPI
async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()