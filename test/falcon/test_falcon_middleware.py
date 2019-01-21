from unittest.mock import patch, ANY

from thunderstorm_auth.user import User


def test_endpoint_returns_200_when_auth_not_required(client, resource):
    resource.requires_auth = False

    response = client.simulate_get('/')

    assert response.status_code == 200, response.json


def test_user_with_decoded_token_data_added_to_req_context(falcon_app, client, access_token_with_permissions, role_uuid, organization_uuid):
    class AssertUserResource:

        requires_auth = True

        def on_get(self, req, resp):
            user = req.context['ts_user']
            assert user == User(username='test-user', roles=[str(role_uuid)], groups=[], organization=str(organization_uuid))

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


def test_endpoint_returns_401_with_expired_token(client, access_token_expired_with_permissions):
    headers = {'X-Thunderstorm-Key': access_token_expired_with_permissions}

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


def test_endpoint_returns_200_with_proper_token_with_auditing(audit_client, access_token_with_permissions, organization_uuid, role_uuid):
    headers = {'X-Thunderstorm-Key': access_token_with_permissions}

    with patch('thunderstorm_auth.falcon.send_ts_task') as mock_send_ts_task:
        response = audit_client.simulate_get('/', headers=headers)

    assert response.status_code == 200, response.json
    mock_send_ts_task.assert_called_with(
        'audit.data',
        ANY,
        {
            'method': 'GET',
            'action': 'Resource_GET_/',
            'endpoint': '/',
            'username': 'test-user',
            'organization_uuid': str(organization_uuid),
            'roles': [str(role_uuid)],
            'groups': [],
            'status': '200 OK'
        },
        expires=3600
    )


def test_endpoint_returns_401_with_permission_on_wrong_service_with_auditing(audit_client, access_token_with_permissions_wrong_service, organization_uuid):
    token = access_token_with_permissions_wrong_service
    headers = {'X-Thunderstorm-Key': token}

    with patch('thunderstorm_auth.falcon.send_ts_task') as mock_send_ts_task:
        response = audit_client.simulate_get('/', headers=headers)

    assert response.status_code == 401, response.json
    mock_send_ts_task.assert_called_with(
        'audit.data',
        ANY,
        {
            'method': 'GET',
            'action': 'Resource_GET_/',
            'endpoint': '/',
            'username': 'test-user',
            'organization_uuid': str(organization_uuid),
            'roles': ANY,
            'groups': [],
            'status': '401 Unauthorized'
        },
        expires=3600
    )


def test_endpoint_returns_401_with_malformed_token_and_auditing(malformed_token, audit_client, organization_uuid):
    headers = {'X-Thunderstorm-Key': malformed_token}

    with patch('thunderstorm_auth.falcon.send_ts_task') as mock_send_ts_task:
        response = audit_client.simulate_get('/', headers=headers)

    assert response.status_code == 401

    assert not mock_send_ts_task.called


def test_endpoint_returns_401_with_expired_token_and_auditing(access_token_expired_with_permissions, audit_client, organization_uuid):
    headers = {'X-Thunderstorm-Key': access_token_expired_with_permissions}

    with patch('thunderstorm_auth.falcon.send_ts_task') as mock_send_ts_task:
        response = audit_client.simulate_get('/', headers=headers)

    assert response.status_code == 401

    assert not mock_send_ts_task.called


def test_endpoint_returns_401_with_incorrectly_signed_token_and_auditing(token_signed_with_incorrect_key, audit_client, organization_uuid):
    headers = {'X-Thunderstorm-Key': token_signed_with_incorrect_key}

    with patch('thunderstorm_auth.falcon.send_ts_task') as mock_send_ts_task:
        response = audit_client.simulate_get('/', headers=headers)

    assert response.status_code == 401
    assert not mock_send_ts_task.called
