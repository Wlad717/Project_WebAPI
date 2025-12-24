from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./currency.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session