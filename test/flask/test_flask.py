import flask
import pytest

from thunderstorm_auth.exceptions import ThunderstormAuthError
from thunderstorm_auth.flask import ts_auth_required
from thunderstorm_auth import utils


@pytest.fixture
def valid_token_with_perm(private_key, key_id, token_data):
    return utils.encode_token(
        private_key,
        key_id,
        {
            'username': 'test-user',
            'permissions': {
                'test-service': ['perm-a']
            },
            'groups': []
        }
    )


@pytest.fixture
def valid_token_with_perm_wrong_service(private_key, key_id):
    return utils.encode_token(
        private_key,
        key_id,
        {
            'username': 'test-user',
            'permissions': {
                'other-service': ['perm-a']
            },
            'groups': []
        }
    )


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

    return app


def test_ts_auth_required_fails_with_non_callable():
    with pytest.raises(ThunderstormAuthError):
        ts_auth_required('my-perm')


def test_ts_auth_required_when_bare(valid_token, flask_app):
    headers = {'X-Thunderstorm-Key': valid_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 200


def test_ts_auth_required_with_no_parameters(valid_token, flask_app):
    headers = {'X-Thunderstorm-Key': valid_token}
    response = flask_app.test_client().get('/no-params', headers=headers)

    assert response.status_code == 200


def test_ts_auth_required_with_permission_no_perm(valid_token, flask_app):
    headers = {'X-Thunderstorm-Key': valid_token}
    response = flask_app.test_client().get('/perm-a', headers=headers)

    assert response.status_code == 403


def test_ts_auth_required_with_permission_with_perm(
    valid_token_with_perm, flask_app
):
    headers = {'X-Thunderstorm-Key': valid_token_with_perm}
    response = flask_app.test_client().get('/perm-a', headers=headers)

    assert response.status_code == 200


def test_ts_auth_required_with_permission_with_perm_wrong_service(
    valid_token_with_perm_wrong_service, flask_app
):
    headers = {'X-Thunderstorm-Key': valid_token_with_perm_wrong_service}
    response = flask_app.test_client().get('/perm-a', headers=headers)

    assert response.status_code == 403