import pytest

from thunderstorm_auth.decoder import decode_token, get_kid_and_alg_headers_from_token
from thunderstorm_auth.exceptions import (ExpiredTokenError, BrokenTokenError, MissingKeyErrror, TokenDecodeError)


def test_decode_token_returns_if_jwt_valid(access_token, jwk_set):
    assert decode_token(access_token, jwk_set)


def test_decode_token_raises_if_jwt_malformed(malformed_token, jwk_set):
    with pytest.raises(BrokenTokenError):
        decode_token(malformed_token, jwk_set)


def test_decode_token_raises_if_jwt_headers_missing(token_with_no_headers, jwk_set):
    with pytest.raises(BrokenTokenError):
        decode_token(token_with_no_headers, jwk_set)


def test_decode_token_raises_if_jwt_expired(access_token_expired, jwk_set):
    with pytest.raises(ExpiredTokenError):
        decode_token(access_token_expired, jwk_set)


def test_decode_token_does_not_raise_if_jwt_expired_but_verify_exp_false(access_token_expired, jwk_set):
    assert decode_token(access_token_expired, jwk_set, options={'verify_exp': False})


def test_decode_token_does_not_raise_if_jwt_expired_but_leeway_is_set(access_token_expired, jwk_set):
    assert decode_token(access_token_expired, jwk_set, leeway=3605)


def test_decode_token_with_jwk_set_raises_broken_token_error_if_token_is_malformed(malformed_token, jwk_set):
    with pytest.raises(BrokenTokenError):
        decode_token(malformed_token, jwk_set, leeway=3605)


def test_decode_token_raises_missing_key_error_if_invalid_key_id_specified_in_jwk(access_token):
    with pytest.raises(MissingKeyErrror):
        decode_token(access_token, {})


def test_get_headers_from_token_returns_key_id_and_signing_algorithm(access_token, key_id):
    kid, alg = get_kid_and_alg_headers_from_token(access_token)
    assert kid == key_id
    assert alg == 'RS512'


def test_get_headers_from_token_raises_BrokenTokenError_if_headers_are_missing():
    with pytest.raises(BrokenTokenError):
        get_kid_and_alg_headers_from_token('not a token')


def test_decode_valid_token_with_invalid_key(token_signed_with_incorrect_key, jwk_set):
    with pytest.raises(TokenDecodeError):
        decode_token(token_signed_with_incorrect_key, jwk_set)
