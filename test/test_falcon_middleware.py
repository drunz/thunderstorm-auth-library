def test_endpoint_returns_200_when_auth_not_required(client, resource):
    resource.requires_auth = False

    response = client.simulate_get('/')

    assert response.status_code == 200, response.json


def test_endpoint_returns_200_with_proper_token(client, valid_token):
    headers = {'X-Thunderstorm-Key': valid_token.decode()}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 200, response.json


def test_endpoint_returns_401_with_invalid_token(client, invalid_token):
    headers = {'X-Thunderstorm-Key': invalid_token.decode()}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 401, response.json


def test_endpoint_returns_401_with_expired_token(client, expired_token):
    headers = {'X-Thunderstorm-Key': expired_token.decode()}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 401, response.json


def test_endpoint_returns_200_when_expired_token_falls_within_leeway(
        client, middleware, expired_token):
    middleware.expiration_leeway = 3600
    headers = {'X-Thunderstorm-Key': expired_token.decode()}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 200, response.json
