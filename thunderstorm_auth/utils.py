import json
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt


def load_jwks_from_file(path):
    with open(path, 'r') as f:
        try:
            jwks = json.load(f)
            assert len(jwks['keys']) > 0
            return jwks
        except (ValueError, KeyError, AssertionError):
            raise ValueError('Invalid JWK Set at {}'.format(path))


def generate_private_key():
    """
    When signing keys on the user-service we include a 'kid' (Key ID) field in the JWT headers
    This header is used to pick the correct JWK to decode a token when there are multiple JWKs.
    Each JWK also includes this field. Using a UUID here but this identifier could be any unique string.
    """
    return rsa.generate_private_key(
        backend=default_backend(),
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
