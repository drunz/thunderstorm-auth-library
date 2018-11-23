from unittest.mock import patch, MagicMock
from uuid import UUID

import pytest

from thunderstorm_auth.permissions import (
    validate_permission, get_registered_permissions, register_permission, get_permissions_info
)
from thunderstorm_auth.exceptions import BrokenTokenError

from test.models import Permission


@pytest.mark.parametrize(
    'token_data,message', [
        ('', 'token data is not a mapping'),
        ({}, 'no roles key'),
        ({'roles': ''}, 'roles is not a list'),
    ]
)
def test_validate_permission_fails_with_invalid_token(token_data, message):
    with pytest.raises(BrokenTokenError, message=message):
        validate_permission(token_data, None, None, MagicMock())


def test_validate_permission_calls_func_validate(role_uuid):
    token_data = {'username': 'test-user', 'roles': [str(role_uuid)]}
    m_func_validate = MagicMock()
    validate_permission(token_data, 'test-permission', 'test-service', m_func_validate)

    m_func_validate.assert_called_with(token_data, 'test-permission')


def test_register_permission():
    assert 'my-test-register-permission' not in get_registered_permissions()
    register_permission('my-test-register-permission')
    assert 'my-test-register-permission' in get_registered_permissions()


@patch('thunderstorm_auth.permissions.get_registered_permissions')
def test_get_permissions_info(mock_get_registered_permissions, db_session, fixtures):
    # arrange
    permissions = [
        fixtures.Permission(
            uuid=UUID('e42b63b0-1014-11e8-bd6c-4a0004692f50'),
            permission='perm1',
            service_name='test',
            is_deleted=False
        ),
        fixtures.Permission(
            uuid=UUID('03a019de-1015-11e8-a5a0-4a0004692f50'),
            permission='perm2',
            service_name='test',
            is_deleted=False
        ),
        fixtures.Permission(
            uuid=UUID('3a2f335e-1015-11e8-9a86-4a0004692f50'),
            permission='perm3',
            service_name='test',
            is_deleted=True
        )
    ]
    mock_get_registered_permissions.return_value = ['perm1', 'perm3', 'perm4']

    # act
    info = get_permissions_info(db_session, Permission)

    # assert
    assert info == {
        'registered': ['perm1', 'perm3', 'perm4'],
        'db': permissions,
        'to_insert': ['perm4'],
        'to_undelete': [UUID('3a2f335e-1015-11e8-9a86-4a0004692f50')],
        'to_delete': [UUID('03a019de-1015-11e8-a5a0-4a0004692f50')],
    }
