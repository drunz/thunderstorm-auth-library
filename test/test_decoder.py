import pytest

from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth.exceptions import ExpiredTokenError, BrokenTokenError


def test_get_decoded_token_returns_if_jwt_valid(valid_token, secret_key):
    assert decode_token(valid_token, secret_key)


def test_get_decoded_token_raises_if_jwt_invalid(invalid_token, secret_key):
    with pytest.raises(BrokenTokenError):
        decode_token(invalid_token, secret_key)


def test_get_decoded_token_raises_if_jwt_expired(expired_token, secret_key):
    with pytest.raises(ExpiredTokenError):
        decode_token(expired_token, secret_key)


def test_get_decoded_token_does_not_raise_if_jwt_expired_but_leeway_is_set(
        expired_token, secret_key):
    assert decode_token(expired_token, secret_key, leeway=3600)
