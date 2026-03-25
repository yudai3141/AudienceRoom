import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.db.base import Base
import app.db.models  # noqa: F401

engine = create_engine(settings.DATABASE_URL, echo=False)


@pytest.fixture()
def db() -> Session:
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
