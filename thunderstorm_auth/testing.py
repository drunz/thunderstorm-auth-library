from datetime import datetime, timedelta
import json
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import jwt
import pytest


__all__ = [
    'encode_token',
    'private_key', 'jwk', 'alternate_private_key', 'alternate_jwk',
    'jwk_set', 'valid_token', 'invalid_token', 'expired_token',
]


def generate_private_key():
    """
    When signing keys on the user-service we include a 'kid' (Key ID) field in the JWT headers
    This header is used to pick the correct JWK to decode a token when there are multiple JWKs.
    Each JWK also includes this field. Using a UUID here but this identifier could be any unique string.
    """
    return rsa.generate_private_key(backend=crypto_default_backend(),
                                    public_exponent=65537,
                                    key_size=2048
                                    ), str(uuid4())


def encode_token(private_key, payload):
    """Encode a token with a private key

    Args:
        private_key (tuple): A private key from `generate_private_key`.
                             Most likely from the `private_key` or
                             `alternate_private_key` fixtures.
        payload (dict):      The payload of the token.

    Returns:
        str: Encoded JWT
    """
    return jwt.encode(
        payload,
        private_key[0],
        algorithm='RS512',
        headers={'kid': private_key[1]}
    )


@pytest.fixture
def private_key():
    return generate_private_key()


@pytest.fixture
def jwk(private_key):
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(private_key[0].public_key())
    jwk_dict = json.loads(jwk)
    return {private_key[1]: jwk_dict}


@pytest.fixture
def alternate_private_key():
    return generate_private_key()


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
def valid_token(private_key):
    return encode_token(private_key, {'data': {'more': 123}})


@pytest.fixture
def invalid_token(valid_token):
    # using a junk string here rather than a truncated token as truncated tokens do not trigger the desired error
    return 'this is not even a token'.encode('utf-8')


@pytest.fixture
def expired_token(private_key):
    return encode_token(
        private_key,
        {
            'data': {'more': 123},
            'exp': datetime.utcnow() - timedelta(hours=1)
        }
    )
