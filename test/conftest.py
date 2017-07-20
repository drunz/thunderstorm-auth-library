from datetime import datetime, timedelta
from flask import Flask
import jwt
import pytest

from thunderstorm_auth.auth import ts_auth_required


@pytest.fixture(scope='session')
def secret_key():
    return 'bacon'


@pytest.fixture(scope='function')
def valid_token(secret_key):
    return jwt.encode({'data': {'more': 123}}, secret_key)


@pytest.fixture(scope='function')
def invalid_token(valid_token):
    return valid_token[:-5]


@pytest.fixture(scope='function')
def expired_token(secret_key):
    return jwt.encode({'data': {'more': 123}, 'exp': datetime.utcnow() - timedelta(hours=1)}, secret_key)


@pytest.fixture(scope='function')
def flask_app(secret_key):
    app = Flask('test_app')
    app.config['TS_AUTH_SECRET_KEY'] = secret_key

    @app.route('/')
    @ts_auth_required
    def hello_world():
        return 'Hello, World!'

    return app
