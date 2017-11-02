from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt


def generate_private_key():
    """
    When signing keys on the user-service we include a 'kid' (Key ID) field in the JWT headers
    This header is used to pick the correct JWK to decode a token when there are multiple JWKs.
    Each JWK also includes this field. Using a UUID here but this identifier could be any unique string.
    """
    private_key = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048
    )
    key_id = str(uuid4())
    return private_key, key_id


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
    key, key_id = private_key

    return jwt.encode(
        payload,
        key,
        algorithm='RS512',
        headers={'kid': key_id}
    )
