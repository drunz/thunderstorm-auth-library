from datetime import datetime, timedelta

import jwt
import pytest


@pytest.fixture(scope='session')
def secret_key():
    return 'bacon'


@pytest.fixture
def valid_token(secret_key):
    return jwt.encode(
        {
            'data': {'more': 123}
        },
        secret_key
    )


@pytest.fixture
def invalid_token(valid_token):
    return valid_token[:-5]


@pytest.fixture
def expired_token(secret_key):
    return jwt.encode(
        {
            'data': {'more': 123},
            'exp': datetime.utcnow() - timedelta(hours=1)
        },
        secret_key
    )
