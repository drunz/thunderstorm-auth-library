from unittest.mock import patch, ANY

from flask import g, Flask
import pytest

from thunderstorm_auth import TOKEN_HEADER, DEFAULT_LEEWAY
from thunderstorm_auth.auditing import AuditConf
from thunderstorm_auth.flask.core import init_ts_auth, TsAuthState
from thunderstorm_auth.flask.decorators import ts_auth_required
from thunderstorm_auth.exceptions import ThunderstormAuthError
from thunderstorm_auth.user import User


def test_ts_auth_required_fails_with_non_callable():
    with pytest.raises(ThunderstormAuthError):
        ts_auth_required('my-perm')


def test_ts_auth_required_with_permission_no_perm(access_token, flask_app, celery):
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


def test_endpoint_returns_200_with_proper_token(access_token_with_permissions, flask_app):
    headers = {'X-Thunderstorm-Key': access_token_with_permissions}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 200


def test_user_with_decoded_token_added_to_g(role_uuid, organization_uuid, access_token_with_permissions, flask_app):
    with flask_app.app_context():
        headers = {'X-Thunderstorm-Key': access_token_with_permissions}
        flask_app.test_client().get('/', headers=headers)

        assert g.user == User(
            username='test-user', roles=[str(role_uuid)], groups=[], organization=str(organization_uuid)
        )


def test_endpoint_returns_401_with_malformed_token(malformed_token, flask_app):
    headers = {'X-Thunderstorm-Key': malformed_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401


def test_endpoint_returns_401_with_expired_token(access_token_expired_with_permissions, flask_app):
    headers = {'X-Thunderstorm-Key': access_token_expired_with_permissions}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401


def test_endpoint_returns_200_when_expired_token_falls_within_leeway(flask_app, access_token_expired_with_permissions):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_LEEWAY'] = 3601
        headers = {'X-Thunderstorm-Key': access_token_expired_with_permissions}

        response = flask_app.test_client().get('/', headers=headers)

        assert response.status_code == 200


def test_endpoint_returns_401_with_missing_token(flask_app):
    response = flask_app.test_client().get('/')

    assert response.status_code == 401


def test_endpoint_returns_500_if_no_public_key_set(access_token_with_permissions, flask_app):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_JWKS'] = None
        headers = {'X-Thunderstorm-Key': access_token_with_permissions}

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
    assert app.config['TS_AUTH_AUDIT_MSG_EXP'] == 3600


def test_ts_auth_extension_has_auditing(datastore, jwk_set):
    app = Flask('test')

    with patch('thunderstorm_auth.flask.core.load_jwks_from_file', return_value=jwk_set):
        init_ts_auth(app, datastore, auditing=True)

    assert isinstance(app.extensions['ts_auth'], TsAuthState)
    assert app.after_request_funcs[None][0].__name__ == 'after_request_auditing'


def test_ts_auth_extension_has_auditing_with_passed_configuration(datastore, jwk_set):
    app = Flask('test')
    auditing = AuditConf(True, ['/status'])

    with patch('thunderstorm_auth.flask.core.load_jwks_from_file', return_value=jwk_set):
        ts_auth = init_ts_auth(app, datastore, auditing=auditing)

    assert app.after_request_funcs[None][0].__name__ == 'after_request_auditing'
    assert ts_auth.auditing.enabled == True
    assert ts_auth.auditing.exclude_paths == ['/status']


def test_endpoint_returns_200_with_proper_token_and_auditing(access_token_with_permissions, audit_flask_app, organization_uuid, role_uuid):
    headers = {'X-Thunderstorm-Key': access_token_with_permissions}
    with patch('thunderstorm_auth.flask.core.send_ts_task') as mock_send_ts_task:
        response = audit_flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 200
    mock_send_ts_task.assert_called_with(
        'audit.data',
        ANY,
        {
            'method': 'GET',
            'action': 'hello_world',
            'endpoint': '/',
            'username': 'test-user',
            'organization_uuid': str(organization_uuid),
            'roles': [str(role_uuid)],
            'groups': [],
            'status': '200 OK'
        },
        expires=3600
    )


def test_endpoint_returns_403_with_access_token_with_permissions_wrong_service_and_auditing(access_token_with_permissions_wrong_service, audit_flask_app, organization_uuid):
    headers = {'X-Thunderstorm-Key': access_token_with_permissions_wrong_service}

    with patch('thunderstorm_auth.flask.core.send_ts_task') as mock_send_ts_task:
        response = audit_flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 403

    mock_send_ts_task.assert_called_with(
        'audit.data',
        ANY,
        {
            'method': 'GET',
            'action': 'hello_world',
            'endpoint': '/',
            'username': 'test-user',
            'organization_uuid': str(organization_uuid),
            'roles': ANY,
            'groups': [],
            'status': '403 FORBIDDEN'
        },
        expires=3600
    )


def test_endpoint_returns_401_with_malformed_token_and_auditing(malformed_token, audit_flask_app, organization_uuid):
    headers = {'X-Thunderstorm-Key': malformed_token}

    with patch('thunderstorm_auth.flask.core.send_ts_task') as mock_send_ts_task:
        response = audit_flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401

    assert not mock_send_ts_task.called


def test_endpoint_returns_401_with_expired_token_and_auditing(access_token_expired_with_permissions, audit_flask_app, organization_uuid):
    headers = {'X-Thunderstorm-Key': access_token_expired_with_permissions}

    with patch('thunderstorm_auth.flask.core.send_ts_task') as mock_send_ts_task:
        response = audit_flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401

    assert not mock_send_ts_task.called


def test_endpoint_returns_401_with_incorrectly_signed_token_and_auditing(token_signed_with_incorrect_key, audit_flask_app, organization_uuid):
    headers = {'X-Thunderstorm-Key': token_signed_with_incorrect_key}

    with patch('thunderstorm_auth.flask.core.send_ts_task') as mock_send_ts_task:
        response = audit_flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401

    assert not mock_send_ts_task.called
