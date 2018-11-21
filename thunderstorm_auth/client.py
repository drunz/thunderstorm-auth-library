from datetime import datetime
from abc import ABCMeta, abstractmethod

from requests import RequestException

from thunderstorm_auth import TOKEN_HEADER
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import ThunderstormAuthError
from thunderstorm_auth.logging import requests


class RefreshError(Exception):
    def __init__(self, error):
        self.error = error


class AssumeIdentityError(Exception):
    def __init__(self, error):
        self.error = error


class Authenticator(metaclass=ABCMeta):
    """Abstract base class for managing auth refresh cycles"""

    @property
    @abstractmethod
    def access_token(self):
        pass

    def needs_refresh(self):
        if not self.access_token:
            return True
        if _is_time_in_past(self._access_token_expiry):
            return True
        return False

    @abstractmethod
    def refresh_access_token(self):
        pass

    def _parse_response(self, resp):
        resp.raise_for_status()
        access_token = resp.json()['token']
        payload = decode_token(access_token, self.jwks)

        return (access_token, payload)


class DirectIdentityAuthenticator(Authenticator):
    """Manages the token refresh cycle for normal authentication"""

    def __init__(self, user_service_url, jwks, refresh_token, access_token=None):
        super()
        self.user_service_url = user_service_url
        self.jwks = jwks
        self._access_token = access_token
        self._access_token_expiry = get_token_expiry(access_token, jwks)
        self._refresh_token = refresh_token

    @property
    def access_token(self):
        return self._access_token

    def refresh_access_token(self):
        try:
            resp = requests.post(
                '{}/api/v1/auth/login'.format(self.user_service_url),
                json={'token': self._refresh_token},
            )
            access_token, payload = self._parse_response(resp)
        except (RequestException, ThunderstormAuthError) as err:
            raise RefreshError(err)
        else:
            self._access_token = access_token
            self._access_token_expiry = payload['exp']


class AssumedIdentityAuthenticator(Authenticator):
    """Manages the token refresh cycle for assumed identity authentication"""

    def __init__(self, client, assume_identity):
        super()
        self._client = client
        self.jwks = self._client.authenticator.jwks
        self._access_token = assume_identity
        self._access_token_expiry = get_token_expiry(assume_identity, self.jwks)

    @property
    def access_token(self):
        return self._access_token

    def refresh_access_token(self):
        try:
            resp = self._client.post(
                '{}/api/v1/auth/assume-identity'.format(self._client.authenticator.user_service_url),
                json={'token': self.access_token},
                headers={'X-Thunderstorm-Key': self._client.authenticator.access_token}
            )
            access_token, payload = self._parse_response(resp)
        except (RequestException, ThunderstormAuthError) as err:
            raise AssumeIdentityError(err)
        else:
            self._access_token = access_token
            self._access_token_expiry = payload['exp']


class Client:
    """Authenticated AAM HTTP client

    This client presents a requests interface that automatically adds and
    refreshes thunderstorm authentication details.

    It can also be used to assume an end user identity and make requests
    as that identity.

    Usage:
        >>> client = Client.direct(
        ...     user_service_url, jwks, access_token, refresh_token
        ... )
        >>> client.get(some_url)
        >>> end_user_client = client.assume_identity(end_user_access_token)
        >>> end_user_client.get(some_url)
    """

    def __init__(self, authenticator: Authenticator):
        self.authenticator = authenticator

    @staticmethod
    def direct(user_service_url, jwks, refresh_token, access_token=None):
        return Client(DirectIdentityAuthenticator(user_service_url, jwks, refresh_token, access_token=access_token))

    def assume_identity(self, assume_identity):
        return Client(AssumedIdentityAuthenticator(self, assume_identity))

    def get(self, *args, **kwargs):
        return self._request('get', args, kwargs)

    def post(self, *args, **kwargs):
        return self._request('post', args, kwargs)

    def put(self, *args, **kwargs):
        return self._request('put', args, kwargs)

    def patch(self, *args, **kwargs):
        return self._request('patch', args, kwargs)

    def options(self, *args, **kwargs):
        return self._request('options', args, kwargs)

    def delete(self, *args, **kwargs):
        return self._request('delete', args, kwargs)

    def _request(self, method, args, kwargs, *, refresh=True):
        """Make an authenticated request refreshing if needed"""
        if refresh and self.authenticator.needs_refresh():
            self.authenticator.refresh_access_token()
            refresh = False

        headers = kwargs.setdefault('headers', {})
        headers[TOKEN_HEADER] = self.authenticator.access_token

        res = getattr(requests, method)(*args, **kwargs)
        if res.status_code == 401 and refresh:
            self.authenticator.refresh_access_token()
            self._request(method, args, kwargs, refresh=False)

        return res


def _is_time_in_past(stamp):
    """Return True if the provided timestamp is in the past

    Args:
        stamp (int/float): Timestamp to test

    Return:
        boolean
    """
    if stamp is None:
        return True
    elif stamp <= datetime.utcnow().timestamp():
        return True

    return False


def get_token_expiry(token, jwks):
    """
    Get the expiry time of a token

    Args:
        token (str): JWT to be decoded
        jwks (dict): Dict of keys to try when decoding the token

    Returns:
        int on success, otherwise None
    """
    if not token:
        return None

    return decode_token(token, jwks, options={'verify_exp': False})['exp']
