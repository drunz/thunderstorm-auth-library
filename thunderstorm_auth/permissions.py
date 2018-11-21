from collections.abc import Mapping
import warnings

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr

from thunderstorm_auth.exceptions import (InsufficientPermissions, BrokenTokenError)

_REGISTERED_PERMISSIONS = set()


def validate_permission(token_data, service_name, permission):
    """Validate a permission is present in a token string

    Args:
        token_data (dict): The data from the auth token
        service_name (str): The name of the service
        permission (str): The permission string required

    Raises:
        BrokenTokenError: If the token data is not valid
        InsufficientPermissions: If the token does not contain the required
                                 permission
    """
    warnings.warn('Token field `permissions` is being deprecated', DeprecationWarning)
    if not isinstance(token_data, Mapping):
        raise BrokenTokenError('Token data must be structured as a dict')
    elif not isinstance(token_data.get('permissions'), Mapping):
        raise BrokenTokenError('Token permissions must be structured as a dict')
    elif permission not in token_data['permissions'].get(service_name, []):
        raise InsufficientPermissions('You do not have the permission required to carry out this action')


# ##### # TODO @shipperizer use this for TSA-720 ##### #
# def validate_permission(token_data, permission, func_validate):
#     """Validate a permission is present in a token string
#
#     Args:
#         token_data (dict): The data from the auth token
#         permission (str): The permission string required
#         func_validate (callable): function that will validate the permission, needs to
#                                   accept token_data and permission string as params
#
#     Raises:
#         BrokenTokenError: If the token data is not valid
#         InsufficientPermissions: If the token does not contain the required
#                                  permission
#     """
#     if not isinstance(token_data, Mapping):
#         raise BrokenTokenError('Token data must be structured as a dict')
#     elif not isinstance(token_data.get('roles'), list):
#         raise BrokenTokenError('Token roles must be structured as a list')
#     elif not func_validate(token_data, permission):
#         raise InsufficientPermissions('You do not have the permission required to carry out this action')


def register_permission(permission):
    """Register a permission with the global store

    This is used to keep track of all permission strings used in the service.

    Args:
        permission (str): The permission string to register
    """
    _REGISTERED_PERMISSIONS.add(permission)


def get_registered_permissions():
    """Return all the permission strings registered so far

    Returns:
        set
    """
    return _REGISTERED_PERMISSIONS


def get_permissions_info(db_session, permission_model):
    """Get information about permissions for this service

    Includes;
        - permissions currently being used on routes
        - permissions in the database
        - permissions that need to be added (on routes but not in database)
        - permissions that need to be deleted (not on routes but in database)
        - permissions that need to be undeleted (on routes but deleted in
          database)

    Returns:
        dict
    """
    registered_permissions = get_registered_permissions()
    db_permissions = db_session.query(permission_model).all()

    to_insert = []
    to_undelete = []
    to_delete = [perm.uuid for perm in db_permissions]

    for reg_perm in registered_permissions:
        found = False
        for db_perm in db_permissions:
            if db_perm.permission == reg_perm:
                found = True
                to_delete.remove(db_perm.uuid)
                if db_perm.is_deleted:
                    to_undelete.append(db_perm.uuid)

        if not found:
            to_insert.append(reg_perm)

    return {
        'registered': registered_permissions,
        'db': db_permissions,
        'to_insert': to_insert,
        'to_undelete': to_undelete,
        'to_delete': to_delete,
    }


def create_permission_model(base):
    """Create an SQLAlchemy Permission

    This is intended to be used in apps that have permissions.

    Args:
        base (Base): Declarative base of database schema to add model to.

    Returns:
        SQLAlchemy Permission model
    """

    return type(
        'Permission', (base, ), {
            key: value
            for key, value in Permission.__dict__.items()
            if not key.startswith('__') or key == '__tablename__'
        }
    )


class PermissionMixin(object):
    @declared_attr
    def __tablename__(cls):
        return 'permission'

    uuid = Column(UUID(as_uuid=True), primary_key=True)
    service_name = Column(String(255), nullable=False)
    permission = Column(String(255), nullable=False, unique=True)
    is_deleted = Column(Boolean(), nullable=False, server_default='false')
    is_sent = Column(Boolean(), nullable=False, server_default='false')


class Permission:
    __tablename__ = 'permission'

    uuid = Column(UUID(as_uuid=True), primary_key=True)
    service_name = Column(String(255), nullable=False)
    permission = Column(String(255), nullable=False, unique=True)
    is_deleted = Column(Boolean(), nullable=False, server_default='false')
    is_sent = Column(Boolean(), nullable=False, server_default='false')
