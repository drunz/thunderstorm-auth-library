from datetime import datetime, timedelta
import json
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import falcon
from falcon import testing as falcon_testing
from flask import Flask
import jwt
import pytest

from thunderstorm_auth.falcon import TsAuthMiddleware
from thunderstorm_auth.flask import ts_auth_required


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
    return jwks


@pytest.fixture
def valid_token(private_key):
    return jwt.encode(
        {
            'data': {'more': 123}
        },
        private_key[0],
        algorithm='RS512',
        headers={'kid': private_key[1]}
    )


@pytest.fixture
def invalid_token(valid_token):
    # using a junk string here rather than a truncated token as truncated tokens do not trigger the desired error
    return 'this is not even a token'.encode('utf-8')


@pytest.fixture
def expired_token(private_key):
    return jwt.encode(
        {
            'data': {'more': 123},
            'exp': datetime.utcnow() - timedelta(hours=1)
        },
        private_key[0],
        algorithm='RS512',
        headers={'kid': private_key[1]}
    )


# FALCON FIXTURES


@pytest.fixture
def resource():
    class Resource:

        requires_auth = True

        def on_get(self, req, resp):
            resp.body = 'ok'

    return Resource()


@pytest.fixture
def middleware(jwk_set):
    return TsAuthMiddleware(jwk_set)


@pytest.fixture
def falcon_app(resource, middleware):
    app = falcon.API(middleware=middleware)
    app.add_route('/', resource)
    return app


@pytest.fixture
def client(falcon_app):
    return falcon_testing.TestClient(falcon_app)


# FLASK FIXTURES

@pytest.fixture
def flask_app(jwk_set):
    app = Flask('test_app')
    app.config['TS_AUTH_JWKS'] = jwk_set

    @app.route('/')
    @ts_auth_required
    def hello_world():
        return 'Hello, World!'

    return app
