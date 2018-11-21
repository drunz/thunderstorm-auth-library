from unittest import mock

from thunderstorm_auth.logging import requests


@mock.patch('thunderstorm_auth.logging.requests._get')
@mock.patch('thunderstorm_auth.logging.requests._get_request_id')
def test_get(mock_get_request_id, mock_get):
    mock_get_request_id.return_value = 'request-id'

    requests.get('/')

    mock_get.assert_called_with('/', headers={'TS-Request-ID': 'request-id'})


@mock.patch('thunderstorm_auth.logging.requests._get')
@mock.patch('thunderstorm_auth.logging.requests._get_request_id')
def test_get_with_headers(mock_get_request_id, mock_get):
    mock_get_request_id.return_value = 'request-id'

    requests.get('/', headers={'foo': 'bar'})

    mock_get.assert_called_with(
        '/', headers={
            'TS-Request-ID': 'request-id',
            'foo': 'bar',
        }
    )


@mock.patch('thunderstorm_auth.logging.requests._get')
@mock.patch('thunderstorm_auth.logging.requests._get_request_id')
def test_get_with_request_id(mock_get_request_id, mock_get):
    mock_get_request_id.return_value = 'request-id'

    requests.get('/', headers={'TS-Request-ID': 'my-id'})

    mock_get.assert_called_with(
        '/', headers={
            'TS-Request-ID': 'my-id',
        }
    )
