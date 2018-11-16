from datetime import datetime, timedelta
import hashlib
import json

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import jwt
from jwt.algorithms import RSAAlgorithm


def load_jwks_from_file(path):
    with open(path, 'r') as f:
        try:
            jwks = json.load(f)
            assert len(jwks['keys']) > 0
            return jwks
        except (ValueError, KeyError, AssertionError):
            raise ValueError('Invalid JWK Set at {}'.format(path))


def generate_private_key():
    return rsa.generate_private_key(backend=crypto_default_backend(), public_exponent=65537, key_size=2048)


def generate_jwk(private_key):
    return json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))


def generate_key_id(jwk):
    return hashlib.md5(json.dumps(jwk).encode('utf-8')).hexdigest()


def encode_token(private_key, key_id, payload, lifetime=None):
    """Encode a token with a private key

    Args:
        private_key:         A private key from `generate_private_key`.
        key_id (str):        Identifier for `private_key`.
        payload (dict):      The payload of the token.

    Returns:
        str: Encoded JWT
    """
    # issued at time
    payload['iat'] = datetime.utcnow()

    lifetime = lifetime or timedelta(minutes=15)

    expiry = datetime.utcnow() + lifetime
    payload['exp'] = expiry

    return jwt.encode(payload, private_key, algorithm='RS512', headers={'kid': key_id}).decode()
