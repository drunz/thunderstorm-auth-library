from datetime import datetime
from abc import ABCMeta, abstractmethod

import requests

from thunderstorm_auth import TOKEN_HEADER
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import ThunderstormAuthError


class RefreshError(Exception):
    def __init__(self, error):
        self.error = error


class AssumeIdentityError(Exception):
    def __init__(self, error):
        self.error = error


class Authenticator(metaclass=ABCMeta):
    """Abstract base class for managing auth refresh cycles"""

    def __init__(self):
        self._cached_access_token_expiry = None

    @property
    @abstractmethod
    def access_token(self):
        pass

    def needs_refresh(self):
        if not self.access_token:
            return True
        if _is_time_in_past(self._cached_access_token_expiry):
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

    def __init__(self, user_service_url, jwks, access_token, refresh_token):
        super()
        self.user_service_url = user_service_url
        self.jwks = jwks
        self._access_token = access_token
        self._refresh_token = refresh_token

    @property
    def access_token(self):
        return self._access_token

    def refresh_access_token(self):
        try:
            resp = requests.post(
                '{}/api/v1/auth/login'.format(self.user_serivce_url),
                json={'token': self.refresh_token},
            )
            access_token, payload = self._parse_response(resp)
        except (requests.RequestException, ThunderstormAuthError) as err:
            raise RefreshError(err)
        else:
            self._access_token = access_token
            self._cached_access_token_expiry = payload['exp']


class AssumedIdentityAuthenticator(Authenticator):
    """Manages the token refresh cycle for assumed identity authentication"""

    def __init__(self, client, assume_identity):
        super()
        self.client = client
        self._assumed_identity_access_token = assume_identity

    @property
    def access_token(self):
        return self._assumed_identity_access_token

    def refresh_access_token(self):
        try:
            resp = self._client.post(
                '{}/api/v1/auth/assume-identity'.format(
                    self.client.user_serivce_url
                ),
                json={'token': self._assumed_identity_access_token},
            )
            access_token, payload = self._parse_response(resp)
        except (requests.RequestException, ThunderstormAuthError) as err:
            raise AssumeIdentityError(err)
        else:
            self._assumed_identity_access_token = access_token
            self._cached_access_token_expiry = payload['exp']


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
    def direct(user_service_url, jwks, access_token, refresh_token):
        return Client(
            DirectIdentityAuthenticator(
                user_service_url, jwks, access_token, refresh_token
            )
        )

    def assume_identity(self, assume_identity):
        return Client(AssumedIdentityAuthenticator(self, assume_identity))

    def get(self, *args, **kwargs):
        return self._request('GET', args, kwargs)

    def post(self, *args, **kwargs):
        return self._request('POST', args, kwargs)

    def put(self, *args, **kwargs):
        return self._request('PUT', args, kwargs)

    def patch(self, *args, **kwargs):
        return self._request('PATCH', args, kwargs)

    def options(self, *args, **kwargs):
        return self._request('OPTIONS', args, kwargs)

    def _request(self, method, args, kwargs, *, refresh=True):
        """Make an authenticated request refreshing if needed"""
        if refresh and self.authenticator.needs_refresh():
            self.authenticator.refresh_access_token()
            refresh = False

        headers = kwargs.setdefault('headers', {})
        headers[TOKEN_HEADER] = self.authenticator.access_token

        res = requests.get(*args, **kwargs)

        if res.status_code == 401 and refresh:
            self.authenticator.refresh_access_token()
            return self._request(method, args, kwargs, refresh=False)


def _is_time_in_past(stamp):
    """Return True if the provided timestamp is in the past

    Args:
        stamp (datetime): Timestamp to test

    Return:
        boolean
    """
    if stamp is None:
        return True
    elif stamp < datetime.utcnow():
        return True

    return False
