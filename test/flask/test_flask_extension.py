from unittest.mock import patch

from flask import g, Flask
import pytest

from thunderstorm_auth import TOKEN_HEADER, DEFAULT_LEEWAY
from thunderstorm_auth.flask.core import init_ts_auth, TsAuthState
from thunderstorm_auth.flask.decorators import ts_auth_required
from thunderstorm_auth.exceptions import ThunderstormAuthError
from thunderstorm_auth.user import User


def test_ts_auth_required_fails_with_non_callable():
    with pytest.raises(ThunderstormAuthError):
        ts_auth_required('my-perm')


def test_ts_auth_required_when_bare(access_token, flask_app):
    headers = {'X-Thunderstorm-Key': access_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 200


def test_ts_auth_required_with_no_parameters(access_token, flask_app):
    headers = {'X-Thunderstorm-Key': access_token}
    response = flask_app.test_client().get('/no-params', headers=headers)

    assert response.status_code == 200


def test_ts_auth_required_with_permission_no_perm(access_token, flask_app):
    headers = {'X-Thunderstorm-Key': access_token}
    response = flask_app.test_client().get('/perm-a', headers=headers)

    assert response.status_code == 403


def test_ts_auth_required_with_permission_with_perm(access_token_with_permissions, flask_app):
    headers = {'X-Thunderstorm-Key': access_token_with_permissions}
    response = flask_app.test_client().get('/perm-a', headers=headers)

    assert response.status_code == 200


def test_ts_auth_required_with_permission_with_perm_wrong_service(
        access_token_with_permissions_wrong_service, flask_app
):
    headers = {'X-Thunderstorm-Key': access_token_with_permissions_wrong_service}
    response = flask_app.test_client().get('/perm-a', headers=headers)

    assert response.status_code == 403


def test_endpoint_returns_200_with_proper_token(access_token, flask_app):
    headers = {'X-Thunderstorm-Key': access_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 200


def test_user_with_decoded_token_added_to_g(access_token, flask_app):
    with flask_app.app_context():
        headers = {'X-Thunderstorm-Key': access_token}
        flask_app.test_client().get('/', headers=headers)

        assert g.user == User(username='test-user', roles=[], permissions={}, groups=[])


def test_endpoint_returns_401_with_malformed_token(malformed_token, flask_app):
    headers = {'X-Thunderstorm-Key': malformed_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401


def test_endpoint_returns_401_with_expired_token(access_token_expired, flask_app):
    headers = {'X-Thunderstorm-Key': access_token_expired}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401


def test_endpoint_returns_200_when_expired_token_falls_within_leeway(flask_app, access_token_expired):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_LEEWAY'] = 3601
        headers = {'X-Thunderstorm-Key': access_token_expired}

        response = flask_app.test_client().get('/', headers=headers)

        assert response.status_code == 200


def test_endpoint_returns_401_with_missing_token(flask_app):
    response = flask_app.test_client().get('/')

    assert response.status_code == 401


def test_endpoint_returns_500_if_no_public_key_set(access_token, flask_app):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_JWKS'] = None
        headers = {'X-Thunderstorm-Key': access_token}

        response = flask_app.test_client().get('/', headers=headers)

        assert response.status_code == 500


def test_ts_auth_extension_has_state(datastore, jwk_set):
    app = Flask('test')

    with patch('thunderstorm_auth.flask.core.load_jwks_from_file', return_value=jwk_set):
        init_ts_auth(app, datastore)

    assert isinstance(app.extensions['ts_auth'], TsAuthState)
    assert app.extensions['ts_auth'].app == app
    assert app.extensions['ts_auth'].datastore == datastore
    assert app.config['TS_AUTH_LEEWAY'] == DEFAULT_LEEWAY
    assert app.config['TS_AUTH_TOKEN_HEADER'] == TOKEN_HEADER
    assert app.config['TS_AUTH_JWKS'] == jwk_set
