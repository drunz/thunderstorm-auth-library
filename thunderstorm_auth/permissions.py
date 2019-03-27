from collections.abc import Mapping
import logging

from celery import current_app, signals, shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from statsd.defaults.env import statsd

from thunderstorm_auth.exceptions import (InsufficientPermissions, BrokenTokenError)


logger = get_task_logger(__name__)
logger.setLevel(logging.INFO)

PERMISSIONS_NEW = 'permissions.new'
PERMISSIONS_DELETE = 'permissions.delete'
MESSAGING_EXCHANGE = 'ts.messaging'
_REGISTERED_PERMISSIONS = set()


class PermissionMixin(object):
    @declared_attr
    def __tablename__(cls):
        return 'permission'

    uuid = Column(UUID(as_uuid=True), primary_key=True)
    service_name = Column(String(255), nullable=False)
    permission = Column(String(255), nullable=False, unique=True)
    is_deleted = Column(Boolean(), nullable=False, server_default='false')
    is_sent = Column(Boolean(), nullable=False, server_default='false')


# TODO @shipperizer swap this for the PermissionMixin
class Permission:
    __tablename__ = 'permission'

    uuid = Column(UUID(as_uuid=True), primary_key=True)
    service_name = Column(String(255), nullable=False)
    permission = Column(String(255), nullable=False, unique=True)
    is_deleted = Column(Boolean(), nullable=False, server_default='false')
    is_sent = Column(Boolean(), nullable=False, server_default='false')


def validate_permission(token_data, permission, service_name, func_validate):
    """Validate a permission is present in a token string

    Args:
        token_data (dict): The data from the auth token
        permission (str): The permission string required
        service_name (str): The name of the service
        func_validate (callable): function that will validate the permission, needs to
                                  accept token_data and permission string as params

    Raises:
        BrokenTokenError: If the token data is not valid
        InsufficientPermissions: If the token does not contain the required
                                 permission
    """
    if not isinstance(token_data, Mapping):
        raise BrokenTokenError('Token data must be structured as a dict')
    elif not isinstance(token_data.get('roles'), list):
        raise BrokenTokenError('Token roles must be structured as a list')
    elif not func_validate(token_data, permission):
        raise InsufficientPermissions('You do not have the permission required to carry out this action')


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


def _init_permission_tasks(datastore):
    """
    Create and init shared task for handling permissions, no need to register them as they are
    shared_task

    Creates a task which is not registered with any app. The task should be
    created and registered to an app using `thunderstorm_auth.setup.init_permissions`.

    Args:
        datastore (AuthDatastore): datastore object from the thunderstorm-auth library

    Returns:
        list: tasks needed for handling permissions
    """
    @signals.worker_ready.connect
    def do_ready(sender, **kwargs):
        if 'ts_auth.permissions.sync' in sender.app.tasks:
            sender.app.tasks['ts_auth.permissions.sync'].delay()

    @shared_task(name='ts_auth.permissions.sync')
    @statsd.timer('tasks.handle_sync_permissions.time')
    def handle_sync_permissions():
        # TODO @shipperizer move it to an internal function in the datastore
        permissions = datastore.db_session.query(
            datastore.permission_model
        ).filter(
            datastore.permission_model.is_sent == False
        )

        for permission in permissions:
            if permission.is_deleted:
                logger.info('deleting permission {}'.format(permission.uuid))
                current_app.send_task(
                    PERMISSIONS_DELETE,
                    (permission.uuid, ),
                    exchange=MESSAGING_EXCHANGE,
                    routing_key=PERMISSIONS_DELETE,
                )
            else:
                logger.info('adding permission {}'.format(permission.uuid))
                current_app.send_task(
                    PERMISSIONS_NEW,
                    (permission.uuid, permission.service_name, permission.permission),
                    exchange=MESSAGING_EXCHANGE,
                    routing_key=PERMISSIONS_NEW,
                )

            permission.is_sent = True
            datastore.commit()


    return [handle_sync_permissions]
