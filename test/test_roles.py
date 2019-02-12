from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from test.models import Role, RolePermissionAssociation


def test_create_role_if_not_exists_task_succeed_and_create_role(db_session, celery, fixtures):
    create_role_if_not_exists = celery.tasks['thunderstorm_auth.roles.create_role_if_not_exists']

    role_uuid = uuid4()

    assert create_role_if_not_exists(role_uuid, 'test')

    assert 'test' == db_session.query(Role.type).filter(Role.uuid == role_uuid).scalar()


def test_create_role_if_not_exists_task_succeed_if_role_exists(db_session, celery, fixtures):
    create_role_if_not_exists = celery.tasks['thunderstorm_auth.roles.create_role_if_not_exists']
    role = fixtures.Role()

    assert db_session.query(Role).count() == 1

    create_role_if_not_exists(role.uuid, 'test')

    assert db_session.query(Role).count() == 1


def test_create_role_permission_association_if_not_exists_task_succeed_and_create_association(db_session, celery, fixtures):
    create_role_permission_association_if_not_exists = celery.tasks['thunderstorm_auth.roles.create_role_permission_association_if_not_exists']
    role = fixtures.Role()
    permission = fixtures.Permission()

    assert not db_session.query(RolePermissionAssociation).count()

    role_uuid, permission_uuid = create_role_permission_association_if_not_exists(role.uuid, permission.uuid)

    assert db_session.query(RolePermissionAssociation).filter(
        RolePermissionAssociation.role_uuid == role_uuid, RolePermissionAssociation.permission_uuid == permission_uuid
    ).one()


def test_create_role_permission_association_if_not_exists_task_succeed_if_association_already_exists(db_session, celery, fixtures):
    create_role_permission_association_if_not_exists = celery.tasks['thunderstorm_auth.roles.create_role_permission_association_if_not_exists']
    role = fixtures.Role()
    permission = fixtures.Permission(roles=[role])

    assert db_session.query(RolePermissionAssociation).count() == 1

    role_uuid, permission_uuid = create_role_permission_association_if_not_exists(role.uuid, permission.uuid)

    assert db_session.query(RolePermissionAssociation).filter(
        RolePermissionAssociation.role_uuid == role_uuid, RolePermissionAssociation.permission_uuid == permission_uuid
    ).one()
    assert db_session.query(RolePermissionAssociation).count() == 1


def test_create_role_permission_association_if_not_exists_task_return_false_if_no_permission(db_session, celery, fixtures):
    create_role_permission_association_if_not_exists = celery.tasks['thunderstorm_auth.roles.create_role_permission_association_if_not_exists']
    role = fixtures.Role()

    assert not db_session.query(RolePermissionAssociation).count()

    assert not create_role_permission_association_if_not_exists(role.uuid, uuid4())

    assert not db_session.query(RolePermissionAssociation).count()


def test_create_role_permission_association_if_not_exists_task_raises_if_no_role(db_session, celery, fixtures):
    create_role_permission_association_if_not_exists = celery.tasks['thunderstorm_auth.roles.create_role_permission_association_if_not_exists']
    permission = fixtures.Permission()

    assert not db_session.query(RolePermissionAssociation).count()

    with pytest.raises(IntegrityError):
        create_role_permission_association_if_not_exists(uuid4(), permission.uuid)

    assert not db_session.query(RolePermissionAssociation).count()


def test_remove_role_orphan_permission_associations_none_permissions(db_session, celery, fixtures):
    remove_role_orphan_permission_associations = celery.tasks['thunderstorm_auth.roles.remove_role_orphan_permission_associations']
    role = fixtures.Role()
    permission = fixtures.Permission(roles=[role])

    assert db_session.query(RolePermissionAssociation).count() == 1

    remove_role_orphan_permission_associations(role.uuid, [])

    assert not db_session.query(RolePermissionAssociation).get((role.uuid, permission.uuid))
    assert not db_session.query(RolePermissionAssociation).count()


def test_remove_role_orphan_permission_associations_removes_stale_permissions(db_session, celery, fixtures):
    remove_role_orphan_permission_associations = celery.tasks['thunderstorm_auth.roles.remove_role_orphan_permission_associations']
    role = fixtures.Role()
    permissions = [fixtures.Permission(roles=[role]) for i in range(10)]

    assert db_session.query(RolePermissionAssociation).count() == 10
    remove_role_orphan_permission_associations(role.uuid, [{'uuid': str(p.uuid)} for p in permissions[:5]])

    assert db_session.query(RolePermissionAssociation).count() == 5
    assert db_session.query(RolePermissionAssociation).get((role.uuid, permissions[0].uuid))
    assert not db_session.query(RolePermissionAssociation).get((role.uuid, permissions[5].uuid))
    assert not db_session.query(RolePermissionAssociation).get((role.uuid, permissions[6].uuid))
    assert not db_session.query(RolePermissionAssociation).get((role.uuid, permissions[7].uuid))
    assert not db_session.query(RolePermissionAssociation).get((role.uuid, permissions[8].uuid))
    assert not db_session.query(RolePermissionAssociation).get((role.uuid, permissions[9].uuid))
