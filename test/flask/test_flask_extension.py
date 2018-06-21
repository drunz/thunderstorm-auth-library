from flask import g

from thunderstorm_auth.user import User


def test_endpoint_returns_200_with_proper_token(access_token, flask_app):
    headers = {'X-Thunderstorm-Key': access_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 200


def test_user_with_decoded_token_added_to_g(access_token, flask_app):
    with flask_app.app_context():
        headers = {'X-Thunderstorm-Key': access_token}
        flask_app.test_client().get('/', headers=headers)

        assert g.user == User(
            username='test-user',
            permissions={},
            groups=[]
        )


def test_endpoint_returns_401_with_malformed_token(malformed_token, flask_app):
    headers = {'X-Thunderstorm-Key': malformed_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401


def test_endpoint_returns_401_with_expired_token(
    access_token_expired, flask_app
):
    headers = {'X-Thunderstorm-Key': access_token_expired}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 401


def test_endpoint_returns_200_when_expired_token_falls_within_leeway(
        flask_app, access_token_expired):
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
