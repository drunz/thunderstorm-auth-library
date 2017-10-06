import pytest

from flask import Flask

from thunderstorm_auth.flask import ts_auth_required


@pytest.fixture
def flask_app(secret_key):
    app = Flask('test_app')
    app.config['TS_AUTH_SECRET_KEY'] = secret_key

    @app.route('/')
    @ts_auth_required
    def hello_world():
        return 'Hello, World!'

    return app


def test_endpoint_returns_200_with_proper_token(valid_token, flask_app):
    headers = {'X-Thunderstorm-Key': valid_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 200


def test_endpoint_returns_401_with_invalid_token(invalid_token, flask_app):
    headers = {'X-Thunderstorm-Key': invalid_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401


def test_endpoint_returns_401_with_expired_token(expired_token, flask_app):
    headers = {'X-Thunderstorm-Key': expired_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401


def test_endpoint_returns_200_when_expired_token_falls_within_leeway(
        flask_app, expired_token):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_LEEWAY'] = 3600
        headers = {'X-Thunderstorm-Key': expired_token}

        response = flask_app.test_client().get('/', headers=headers)

        assert response.status_code == 200


def test_endpoint_returns_401_with_missing_token(flask_app):
    response = flask_app.test_client().get('/')

    assert response.status_code == 401


def test_endpoint_returns_500_if_no_secret_key_set(valid_token, flask_app):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_SECRET_KEY'] = None
        headers = {'X-Thunderstorm-Key': valid_token}

        response = flask_app.test_client().get('/', headers=headers)

        assert response.status_code == 500
