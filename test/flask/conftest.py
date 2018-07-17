import flask
import pytest

from thunderstorm_auth.flask import ts_auth_required
from thunderstorm_auth.exceptions import HTTPError

@pytest.fixture
def flask_app(jwk_set):
    app = flask.Flask('test_app')
    app.config['TS_AUTH_JWKS'] = jwk_set

    app.config['TS_SERVICE_NAME'] = 'test-service'

    @app.route('/')
    @ts_auth_required
    def hello_world():
        return 'Hello, World!'

    @app.route('/no-params')
    @ts_auth_required()
    def no_params():
        return 'no params'

    @app.route('/perm-a')
    @ts_auth_required(with_permission='perm-a')
    def with_perm_a():
        return 'with perm a'

    @app.errorhandler(HTTPError)
    def handle_invalid_usage(exc):
        data = {'code': exc.code, 'message': exc.message}

        return flask.jsonify(data), data['code']

    return app
