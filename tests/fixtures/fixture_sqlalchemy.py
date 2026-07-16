import pytest
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from infrastructure.orm.base import Base


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def sqlalchemy_engine(postgres_container: PostgresContainer):
    row_url = postgres_container.get_connection_url()

    db_url = row_url.replace("+psycopg2", "+psycopg")

    engine = create_engine(db_url)

    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(sqlalchemy_engine: Engine):
    SessionTesting = sessionmaker(bind=sqlalchemy_engine)
    session = SessionTesting()

    yield session
    session.close()

    with sqlalchemy_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE staffs RESTART IDENTITY CASCADE"))
