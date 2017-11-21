import os
import sqlalchemy_utils
import pytest
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope='session')
def db_uri():
    host = os.environ.get('DB_HOST', 'postgres')
    port = os.environ.get('DB_PORT', 5432)
    username = os.environ.get('DB_USER', 'postgres')
    password = os.environ.get('DB_PASS', 'postgres')
    name = os.environ.get('DB_NAME', 'test_auth_lib')

    return 'postgresql://{username}:{password}@{host}:{port}/{name}'.format(
        host=host,
        port=port,
        username=username,
        password=password,
        name=name
    )


@pytest.fixture(scope='session')
def test_database(db_uri):
    sqlalchemy_utils.create_database(db_uri)
    yield create_engine(db_uri)
    sqlalchemy_utils.drop_database(db_uri)


@pytest.fixture(scope='session')
def db_connection(test_database):
    with test_database.connect() as connection:
        transaction = connection.begin()
        yield connection
        transaction.rollback()


@pytest.fixture
def metadata(db_connection):
    meta = MetaData(bind=db_connection)
    yield meta
    meta.drop_all()


@pytest.fixture
def base(metadata):
    return declarative_base(metadata=metadata)


@pytest.fixture
def db_session(db_connection):
    session = sessionmaker(bind=db_connection)()
    yield session
    session.close()
