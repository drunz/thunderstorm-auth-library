from datetime import timedelta
import functools
from os import environ
from unittest.mock import patch

from factory.alchemy import SQLAlchemyModelFactory
import flask
import jwt.algorithms
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import sqlalchemy_utils as sa_utils

from thunderstorm_auth import utils
from thunderstorm_auth.datastore import SQLAlchemySessionAuthStore
from thunderstorm_auth.exceptions import HTTPError
from thunderstorm_auth.flask import ts_auth_required, init_ts_auth
from thunderstorm_auth.roles import _init_role_tasks

from test import models
import test.fixtures


@pytest.fixture
def private_key():
    return utils.generate_private_key()


@pytest.fixture
def jwk(private_key):
    return utils.generate_jwk(private_key)


@pytest.fixture
def key_id(jwk):
    return utils.generate_key_id(jwk)


@pytest.fixture
def alternate_private_key():
    return utils.generate_private_key()


@pytest.fixture
def alternate_jwk(alternate_private_key):
    return utils.generate_jwk(alternate_private_key)


@pytest.fixture
def alternate_key_id(alternate_jwk):
    return utils.generate_key_id(alternate_jwk)


@pytest.fixture
def jwk_set(jwk, key_id, alternate_jwk, alternate_key_id):
    return {'keys': {key_id: jwk, alternate_key_id: alternate_jwk}}


@pytest.fixture
def access_token_payload():
    return {'username': 'test-user', 'token_type': 'access', 'groups': [], 'roles': [], 'permissions': {}}


@pytest.fixture
def refresh_token_payload():
    return {
        'username': 'test-user',
        'token_type': 'refresh',
    }


@pytest.fixture
def make_token(private_key, key_id):
    """Returns a partial object for creating a token.
        Callers can then specify their desired payload or lifetime when
        calling the returned object. If no lifetime is specified it defaults
        to 15 minutes.
    """
    return functools.partial(utils.encode_token, private_key, key_id)


@pytest.fixture
def access_token(make_token, access_token_payload):
    return make_token(access_token_payload)


@pytest.fixture
def access_token_with_permissions(make_token, access_token_payload):
    access_token_payload['permissions'] = {
        # service name needs to match the service name defined in flask_app fixture
        'test-service': ['perm-a', 'basic']
    }
    return make_token(access_token_payload)


@pytest.fixture
def access_token_with_permissions_wrong_service(make_token, access_token_payload):
    access_token_payload['permissions'] = {'other-service': ['perm-a']}
    return make_token(access_token_payload)


@pytest.fixture
def access_token_expired(make_token, access_token_payload):
    access_token_payload['permissions'] = {
        # service name needs to match the service name defined in flask_app fixture
        'test-service': ['perm-a', 'basic']
    }
    lifetime = timedelta(hours=-1)
    return make_token(access_token_payload, lifetime=lifetime)


@pytest.fixture
def access_token_expired_with_permissions(make_token, access_token_payload):
    lifetime = timedelta(hours=-1)
    access_token_payload['permissions'] = {'test-service': ['perm-a']}
    return make_token(access_token_payload, lifetime=lifetime)


@pytest.fixture
def refresh_token(make_token, refresh_token_payload):
    return make_token(refresh_token_payload)


@pytest.fixture
def token_signed_with_incorrect_key(key_id, access_token_payload, alternate_private_key):
    """ Return a token signed with a key that does not match the KID specified
    """
    return utils.encode_token(
        # token should have been signed with private_key
        alternate_private_key,
        key_id,
        access_token_payload
    )


@pytest.fixture
def malformed_token():
    # using a junk string here rather than a truncated token as truncated
    # tokens do not trigger the desired error
    return 'this is not even a token'


@pytest.fixture
def token_with_no_headers(private_key):
    return jwt.encode({'data': 'nodata'}, private_key, algorithm='RS512')


@pytest.fixture
def flask_app(datastore, jwk_set):
    app = flask.Flask('test_app')

    app.config['TS_AUTH_JWKS'] = jwk_set
    app.config['TS_SERVICE_NAME'] = 'test-service'

    # patch load_jwks_from_file
    with patch('thunderstorm_auth.flask.core.load_jwks_from_file', return_value=jwk_set):
        app.ts_auth = init_ts_auth(app, datastore)

    @app.route('/')
    @ts_auth_required(with_permission='basic')
    def hello_world():
        return 'Hello, World!'

    @app.route('/no-params')
    @ts_auth_required(with_permission='basic')
    def no_params():
        return 'no params'

    @app.route('/perm-a')
    @ts_auth_required(with_permission='perm-a')
    def with_perm_a():
        return 'with perm a'

    @app.errorhandler(HTTPError)
    def handle_invalid_usage(exc):
        data = {'code': exc.code, 'message': exc.message}

        return flask.jsonify(data), data['code']

    with app.app_context():
        yield app


@pytest.fixture
def role_tasks(db_session):
    datastore = SQLAlchemySessionAuthStore(
        db_session, models.Role, models.Permission, models.RolePermissionAssociation
    )
    # initialize only once the tasks, return a mapping task name: task
    return {t.name: t for t in _init_role_tasks(datastore)}


@pytest.fixture(scope='function')
def datastore(db_session):
    return SQLAlchemySessionAuthStore(db_session, models.Role, models.Permission, models.RolePermissionAssociation)


@pytest.fixture
def celery(celery_app, datastore):
    _init_role_tasks(datastore)
    return celery_app


#############################################################
# DB FIXTURES
#############################################################


@pytest.fixture(scope='session')
def db_uri():
    db_name = environ['DB_NAME']
    db_host = environ['DB_HOST']
    db_user = environ['DB_USER']
    db_pass = environ['DB_PASS']
    return 'postgresql://{}:{}@{}:5432/{}'.format(db_user, db_pass, db_host, db_name)


@pytest.fixture(scope='session')
def test_database(db_uri):
    if sa_utils.database_exists(db_uri):
        sa_utils.drop_database(db_uri)

    sa_utils.create_database(db_uri)

    engine = create_engine(db_uri)
    models.Base.metadata.create_all(engine)

    return engine


@pytest.fixture
def db_connection(test_database):
    with test_database.connect() as connection:
        transaction = connection.begin()
        yield connection
        transaction.rollback()


@pytest.fixture
def db_session(db_connection):
    session = scoped_session(sessionmaker(bind=db_connection))
    yield session
    session.close()


@pytest.fixture
def fixtures(db_session):
    for item in dir(test.fixtures):
        item = getattr(test.fixtures, item)
        if isinstance(item, type) and issubclass(item, SQLAlchemyModelFactory):
            item._meta.sqlalchemy_session = db_session

    return test.fixtures
