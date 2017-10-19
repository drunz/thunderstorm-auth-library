import pytest

from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import ExpiredTokenError, BrokenTokenError


def test_get_decoded_token_returns_if_jwt_valid(valid_token, jwk_set):
    assert decode_token(valid_token, jwk_set)


def test_get_decoded_token_raises_if_jwt_invalid(invalid_token, jwk_set):
    with pytest.raises(BrokenTokenError):
        decode_token(invalid_token, jwk_set)


def test_get_decoded_token_raises_if_jwt_expired(expired_token, jwk_set):
    with pytest.raises(ExpiredTokenError):
        decode_token(expired_token, jwk_set)


def test_get_decoded_token_does_not_raise_if_jwt_expired_but_leeway_is_set(
        expired_token, jwk_set):
    assert decode_token(expired_token, jwk_set, leeway=3605)


def test_get_decoded_token_with_jwk_set_raises_broken_token_error_if_token_is_malformed(
        invalid_token, jwk_set):
    with pytest.raises(BrokenTokenError):
        decode_token(invalid_token, jwk_set, leeway=3605)
