import pytest
import falcon
from falcon import testing as falcon_testing
from flask import Flask

from thunderstorm_auth.testing import *  # noqa
from thunderstorm_auth.falcon import TsAuthMiddleware
from thunderstorm_auth.flask import ts_auth_required


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
