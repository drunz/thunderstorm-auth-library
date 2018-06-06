import json
import logging

from thunderstorm_auth import TOKEN_HEADER
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import (
    TokenError, TokenHeaderMissing, AuthJwksNotSet,
    ThunderstormAuthError, InsufficientPermissions
)
from thunderstorm_auth import permissions
from thunderstorm_auth.user import User

try:
    import falcon
    HAS_FALCON = True
except ImportError:
    HAS_FALCON = False


logger = logging.getLogger(__name__)

USER_CONTEXT_KEY = 'ts_user'


class TsAuthMiddleware:
    """Falcon middleware for Thunderstorm Authentication."""

    def __init__(
        self, jwks, expiration_leeway=0,
        with_permission=None, service_name=None,

    ):
        """Falcon middleware for Thunderstorm Authentication.

        Args:
            jwks (dict): JWK Set containing JWKs (dicts) which may be used to decode an auth token
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
        self.with_permission = with_permission
        self.service_name = service_name

        if not self.with_permission:
            logger.error('Auth configured with no permission')

    def process_resource(self, req, res, resource, params):
        requires_auth = getattr(resource, 'requires_auth', False)

        if requires_auth:
            try:
                decoded_token_data = self._decode_token(req)
                self._validate_permission(decoded_token_data)
            except (TokenError, InsufficientPermissions) as error:
                raise _bad_token(error)

            user = User.from_decoded_token(decoded_token_data)
            req.context[USER_CONTEXT_KEY] = user

    def _decode_token(self, request):
        token = _get_token(request)
        if not self.jwks.get('keys'):
            raise AuthJwksNotSet(
                'There are no JWKs in the JWK set provided or the set is not structured properly'
            )
        return decode_token(
            token,
            self.jwks,
            leeway=self.expiration_leeway
        )

    def _validate_permission(self, token_data):
        if self.with_permission:
            permissions.validate_permission(
                token_data, self.service_name, self.with_permission
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
