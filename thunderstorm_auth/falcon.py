import json
import logging

from thunderstorm.messaging import send_ts_task

from thunderstorm_auth import TOKEN_HEADER
from thunderstorm_auth.auditing import AuditSchema
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import (
    TokenError, TokenHeaderMissing, AuthJwksNotSet, ThunderstormAuthError, InsufficientPermissions
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
            self,
            jwks,
            datastore=None,
            expiration_leeway=0,
            with_permission=None,
            service_name=None,
            auditing=False
    ):
        """Falcon middleware for Thunderstorm Authentication.

        Args:
            jwks (dict): JWK Set containing JWKs (dicts) which may be used to decode an auth token
            datastore (AuthDatastore object): datastore used for the auth data retrieval
            expiration_leeway (int): Optional number of seconds of lenience when
                calculating token expiry.
            auditing (bool): Defines whether or not auditing is enabled for API calls

        Raises:
            ThunderstormAuthError: If Falcon is not installed.
        """
        if not HAS_FALCON:
            raise ThunderstormAuthError('Cannot create Falcon middleware as Falcon is not installed.')

        self.expiration_leeway = expiration_leeway
        self.datastore = datastore
        self.jwks = jwks
        self.with_permission = with_permission
        self.service_name = service_name
        self.auditing = auditing
        self.audit_msg_exp = 3600

        if not self.with_permission:
            raise ThunderstormAuthError('Route with auth but no permission is not allowed.')

        if not self.datastore:
            raise ThunderstormAuthError('Datastore needs to be set and a valid AuthDatastore object')


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

    def process_response(self, req, res, resource, req_succeeded):
        if not self.auditing:
            return

        try:
            user = req.context.get(USER_CONTEXT_KEY) or User.from_decoded_token(self._decode_token(req))
        except TokenError as exc:
            logger.warning('AUDIT -- {}'.format(exc))
        else:
            message = {
                'method': req.method,
                'action': '{}_{}_{}'.format(resource.__class__.__name__, req.method, req.path),
                'endpoint': req.path,
                'username': user.username,
                'organization_uuid': user.organization,
                'roles': user.roles,
                'groups': user.groups,
                'status': res.status
            }
            schema = AuditSchema()
            send_ts_task('audit.data', schema, schema.dump(message).data, expires=self.audit_msg_exp)

    def func_validate(self, token_data, permission):
        role_uuids = token_data.get('roles')
        return self.datastore.is_permission_in_roles(
            permission_string=permission, role_uuids=role_uuids
        )

    def _decode_token(self, request):
        token = _get_token(request)
        if not self.jwks.get('keys'):
            raise AuthJwksNotSet('There are no JWKs in the JWK set provided or the set is not structured properly')
        return decode_token(token, self.jwks, leeway=self.expiration_leeway)

    def _validate_permission(self, token_data):
        if self.with_permission:
            permissions.validate_permission(token_data, self.with_permission, self.service_name, self.func_validate)
        else:
            logger.error('Route with auth but no permission')


def _get_token(request):
    token = request.get_header(TOKEN_HEADER)
    if token is None:
        raise TokenHeaderMissing()
    return token


def _bad_token(error):
    body = json.dumps({'message': str(error)})
    return falcon.HTTPStatus(falcon.HTTP_401, body=body)
