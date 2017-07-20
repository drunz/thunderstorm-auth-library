import pytest

from conftest import invalid_token, expired_token
from thunderstorm_auth.auth import decode_token, AuthFlaskError, AuthSecretKeyNotSet


def test_decode_token_returns_if_jwt_valid(valid_token, flask_app):
    with flask_app.app_context():
        assert decode_token(valid_token)


def test_decode_token_raises_if_no_secret_key_set(invalid_token, flask_app):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_SECRET_KEY'] = None
        with pytest.raises(AuthSecretKeyNotSet):
            decode_token(invalid_token)


def test_decode_token_raises_if_jwt_invalid(invalid_token, flask_app):
    with flask_app.app_context():
        with pytest.raises(AuthFlaskError):
            decode_token(invalid_token)


def test_decode_token_raises_if_jwt_expired(expired_token, flask_app):
    with flask_app.app_context():
        with pytest.raises(AuthFlaskError):
            decode_token(expired_token)


def test_decode_token_does_not_raise_if_jwt_expired_but_leeway_is_set(expired_token, flask_app):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_LEEWAY'] = 3600
        assert decode_token(expired_token)


def test_endpoint_returns_200_with_proper_token(valid_token, flask_app):
    response = flask_app.test_client().get('/', headers={'X-Thunderstorm-Key': valid_token})

    assert response.status_code == 200


@pytest.mark.parametrize('token,', [invalid_token, expired_token, None])
def test_endpoint_returns_401_with_invalid_token(token, flask_app):
    response = flask_app.test_client().get('/', headers={'X-Thunderstorm-Key': token})

    assert response.status_code == 401


def test_endpoint_returns_500_if_no_secret_key_set(valid_token, flask_app):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_SECRET_KEY'] = None
        response = flask_app.test_client().get('/', headers={'X-Thunderstorm-Key': valid_token})

        assert response.status_code == 500
