import jwt

from thunderstorm_auth import DEFAULT_LEEWAY
from thunderstorm_auth.exceptions import ExpiredTokenError, BrokenTokenError


def decode_token(token, secret_key, leeway=DEFAULT_LEEWAY):
    """Decode and extract data from a JWT.

    Args:
        token (str): Token data to decode.
        secret_key (str): Shared secret key used to decode the token.
        leeway (int): Number of seconds of lenience used in determining if a
            token has expired.

    Returns:
         dict payload stored in the token

    Raises:
        ExpiredTokenError: If the token has expired.
        BrokenTokenError: If the token is malformed.
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
