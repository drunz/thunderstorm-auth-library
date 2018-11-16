from thunderstorm_auth.user import User


def test_endpoint_returns_200_when_auth_not_required(client, resource):
    resource.requires_auth = False

    response = client.simulate_get('/')

    assert response.status_code == 200, response.json


def test_user_with_decoded_token_data_added_to_req_context(falcon_app, client, access_token_with_permissions):
    class AssertUserResource:

        requires_auth = True

        def on_get(self, req, resp):
            user = req.context['ts_user']
            assert user == User(username='test-user', roles=[], permissions={'test-service': ['perm-a']}, groups=[])

    falcon_app.add_route('/assert-user', AssertUserResource())

    headers = {'X-Thunderstorm-Key': access_token_with_permissions}

    response = client.simulate_get('/assert-user', headers=headers)

    assert response.status_code == 200, response.json


def test_endpoint_returns_200_with_proper_token(client, access_token_with_permissions):
    headers = {'X-Thunderstorm-Key': access_token_with_permissions}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 200, response.json


def test_endpoint_returns_401_with_malformed_token(client, malformed_token):
    headers = {'X-Thunderstorm-Key': malformed_token}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 401, response.json


def test_endpoint_returns_401_with_expired_token(client, access_token_expired):
    headers = {'X-Thunderstorm-Key': access_token_expired}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 401, response.json


def test_endpoint_returns_200_when_expired_token_falls_within_leeway(
        client, middleware, access_token_expired_with_permissions
):
    middleware.expiration_leeway = 3601
    headers = {'X-Thunderstorm-Key': access_token_expired_with_permissions}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 200, response.json


def test_endpoint_returns_401_with_no_permissions(client, access_token):
    headers = {'X-Thunderstorm-Key': access_token}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 401, response.json


def test_endpoint_returns_401_with_permission_on_wrong_service(client, access_token_with_permissions_wrong_service):
    token = access_token_with_permissions_wrong_service
    headers = {'X-Thunderstorm-Key': token}

    response = client.simulate_get('/', headers=headers)

    assert response.status_code == 401, response.json
