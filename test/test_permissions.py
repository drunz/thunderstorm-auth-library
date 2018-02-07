import pytest

from thunderstorm_auth.permissions import validate_permission
from thunderstorm_auth.exceptions import (
    BrokenTokenError, InsufficientPermissions
)


@pytest.mark.parametrize('token_data,message', [
    ('', 'token data is not a mapping'),
    ({}, 'no permissions key'),
    ({'permissions': ''}, 'permissions is not a mapping'),
])
def test_validate_permission_fails_with_invalid_token(token_data, message):
    with pytest.raises(BrokenTokenError, message=message):
        validate_permission(token_data, None, None)


@pytest.mark.parametrize('permissions,message', [
    ({}, 'no permissions'),
    ({'test-service': ['other-perm']}, 'right service wrong permission'),
    ({'other': ['test-permission']}, 'wrong service right permission'),
])
def test_validate_permission_fails_with_insufficient_permissions(
    permissions, message
):
    with pytest.raises(InsufficientPermissions, message=message):
        token_data = {
            'username': 'test-user',
            'permissions': permissions,
        }
        validate_permission(token_data, 'test-service', 'test-permission')


def test_validate_permission_passes():
    token_data = {
        'username': 'test-user',
        'permissions': {
            'test-service': ['one-permission', 'test-permission']
        }
    }
    validate_permission(token_data, 'test-service', 'test-permission')
