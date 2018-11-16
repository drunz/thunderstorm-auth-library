from unittest import mock

import pytest

from thunderstorm_auth.permissions import (
    validate_permission, get_registered_permissions, register_permission, get_permissions_info, Permission
)
from thunderstorm_auth.exceptions import (BrokenTokenError, InsufficientPermissions)


@pytest.mark.parametrize(
    'token_data,message', [
        ('', 'token data is not a mapping'),
        ({}, 'no permissions key'),
        ({'permissions': ''}, 'permissions is not a mapping'),
    ]
)
def test_validate_permission_fails_with_invalid_token(token_data, message):
    with pytest.raises(BrokenTokenError, message=message):
        validate_permission(token_data, None, None)


@pytest.mark.parametrize(
    'permissions,message', [
        ({}, 'no permissions'),
        ({'test-service': ['other-perm']}, 'right service wrong permission'),
        ({'other': ['test-permission']}, 'wrong service right permission'),
    ]
)
def test_validate_permission_fails_with_insufficient_permissions(permissions, message):
    with pytest.raises(InsufficientPermissions, message=message):
        token_data = {
            'username': 'test-user',
            'permissions': permissions,
        }
        validate_permission(token_data, 'test-service', 'test-permission')


def test_validate_permission_passes():
    token_data = {'username': 'test-user', 'permissions': {'test-service': ['one-permission', 'test-permission']}}
    validate_permission(token_data, 'test-service', 'test-permission')


def test_register_permission():
    assert 'my-test-register-permission' not in get_registered_permissions()
    register_permission('my-test-register-permission')
    assert 'my-test-register-permission' in get_registered_permissions()


def make_permission(uuid, permission, is_deleted, service_name='test'):
    p = Permission()
    p.uuid = uuid
    p.service_name = service_name
    p.permission = permission
    p.is_deleted = is_deleted
    return p


@mock.patch('thunderstorm_auth.permissions.get_registered_permissions')
def test_get_permissions_info(mock_get_registered_permissions):
    # arrange
    registered_permissions = ['perm1', 'perm3', 'perm4']
    db_permissions = [
        make_permission(uuid='e42b63b0-1014-11e8-bd6c-4a0004692f50', permission='perm1', is_deleted=False),
        make_permission(uuid='03a019de-1015-11e8-a5a0-4a0004692f50', permission='perm2', is_deleted=False),
        make_permission(uuid='3a2f335e-1015-11e8-9a86-4a0004692f50', permission='perm3', is_deleted=True)
    ]

    db_session = mock.Mock()
    db_session.query.return_value.all.return_value = db_permissions
    mock_get_registered_permissions.return_value = registered_permissions

    # act
    info = get_permissions_info(db_session, Permission)

    # assert
    assert info == {
        'registered': registered_permissions,
        'db': db_permissions,
        'to_insert': ['perm4'],
        'to_undelete': ['3a2f335e-1015-11e8-9a86-4a0004692f50'],
        'to_delete': ['03a019de-1015-11e8-a5a0-4a0004692f50'],
    }
