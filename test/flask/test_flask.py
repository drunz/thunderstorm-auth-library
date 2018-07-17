import flask
import pytest

from thunderstorm_auth.exceptions import ThunderstormAuthError
from thunderstorm_auth.flask import ts_auth_required


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


def test_ts_auth_required_with_permission_with_perm(
    access_token_with_permissions, flask_app
):
    headers = {'X-Thunderstorm-Key': access_token_with_permissions}
    response = flask_app.test_client().get('/perm-a', headers=headers)

    assert response.status_code == 200


def test_ts_auth_required_with_permission_with_perm_wrong_service(
    access_token_with_permissions_wrong_service, flask_app
):
    headers = {
        'X-Thunderstorm-Key': access_token_with_permissions_wrong_service
    }
    response = flask_app.test_client().get('/perm-a', headers=headers)

    assert response.status_code == 403
