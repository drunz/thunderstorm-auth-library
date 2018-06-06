from thunderstorm_auth.user import User


def test_endpoint_returns_200_when_auth_not_required(client, resource):
    resource.requires_auth = False

    response = client.simulate_get('/')

    assert response.status_code == 200, response.json


def test_user_with_decoded_token_data_added_to_req_context(
    falcon_app, client, valid_token_with_perm
):
    class AssertUserResource:

        requires_auth = True

        def on_get(self, req, resp):
            user = req.context['ts_user']
            assert user == User(
                username='test-user',
                permissions={'test-service': ['perm-a']},
                groups=[]
            )

    falcon_app.add_route('/assert-user', AssertUserResource())

    headers = {'X-Thunderstorm-Key': valid_token_with_perm.decode()}

    response = client.simulate_get('/assert-user', headers=headers)

    assert response.status_code == 200, response.json


def test_endpoint_returns_200_with_proper_token(client, valid_token_with_perm):
    headers = {'X-Thunderstorm-Key': valid_token_with_perm.decode()}

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
    client, middleware, expired_token_with_perm
):
    middleware.expiration_leeway = 3601
    headers = {'X-Thunderstorm-Key': expired_token_with_perm.decode()}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 200, response.json


def test_endpoint_returns_401_with_no_permissions(client, valid_token):
    headers = {'X-Thunderstorm-Key': valid_token.decode()}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 401, response.json


def test_endpoint_returns_401_with_permission_on_wrong_service(
    client, valid_token_with_perm_wrong_service
):
    token = valid_token_with_perm_wrong_service
    headers = {'X-Thunderstorm-Key': token.decode()}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 401, response.json
