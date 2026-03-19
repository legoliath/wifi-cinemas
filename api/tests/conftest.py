import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from jose import jwt
from datetime import datetime, timedelta, timezone
import uuid

from app.main import app
from app.database import Base, get_db
from app.config import settings

# SQLite async for tests (no PostgreSQL needed)
TEST_DB_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with test_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with test_session() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_token(user_id: str, role: str = "user") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": expire},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession):
    from app.models.user import User
    user = User(
        id=uuid.uuid4(),
        email="admin@wificinemas.com",
        name="Admin",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(admin_user):
    return make_token(str(admin_user.id), "admin")


@pytest_asyncio.fixture
async def regular_user(db: AsyncSession):
    from app.models.user import User
    user = User(
        id=uuid.uuid4(),
        email="crew@wificinemas.com",
        name="Crew Member",
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_token(regular_user):
    return make_token(str(regular_user.id), "user")
