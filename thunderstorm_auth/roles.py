from celery import shared_task, group, chain
import marshmallow  # TODO: @will-norris backwards compat - remove
from marshmallow import fields, Schema
from marshmallow.exceptions import ValidationError
from statsd.defaults.env import statsd
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


MARSHMALLOW_2 = int(marshmallow.__version__[0]) < 3


class PermissionSchema(Schema):
    uuid = fields.UUID(required=True, allow_none=False)
    service = fields.String(required=True, allow_none=False)
    permission_string = fields.String(required=True, allow_none=False)


class RoleSchema(Schema):
    uuid = fields.UUID(required=True, allow_none=False)
    type = fields.String(required=True, allow_none=False)
    permissions = fields.List(fields.Nested(PermissionSchema), required=True)


class RolePermissionAssociationMixin(object):
    @declared_attr
    def __tablename__(cls):
        return 'role_permission_association'

    @declared_attr
    def role_uuid(cls):
        return Column(UUID(as_uuid=True), ForeignKey('role.uuid', ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def permission_uuid(cls):
        return Column(UUID(as_uuid=True), ForeignKey('permission.uuid', ondelete='CASCADE'), primary_key=True)


class RoleMixin(object):
    @declared_attr
    def __tablename__(cls):
        return 'role'

    uuid = Column(UUID(as_uuid=True), primary_key=True)
    type = Column(String(), unique=True, nullable=False)

    @declared_attr
    def permissions(cls):
        return relationship('Permission', secondary='role_permission_association', backref='roles')


def _init_role_tasks(datastore):
    """
    Create and init shared task for handling roles, no need to register thema s they are
    shared_task

    Creates a task which is not registered with any app. The task should be
    created and registered to an app using `thunderstorm_auth.setup.init_group_sync_tasks`.

    Args:
        datastore (AuthDatastore): datastore object from the thunderstorm-auth library

    Returns:
        list: tasks needed for handling roles and role associations
    """

    @shared_task
    @statsd.timer('tasks.create_role_if_not_exists.time')
    def create_role_if_not_exists(role_uuid, role_type):
        """
        Create a role if not already in the db

        Args:
            role_uuid (uuid): primary identifier of a role
            role_type (str): type of a role
        """
        role = datastore.get_role(role_uuid)

        if not role:
            datastore.create_role(role_uuid, role_type, commit=True)

        return role_uuid

    @shared_task
    @statsd.timer('tasks.create_role_permission_association_if_not_exists.time')
    def create_role_permission_association_if_not_exists(role_uuid, permission_uuid):
        """
        Create a role-permission association if not already in the db

        Args:
            role_uuid (uuid): primary identifier of a role
            permission_uuid (uuid): primary identifier of a permission
        """
        permission = datastore.get_permission(permission_uuid)

        if not permission:
            # nothing to do for permissions of other services
            # TODO @shipperizer maybe return a tuple to be consistent with the output
            return False

        datastore.create_role_permission_association(role_uuid, permission_uuid, commit=True)

        return (role_uuid, permission_uuid)

    @shared_task
    @statsd.timer('tasks.create_role_permission_associations_if_not_exist.time')
    def create_role_permission_associations_if_not_exist(role_uuid, permissions):
        """
        Trigger tasks to create role-permission associations if not already in the db

        Args:
            role_uuid (uuid): primary identifier of a role
            permissions (dict): dictionary of permission objects
        """
        return group([create_role_permission_association_if_not_exists.si(role_uuid, permission['uuid']) for permission in permissions])()


    @shared_task
    @statsd.timer('tasks.remove_role_orphan_permission_associations.time')
    def remove_role_orphan_permission_associations(role_uuid, permissions):
        """
        Trigger tasks to remove role-permission associations if no more linked to the role

        Args:
            role_uuid (uuid): primary identifier of a role
            permissions (dict): dictionary of permission objects
        """
        permission_uuids = {str(permission['uuid']) for permission in permissions}

        role_permission_uuids = {str(p.uuid) for p in datastore.get_role_permissions(role_uuid)}

        orphan_uuids = role_permission_uuids - permission_uuids

        return [
            datastore.delete_role_permission_association(role_uuid, orphan_uuid, commit=True)
            for orphan_uuid in orphan_uuids
        ]

    # TODO @shipperizer restructure tasks.py and put this into it
    # TODO @shipperizer make this a ts_task from thunderstorm-messagging
    @shared_task(name='handle_role_data')
    @statsd.timer('tasks.handle_role_data.time')
    def handle_role_data(payload):
        # TODO @shipperizer remove this when using ts_task decorator
        payload = payload.get('data')
        if not payload:
            raise NotImplementedError

        # TODO @ship[perizer backwards compat - remove
        if MARSHMALLOW_2:
            data, errors = RoleSchema().load(payload)
            if errors:
                # TODO @shipperizer raise a proper exception
                raise NotImplementedError
        else:
            try:
                data = RoleSchema().load(payload)
            except ValidationError:
                # TODO @shipperizer raise a proper exception
                raise NotImplementedError

        chain(
            create_role_if_not_exists.si(data['uuid'], data['type']),
            remove_role_orphan_permission_associations.si(data['uuid'], data['permissions']),
            create_role_permission_associations_if_not_exist.si(data['uuid'], data['permissions'])
        )()

    return [handle_role_data, create_role_if_not_exists, remove_role_orphan_permission_associations, create_role_permission_associations_if_not_exist, create_role_permission_association_if_not_exists]


def _role_task_routing_key():
    """
    Routing key for role tasks
    """
    return 'role.data'
