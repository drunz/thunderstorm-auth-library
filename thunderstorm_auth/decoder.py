import json

import jwt
import jwt.algorithms

from thunderstorm_auth import DEFAULT_LEEWAY
from thunderstorm_auth.exceptions import (ExpiredTokenError, BrokenTokenError, MissingKeyErrror,
                                          TokenDecodeError)


def decode_token(token, jwks, leeway=DEFAULT_LEEWAY, options=None):
    """Decode and extract data from a JWT.

    Args:
        token (str): Token data to decode.
        jwks (dict): JWK Set containing JWKs to be tried to decode the token.
        leeway (int): Number of seconds of lenience used in determining if a
            token has expired.
        options (dict): Allow the caller to pass additional options to the
            decode method of pyjwt.

    Returns:
         dict payload stored in the token

    Raises:
        ExpiredTokenError: If the token has expired.
        BrokenTokenError: If the token is malformed.
        MissingKeyErrror: If the key_id in the token is not present in the JWK set provided.
    """
    try:
        key_id, algorithm = get_kid_and_alg_headers_from_token(token)

        public_key = get_public_key_from_jwk(jwks['keys'][key_id])

        return jwt.decode(
            token,
            key=public_key,
            leeway=leeway,
            algorithms=[algorithm],
            options=options
        )

    except jwt.exceptions.ExpiredSignatureError:
        raise ExpiredTokenError(
            'Auth token expired. Please retry with a new token.'
        )
    except jwt.exceptions.DecodeError as ex:
        raise TokenDecodeError('An error occurred while decoding your token: {}'.format(ex))
    except BrokenTokenError as ex:
        raise BrokenTokenError(ex)
    except KeyError:
        raise MissingKeyErrror(
            'The key_id specified in your token is not present in the JWK set provided.'
        )


def get_public_key_from_jwk(jwk):
    """
    Create an _RSAPublicKey object using the contents of a JWK

    Args:
        JWK (dict): Contains information which represents a public key

    Returns:
        _RSAPublicKey
    """
    jwk_str = json.dumps(jwk)
    return jwt.algorithms.RSAAlgorithm.from_jwk(jwk_str)


def get_kid_and_alg_headers_from_token(token):
    """
    Extract the kid and alg headers from a JWT

    Args:
        token (str): Signed token from the user service

    Returns:
        tuple: Tuple of strings containing the key_id and algorithm used for signing the JWT

    Raises:
        BrokenTokenError: If the JWT is malformed or missing required headers.
    """
    try:
        token_headers = jwt.PyJWS().get_unverified_header(token)
        return token_headers['kid'], token_headers['alg']
    except jwt.exceptions.DecodeError:
        msg = 'The token supplied is either malformed or missing required segments.'
    except KeyError:
        msg = 'Token authentication failed due to missing <kid> or <alg> token header'

    raise BrokenTokenError(msg)
