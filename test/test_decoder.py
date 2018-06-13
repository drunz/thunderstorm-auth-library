import pytest

from thunderstorm_auth.decoder import decode_token, get_kid_and_alg_headers_from_token
from thunderstorm_auth.exceptions import (ExpiredTokenError, BrokenTokenError, MissingKeyErrror,
                                          TokenDecodeError)


def test_decode_token_returns_if_jwt_valid(valid_token, jwk_set):
    assert decode_token(valid_token, jwk_set)


def test_decode_token_raises_if_jwt_invalid(invalid_token, jwk_set):
    with pytest.raises(BrokenTokenError):
        decode_token(invalid_token, jwk_set)


def test_decode_token_raises_if_jwt_headers_invalid(invalid_token_no_headers, jwk_set):
    with pytest.raises(BrokenTokenError):
        decode_token(invalid_token_no_headers, jwk_set)


def test_decode_token_raises_if_jwt_expired(expired_token, jwk_set):
    with pytest.raises(ExpiredTokenError):
        decode_token(expired_token, jwk_set)


def test_decode_token_does_not_raise_if_jwt_expired_but_verify_exp_false(
    expired_token, jwk_set
):
    assert decode_token(expired_token, jwk_set, options={'verify_exp': False})


def test_decode_token_does_not_raise_if_jwt_expired_but_leeway_is_set(
        expired_token, jwk_set):
    assert decode_token(expired_token, jwk_set, leeway=3605)


def test_decode_token_with_jwk_set_raises_broken_token_error_if_token_is_malformed(
        invalid_token, jwk_set):
    with pytest.raises(BrokenTokenError):
        decode_token(invalid_token, jwk_set, leeway=3605)


def test_decode_token_raises_missing_key_error_if_invalid_key_id_specified_in_jwk(valid_token):
    with pytest.raises(MissingKeyErrror):
        decode_token(valid_token, {})


def test_get_headers_from_token_returns_key_id_and_signing_algorithm(valid_token, key_id):
    kid, alg = get_kid_and_alg_headers_from_token(valid_token)
    assert kid == key_id
    assert alg == 'RS512'


def test_get_headers_from_token_raises_BrokenTokenError_if_headers_are_missing():
    with pytest.raises(BrokenTokenError):
        get_kid_and_alg_headers_from_token('not a token')


def test_decode_valid_token_with_invalid_key(valid_token_signed_with_incorrect_key, jwk_set):
    with pytest.raises(TokenDecodeError):
        decode_token(valid_token_signed_with_incorrect_key, jwk_set)
