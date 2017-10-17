from functools import wraps

from flask import current_app, jsonify, request, g

from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import TokenError, AuthJwksNotSet, TokenHeaderMissing


def _decode_token(token):
    """
    Helper for the flask decorator
    wraps get_decoded_token exceptions in flask-type errors
    """
    # TODO @shipperizer move this to use the flask extension with the LocalProxy
    jwks = _get_jwks()
    leeway = current_app.config.get('TS_AUTH_LEEWAY')

    return decode_token(token, jwks, leeway)


def _get_token():
    token = request.headers.get(current_app.config.get('TS_AUTH_TOKEN_HEADER'))
    if token is None:
        raise TokenHeaderMissing()
    return token


def _get_jwks():
    try:
        return current_app.config['TS_AUTH_JWKS']
    except KeyError:
        raise AuthJwksNotSet('TS_AUTH_JWKS missing from Flask config')


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
