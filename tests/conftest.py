import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
import app.database
from app.main import app as fastapi_app
import os
os.environ["CELERY_ALWAYS_EAGER"] = "True"

# Переопределяем БД на SQLite для тестов
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Глобально подменяем сессии в модуле app.database
app.database.engine = test_engine
app.database.SessionLocal = TestSessionLocal

def override_get_db():
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
