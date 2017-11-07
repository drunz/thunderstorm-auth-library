from datetime import datetime, timedelta

import jwt.algorithms
import pytest

from thunderstorm_auth import utils


@pytest.fixture
def private_key():
    return utils.generate_private_key()


@pytest.fixture
def jwk(private_key):
    return utils.generate_jwk_string(private_key)


@pytest.fixture
def key_id(jwk):
    return utils.generate_key_id(jwk)


@pytest.fixture
def alternate_private_key():
    return utils.generate_private_key()


@pytest.fixture
def alternate_jwk(alternate_private_key):
    return utils.generate_jwk_string(alternate_private_key)


@pytest.fixture
def alternate_key_id(alternate_jwk):
    return utils.generate_key_id(alternate_jwk)


@pytest.fixture
def jwk_set(jwk, key_id, alternate_jwk, alternate_key_id):
    return {
        'keys': {
            key_id: jwk,
            alternate_key_id: alternate_jwk
        }
    }


@pytest.fixture
def token_data():
    return {
        'username': 'test-user',
        'permissions': {},
        'groups': []
    }


@pytest.fixture
def valid_token(private_key, key_id, token_data):
    return utils.encode_token(
        private_key,
        key_id,
        token_data
    )


@pytest.fixture
def invalid_token():
    # using a junk string here rather than a truncated token as truncated
    # tokens do not trigger the desired error
    return 'this is not even a token'.encode('utf-8')


@pytest.fixture
def invalid_token_no_headers(private_key):
    return jwt.encode(
        {'data': 'nodata'},
        private_key,
        algorithm='RS512'
    )


@pytest.fixture
def expired_token(private_key, key_id, token_data):
    expiry = datetime.utcnow() - timedelta(hours=1)
    return utils.encode_token(
        private_key,
        key_id,
        dict(token_data, exp=expiry)
    )
