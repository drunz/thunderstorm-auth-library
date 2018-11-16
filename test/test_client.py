from unittest.mock import patch, PropertyMock

import pytest
from requests import RequestException

from thunderstorm_auth.client import (
    Client, AssumedIdentityAuthenticator, DirectIdentityAuthenticator, get_token_expiry, AssumeIdentityError,
    RefreshError
)
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import ThunderstormAuthError


def test_direct_returns_client_with_DirectIdentityAuthenticator(jwk_set, access_token, refresh_token):
    # act
    client = Client.direct('http://user-service-url', jwk_set, refresh_token)

    # assert
    assert isinstance(client.authenticator, DirectIdentityAuthenticator)


def test_assume_identity_returns_client_with_AssumedIdentityAuthenticator(jwk_set, access_token, refresh_token):
    # arrange/act
    client = Client.direct('http://user-service-url', jwk_set, refresh_token)
    end_user_client = client.assume_identity(access_token)

    # assert
    assert isinstance(end_user_client.authenticator, AssumedIdentityAuthenticator)


@patch('thunderstorm_auth.client.requests')
def test_direct_identity_client_requests_access_token_when_none_set(
        mock_requests, jwk_set, access_token, refresh_token
):
    # arrange
    mock_requests.post.return_value.json.return_value = {'token': access_token}
    client = Client.direct('http://user-service-url', jwk_set, refresh_token)

    # act
    client.get('http://example.com')

    # assert
    mock_requests.post.assert_called_with('http://user-service-url/api/v1/auth/login', json={'token': refresh_token})

    mock_requests.get.assert_called_with('http://example.com', headers={'X-Thunderstorm-Key': access_token})


@patch('thunderstorm_auth.client.requests')
def test_direct_identity_client_does_not_request_access_token_when_valid_token_set(
        mock_requests, jwk_set, access_token, refresh_token
):
    # arrange
    mock_requests.post.return_value.json.return_value = {'token': access_token}
    client = Client.direct('http://user-service-url', jwk_set, refresh_token, access_token=access_token)

    # act
    client.get('http://example.com')

    # assert
    assert not mock_requests.post.called
    mock_requests.get.assert_called_with('http://example.com', headers={'X-Thunderstorm-Key': access_token})


@patch('thunderstorm_auth.client.requests')
def test_assume_identity_client_with_valid_token_set_does_not_request_new_token(
        mock_requests, jwk_set, access_token, refresh_token
):
    # arrange
    mock_requests.post.return_value.json.return_value = {'token': access_token}
    client = Client.direct('http://user-service-url', jwk_set, refresh_token)
    end_user_client = client.assume_identity(access_token)

    # act
    end_user_client.get('http://example.com')

    # assert
    assert not mock_requests.post.called
    mock_requests.get.assert_called_with('http://example.com', headers={'X-Thunderstorm-Key': access_token})


@patch('thunderstorm_auth.client.requests')
def test_assume_identity_client_with_expired_token_refreshes_token(
        mock_requests, jwk_set, access_token_expired, access_token, refresh_token
):
    # arrange
    mock_requests.post.return_value.json.return_value = {'token': access_token}
    client = Client.direct('http://user-service-url', jwk_set, refresh_token)
    end_user_client = client.assume_identity(access_token_expired)

    # act
    end_user_client.get('http://example.com')

    # assert
    assert end_user_client.authenticator.access_token == access_token

    mock_requests.post.assert_called_with(
        'http://user-service-url/api/v1/auth/assume-identity',
        json={'token': access_token_expired},
        headers={'X-Thunderstorm-Key': access_token}
    )

    mock_requests.get.assert_called_with('http://example.com', headers={'X-Thunderstorm-Key': access_token})


@patch('thunderstorm_auth.client.decode_token')
def test_get_token_expiry_with_None(mock_decode_token):
    assert get_token_expiry(None, {'fake': 'jwks'}) is None


def test_get_token_expiry_with_expired_token(access_token_expired, jwk_set):
    exp = decode_token(access_token_expired, jwk_set, options={'verify_exp': False})['exp']

    assert get_token_expiry(access_token_expired, jwk_set) == exp


@pytest.mark.parametrize('exception_class', [ThunderstormAuthError, RequestException])
def test_assumed_identity_client_refresh_access_token_failure(
        exception_class, jwk_set, access_token_expired, refresh_token
):
    # arrange
    client = Client.direct('http://user-service-url', jwk_set, refresh_token)

    end_user_client = client.assume_identity(access_token_expired)

    # act/assert
    with patch.object(end_user_client.authenticator._client, '_request', new_callable=PropertyMock) as mock__client:
        mock__client.post.side_effect = exception_class
        with pytest.raises(AssumeIdentityError):
            end_user_client.get('http://foo.com')
            # not updated
            assert end_user_client.authenticator.access_token == access_token_expired


@patch('thunderstorm_auth.client.requests')
def test_assumed_identity_client_refresh_access_token_success(
        mock_requests, jwk_set, access_token, refresh_token, access_token_expired
):
    # arrange
    mock_requests.post.return_value.json.return_value = {'token': access_token}
    exp = decode_token(access_token, jwk_set)['exp']
    client = Client.direct('http://user-service-url', jwk_set, refresh_token)
    end_user_client = client.assume_identity(access_token_expired)

    # act
    end_user_client.authenticator.refresh_access_token()

    # assert
    assert end_user_client.authenticator.access_token is access_token
    assert end_user_client.authenticator._access_token_expiry == exp


@patch('thunderstorm_auth.client.requests')
def test_direct_identity_client_refresh_access_token_success(
        mock_requests, jwk_set, access_token_expired, refresh_token, access_token
):
    # arrange
    mock_requests.post.return_value.json.return_value = {'token': access_token}
    exp = decode_token(access_token, jwk_set, options={'verify_exp': False})['exp']
    client = Client.direct('http://user-service-url', jwk_set, refresh_token, access_token=access_token_expired)

    # act
    client.authenticator.refresh_access_token()

    # assert
    assert client.authenticator.access_token == access_token
    assert client.authenticator._access_token_expiry == exp


@patch('thunderstorm_auth.client.requests')
def test_direct_identity_client_refresh_access_token_failure(
        mock_requests, jwk_set, access_token_expired, refresh_token, access_token
):
    # arrange
    client = Client.direct('http://user-service-url', jwk_set, refresh_token, access_token=access_token_expired)
    exp = decode_token(access_token_expired, jwk_set, options={'verify_exp': False})['exp']

    # because we patch requests we need to put back RequestException otherwise
    # the except block of refresh_access_token will fail
    mock_requests.RequestException = RequestException
    mock_requests.post.side_effect = ThunderstormAuthError

    # act/assert
    # act/assert
    with pytest.raises(RefreshError):
        client.get('http://foo.com')
        # not updated
        assert client.authenticator.access_token == access_token_expired
        assert client.authenticator._access_token_expiry == exp


@pytest.mark.parametrize('http_method', ['get', 'post', 'put', 'patch', 'options', 'delete'])
def test_client_calls__request_with__correct_args(http_method, access_token, jwk_set, refresh_token):
    # arrange
    client = Client.direct('http://user-service-url', jwk_set, refresh_token, access_token=access_token)

    # act
    with patch.object(client, '_request', new_callable=PropertyMock) as mock__request:
        getattr(client, http_method)('http://foo.com', 'arg1', 'arg2', kwarg='some_kwarg')
        mock__request.assert_called_with(http_method, ('http://foo.com', 'arg1', 'arg2'), {'kwarg': 'some_kwarg'})
