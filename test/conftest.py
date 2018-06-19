from datetime import timedelta
import functools

import jwt.algorithms
import pytest

from thunderstorm_auth import utils


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
    return {
        'keys': {
            key_id: jwk,
            alternate_key_id: alternate_jwk
        }
    }


@pytest.fixture
def access_token_payload():
    return {
        'username': 'test-user',
        'token_type': 'access',
        'groups': [],
        'permissions': {}
    }


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
    return functools.partial(
        utils.encode_token,
        private_key,
        key_id
    )


@pytest.fixture
def access_token(make_token, access_token_payload):
    return make_token(access_token_payload)


@pytest.fixture
def access_token_with_permissions(make_token, access_token_payload):
    access_token_payload['permissions'] = {
        # service name needs to match the service name defined in flask_app fixture
        'test-service': ['perm-a']
    }
    return make_token(access_token_payload)


@pytest.fixture
def access_token_with_permissions_wrong_service(make_token, access_token_payload):
    access_token_payload['permissions'] = {
        'other-service': ['perm-a']
    }
    return make_token(access_token_payload)


@pytest.fixture
def access_token_expired(make_token, access_token_payload):
    lifetime = timedelta(hours=-1)
    return make_token(access_token_payload, lifetime=lifetime)


@pytest.fixture
def access_token_expired_with_permissions(make_token, access_token_payload):
    lifetime = timedelta(hours=-1)
    access_token_payload['permissions'] = {
        'test-service': ['perm-a']
    }
    return make_token(access_token_payload, lifetime=lifetime)


@pytest.fixture
def refresh_token(make_token, refresh_token_payload):
    return make_token(refresh_token_payload)


@pytest.fixture
def token_signed_with_incorrect_key(
    key_id, access_token_payload, alternate_private_key
):
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
    return jwt.encode(
        {'data': 'nodata'},
        private_key,
        algorithm='RS512'
    )
