"""
Database Configuration and Session Management
Handles database connection, session creation, and schema initialization
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import os

# Database URL - SQLite for simplicity, easily migratable to PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./banking_system.db")

# Create async engine for SQLite
# Using StaticPool for SQLite to handle concurrent access properly
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries for debugging
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """
    Initialize database schema
    Creates all tables if they don't exist
    """
    from src.models.base import Base
    from src.models.account import Account
    from src.models.transaction_log import TransactionLog
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """
    Dependency for FastAPI to get database session
    Ensures proper transaction management and cleanup
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

