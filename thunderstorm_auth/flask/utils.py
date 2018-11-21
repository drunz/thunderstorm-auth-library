from flask import current_app, request

from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth import permissions
from thunderstorm_auth.exceptions import (
    TokenHeaderMissing, AuthJwksNotSet, InsufficientPermissions, Forbidden, Unauthorized
)


def _decode_token():
    token = _get_token()
    jwks = _get_jwks()
    leeway = current_app.config['TS_AUTH_LEEWAY']
    return decode_token(token, jwks, leeway)


def _get_token():
    token_header = current_app.config['TS_AUTH_TOKEN_HEADER']
    token = request.headers.get(token_header)
    if token is None:
        raise TokenHeaderMissing()
    return token


def _get_jwks():
    try:
        current_app.config['TS_AUTH_JWKS']['keys']
        return current_app.config['TS_AUTH_JWKS']
    except KeyError:
        message = 'TS_AUTH_JWKS missing from Flask config or JWK set not structured correctly'
        raise AuthJwksNotSet(message)


# ##### # TODO @shipperizer use this for TSA-720 # ##### #
# def func_validate(token_data, permission):
#     role_uuids = token_data.get(roles)
#     return current_app.extensions['ts_auth'].datastore.is_permission_in_roles(
#         permission_string=permission, role_uuids=role_uuids
#     )


def _validate_permission(token_data, permission):
    if permission:
        service_name = current_app.config['TS_SERVICE_NAME']
        permissions.validate_permission(token_data, service_name, permission)
        # ##### # TODO @shipperizer use this for TSA-720 # ##### #
        # permissions.validate_permission(token_data, permission, func_validate)
    else:
        current_app.logger.error('Route with auth but no permission: {}'.format(request.path))


def _bad_token(error):
    current_app.logger.info(error)

    if isinstance(error, InsufficientPermissions):
        raise Forbidden('You do not have the required permission to carry out the requested action')
    else:
        raise Unauthorized('Invalid authentication token provided')
