from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,      # 👈 async session
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # 👈 avoids lazy-load errors after commit
    
)

Base = declarative_base()

async def get_db():            # 👈 must be async
    async with SessionLocal() as session:
        yield session