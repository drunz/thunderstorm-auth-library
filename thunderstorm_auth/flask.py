from functools import wraps

from flask import g

from thunderstorm_auth import TOKEN_HEADER, DEFAULT_LEEWAY
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import ThunderstormAuthError
from thunderstorm_auth.exceptions import AuthSecretKeyNotSet
from thunderstorm_auth.exceptions import TokenError, TokenHeaderMissing

try:
    from flask import current_app, jsonify, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


EXTENSION_KEY = 'ts_auth'

FLASK_SECRET_KEY = 'TS_AUTH_SECRET_KEY'
FLASK_LEEWAY = 'TS_AUTH_LEEWAY'


def ts_auth_required(func):
    """Flask decorator to check the authentication token X-Thunderstorm-Key

    If token decode fails for any reason, an an error is logged and a 401
    Unauthorized is returned to the caller.

    Raises:
        ThunderstormAuthError: If Flask is not installed.
    """
    if not HAS_FLASK:
        raise ThunderstormAuthError(
            'Cannot decorate Flask route as Flask is not installed.'
        )

    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            g.token = _decode_token()
        except TokenError as error:
            return _bad_token(error)
        else:
            return func(*args, **kwargs)

    return decorated_function


def _decode_token():
    token = _get_token()
    secret_key = _get_secret_key()
    leeway = current_app.config.get(FLASK_LEEWAY, DEFAULT_LEEWAY)
    return decode_token(token, secret_key, leeway)


def _get_token():
    token = request.headers.get(TOKEN_HEADER)
    if token is None:
        raise TokenHeaderMissing()
    return token


def _get_secret_key():
    try:
        return current_app.config[FLASK_SECRET_KEY]
    except KeyError:
        raise AuthSecretKeyNotSet(
            '{} missing from Flask config'.format(FLASK_SECRET_KEY)
        )


def _bad_token(error):
    current_app.logger.error(error)
    return jsonify(message=str(error)), 401