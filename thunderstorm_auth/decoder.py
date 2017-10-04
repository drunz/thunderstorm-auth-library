import jwt

from thunderstorm_auth import DEFAULT_LEEWAY
from thunderstorm_auth.exceptions import ExpiredTokenError, BrokenTokenError


def decode_token(token, secret_key, leeway=DEFAULT_LEEWAY):
    """
    JWT decoding method

    :params
       token - :str token to decode
       secret_key - :str shared secret key used to decode the token
       leeway - :int amount of seconds of difference allowed to the
                     expiration time
    :raise BrokenTokenError, ExpiredTokenError
    :return :dict payload stored in the token
    """
    try:
        return jwt.decode(
            jwt=token,
            key=secret_key,
            leeway=leeway
        )
    except jwt.exceptions.ExpiredSignatureError:
        raise ExpiredTokenError(
            'Auth token expired. Please retry with a new token.'
        )
    except jwt.exceptions.DecodeError:
        raise BrokenTokenError(
            'Token authentication failed.'
        )
