import json

import jwt

from thunderstorm_auth import DEFAULT_LEEWAY
from thunderstorm_auth.exceptions import ExpiredTokenError, BrokenTokenError


def decode_token(token, jwks, leeway=DEFAULT_LEEWAY):
    """Decode and extract data from a JWT.

    Args:
        token (str): Token data to decode.
        jwks (dict): JWK Set containing JWKs to be tried to decode the token.
        leeway (int): Number of seconds of lenience used in determining if a
            token has expired.

    Returns:
         dict payload stored in the token

    Raises:
        ExpiredTokenError: If the token has expired.
        BrokenTokenError: If the token is malformed.
    """
    try:
        key_id = get_signing_key_id_from_jwt(token)

        key_object = get_public_key_from_jwk(jwks['keys'][key_id])

        return jwt.decode(
            jwt=token,
            key=key_object,
            leeway=leeway,
            algorithms=['RS512']
        )

    except jwt.exceptions.ExpiredSignatureError:
        raise ExpiredTokenError(
            'Auth token expired. Please retry with a new token.'
        )
    except jwt.exceptions.DecodeError as ex:
        raise BrokenTokenError(
            'Token authentication failed due to a malformed token or incorrect JWK.'
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


def get_signing_key_id_from_jwt(token):
    """
    Match a token to a particular JWK based on kid (Key ID)

    Args:
        token (str): Signed token from the user service

    Returns:
        str: The kid of of the JWK used to sign the token.
    """
    # the outputs are payload, signing_input, header, signature
    token_contents = jwt.PyJWS()._load(token)

    token_header = token_contents[2]

    return token_header['kid']
