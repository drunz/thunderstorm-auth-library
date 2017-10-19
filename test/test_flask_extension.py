from flask import g


def test_endpoint_returns_200_with_proper_token(valid_token, flask_app):
    headers = {'X-Thunderstorm-Key': valid_token}
    response = flask_app.test_client().get('/', headers=headers)

    assert response.status_code == 200


def test_decoded_token_added_to_g(valid_token, flask_app):
    with flask_app.app_context():
        headers = {'X-Thunderstorm-Key': valid_token}
        flask_app.test_client().get('/', headers=headers)

        assert g.token == {'data': {'more': 123}}


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


def test_endpoint_returns_500_if_no_public_key_set(valid_token, flask_app):
    with flask_app.app_context():
        flask_app.config['TS_AUTH_JWKS'] = None
        headers = {'X-Thunderstorm-Key': valid_token}

        response = flask_app.test_client().get('/', headers=headers)

        assert response.status_code == 500
