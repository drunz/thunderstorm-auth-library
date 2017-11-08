import flask
import pytest

from thunderstorm_auth.flask import ts_auth_required


@pytest.fixture
def flask_app(jwk_set):
    app = flask.Flask('test_app')
    app.config['TS_AUTH_JWKS'] = jwk_set

    @app.route('/')
    @ts_auth_required
    def hello_world():
        return 'Hello, World!'

    return app
