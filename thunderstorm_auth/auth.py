from functools import wraps

from flask import current_app, jsonify, request
import jwt


def get_decoded_token(token, secret_key=None, leeway=0):
    """
    JWT decoding method

    :params
       token - :str token to decode
       secret_key - :str shared secret key used to decode the token
       leeway - :int amount of seconds of difference allowed to the expiration time
    :raise BrokenTokenError, ExpiredTokenError
    :return :dict payload stored in the token
    """
    try:
        jwt_payload = jwt.decode(token, secret_key, leeway=leeway)

    except jwt.exceptions.ExpiredSignatureError:
        raise ExpiredTokenError(message='need reauthentication, expired JWT token {}'.format(token))
    except jwt.exceptions.DecodeError:
        raise BrokenTokenError(message='validation failed on JWT token {}'.format(token))

    return jwt_payload


# -------------------------------------------------------------- #
# Flask Decorator
# -------------------------------------------------------------- #

def decode_token(token):
    """
    Helper for the flask decorator
    wraps get_decoded_token exceptions in flask-type errors
    """
    auth_secret_key = current_app.config.get('TS_AUTH_SECRET_KEY')
    leeway = current_app.config.get('TS_AUTH_LEEWAY', 0)

    if auth_secret_key is None:
        raise AuthSecretKeyNotSet('flask app has not got TS_AUTH_SECRET_KEY set in the config')

    return get_decoded_token(token, auth_secret_key, leeway)


def ts_auth_required(func):
    """
    Flask decorator to check the authentication token <thunderstorm-key>
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Thunderstorm-Key')

        try:
            decode_token(token)

        except BaseTokenError as e:
            current_app.logger.error(e.message)
            return jsonify(message=e.message), 401
        else:
            return func(*args, **kwargs)

    return decorated_function


# -------------------------------------------------------------- #
# Exceptions
# -------------------------------------------------------------- #

class AuthSecretKeyNotSet(Exception):
    pass


class BaseTokenError(Exception):
    def __init__(self, message=None):
        self.message = str(message)


class BrokenTokenError(BaseTokenError):
    pass


class ExpiredTokenError(BaseTokenError):
    pass
