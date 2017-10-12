import json

from thunderstorm_auth import TOKEN_HEADER
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import ThunderstormAuthError
from thunderstorm_auth.exceptions import TokenError, TokenHeaderMissing

try:
    import falcon
    HAS_FALCON = True
except ImportError:
    HAS_FALCON = False


CONTEXT_KEY = 'ts_auth'


class TsAuthMiddleware:
    """Falcon middleware for Thunderstorm Authentication."""

    def __init__(self, jwks, expiration_leeway=0):
        """Falcon middleware for Thunderstorm Authentication.

        Args:
            jwks (list): Set of jwks (dicts) which may be used to decode an auth token
            expiration_leeway (int): Optional number of seconds of lenience when
                calculating token expiry.

        Raises:
            ThunderstormAuthError: If Falcon is not installed.
        """
        if not HAS_FALCON:
            raise ThunderstormAuthError(
                'Cannot create Falcon middleware as Falcon is not installed.'
            )

        self.expiration_leeway = expiration_leeway
        self.jwks = jwks

    def process_resource(self, req, res, resource, params):
        requires_auth = getattr(resource, 'requires_auth', False)

        if requires_auth:
            try:
                decoded_auth_data = self._decode_token(req)
            except TokenError as error:
                raise _bad_token(error)
            else:
                req.context[CONTEXT_KEY] = decoded_auth_data

    def _decode_token(self, request):
        token = _get_token(request)
        return decode_token(
            token,
            self.jwks,
            leeway=self.expiration_leeway
        )


def _get_token(request):
    token = request.get_header(TOKEN_HEADER)
    if token is None:
        raise TokenHeaderMissing()
    return token


def _bad_token(error):
    body = json.dumps({
        'message': str(error)
    })
    return falcon.HTTPStatus(falcon.HTTP_401, body=body)
