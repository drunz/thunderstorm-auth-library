from functools import wraps

from flask import current_app, jsonify, request, g

from thunderstorm_auth import TOKEN_HEADER, DEFAULT_LEEWAY
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import TokenError, AuthSecretKeyNotSet, TokenHeaderMissing


FLASK_SECRET_KEY = 'TS_AUTH_SECRET_KEY'
FLASK_LEEWAY = 'TS_AUTH_LEEWAY'


def _decode_token(token):
    """
    Helper for the flask decorator
    wraps get_decoded_token exceptions in flask-type errors
    """
    # TODO @shipperizer move this to use the flask extension with the LocalProxy
    auth_secret_key = _get_secret_key()
    leeway = current_app.config.get(FLASK_LEEWAY, DEFAULT_LEEWAY)

    if auth_secret_key is None:
        raise AuthSecretKeyNotSet('TS_AUTH_SECRET_KEY missing from Flask config')

    return decode_token(token, auth_secret_key, leeway)


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


def ts_auth_required(func):
    """
    Flask decorator to check the authentication token X-Thunderstorm-Key

    If token decode fails for any reason, an an error is logged and a 401 Unauthorized
    is returned to the caller.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = token = _get_token()
        try:
            # store decoded token on request-bounded context g
            g.token = _decode_token(token)

        except TokenError as e:
            current_app.logger.error(e)
            return _bad_token(e)
        else:
            return func(*args, **kwargs)

    return decorated_function
