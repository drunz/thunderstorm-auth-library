import json
from datetime import datetime, timedelta

import jwt.algorithms
import pytest

from test import utils


@pytest.fixture
def private_key():
    return utils.generate_private_key()


@pytest.fixture
def jwk(private_key):
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(private_key[0].public_key())
    jwk_dict = json.loads(jwk)
    return {private_key[1]: jwk_dict}


@pytest.fixture
def alternate_private_key():
    return utils.generate_private_key()


@pytest.fixture
def alternate_jwk(alternate_private_key):
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(alternate_private_key[0].public_key())
    jwk_dict = json.loads(jwk)
    return {alternate_private_key[1]: jwk_dict}


@pytest.fixture
def jwk_set(jwk, alternate_jwk):
    jwks = {}
    # merge dictionaries
    jwks.update(jwk)
    jwks.update(alternate_jwk)
    return {"keys": jwks}


@pytest.fixture
def token_data():
    return {
        'username': 'test-user',
        'permissions': {},
        'groups': []
    }


@pytest.fixture
def valid_token(private_key, token_data):
    return utils.encode_token(private_key, token_data)


@pytest.fixture
def invalid_token():
    # using a junk string here rather than a truncated token as truncated tokens do not trigger the desired error
    return 'this is not even a token'.encode('utf-8')


@pytest.fixture
def invalid_token_no_headers(private_key):
    return jwt.encode({'data': 'nodata'}, private_key[0], algorithm='RS512')


@pytest.fixture
def expired_token(private_key, token_data):
    expiry = datetime.utcnow() - timedelta(hours=1)
    return utils.encode_token(
        private_key,
        dict(token_data, exp=expiry)
    )
