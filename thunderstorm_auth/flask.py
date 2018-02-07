from functools import wraps

from flask import g

from thunderstorm_auth import TOKEN_HEADER, DEFAULT_LEEWAY
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.permissions import validate_permission
from thunderstorm_auth.exceptions import (
    TokenError, TokenHeaderMissing, AuthJwksNotSet, ThunderstormAuthError,
    ExpiredTokenError, InsufficientPermissions
)
from thunderstorm_auth.user import User

try:
    from flask import current_app, jsonify, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


FLASK_JWKS = 'TS_AUTH_JWKS'
FLASK_LEEWAY = 'TS_AUTH_LEEWAY'


def ts_auth_required(func=None, *, with_permission=None):
    """Flask decorator to check the authentication token X-Thunderstorm-Key

    If token decode fails for any reason, an an error is logged and a 401
    Unauthorized is returned to the caller.

    Args:
        func (Callable):       View to decorate
        with_permission (str): Permission string required for this view

    Raises:
        ThunderstormAuthError: If Flask is not installed.
    """
    if not HAS_FLASK:
        raise ThunderstormAuthError(
            'Cannot decorate Flask route as Flask is not installed.'
        )

    def wrapper(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            try:
                decoded_token_data = _decode_token()
                _validate_permission(decoded_token_data, with_permission)
            except (TokenError, InsufficientPermissions) as error:
                return _bad_token(error)

            g.user = User.from_decoded_token(decoded_token_data)
            return func(*args, **kwargs)

        return decorated_function

    if callable(func):
        return wrapper(func)
    elif func is None:
        return wrapper
    else:
        raise ThunderstormAuthError('Non-callable provided for decorator')


def _decode_token():
    token = _get_token()
    jwks = _get_jwks()
    leeway = current_app.config.get(FLASK_LEEWAY, DEFAULT_LEEWAY)
    return decode_token(token, jwks, leeway)


def _get_token():
    token = request.headers.get(TOKEN_HEADER)
    if token is None:
        raise TokenHeaderMissing()
    return token


def _get_jwks():
    try:
        current_app.config[FLASK_JWKS]['keys']
        return current_app.config[FLASK_JWKS]
    except KeyError:
        message = (
            '{} missing from Flask config or JWK set not structured '
            'correctly'
        ).format(FLASK_JWKS)

        raise AuthJwksNotSet(message)


def _validate_permission(token_data, permission):
    if permission:
        service_name = current_app.config['TS_AUTH_SERVICE_NAME']
        validate_permission(token_data, service_name, permission)


def _bad_token(error):
    if isinstance(error, ExpiredTokenError):
        current_app.logger.info(error)
    else:
        current_app.logger.error(error)
    status_code = 403 if isinstance(error, InsufficientPermissions) else 401
    return jsonify(message=str(error)), status_code
