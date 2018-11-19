from functools import wraps

from flask import g

from thunderstorm_auth import permissions
from thunderstorm_auth.exceptions import TokenError, ThunderstormAuthError, InsufficientPermissions
from thunderstorm_auth.user import User
from thunderstorm_auth.flask.utils import _validate_permission, _decode_token, _bad_token

try:
    import flask  # noqa
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
        raise ThunderstormAuthError('Cannot decorate Flask route as Flask is not installed.')

    if with_permission is not None:
        permissions.register_permission(with_permission)
    else:
        raise ThunderstormAuthError('Route with auth but no permission is not allowed.')

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
