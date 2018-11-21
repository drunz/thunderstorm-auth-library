from datetime import datetime
from os import environ
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.query import Query
from werkzeug.contrib.cache import BaseCache, SimpleCache, RedisCache, MemcachedCache

from thunderstorm_auth.datastore import SQLAlchemySessionAuthStore
from test.models import Role, Permission, RolePermissionAssociation


def test_sqlalchemy_auth_datastore_initialization(db_session):
    datastore = SQLAlchemySessionAuthStore(db_session, Role, Permission, RolePermissionAssociation)

    assert datastore.db_session == db_session
    assert datastore.role_model == Role
    assert datastore.permission_model == Permission
    assert datastore.association_model == RolePermissionAssociation
    assert isinstance(datastore.cache, SimpleCache)


def test_sqlalchemy_auth_datastore_initialization_with_wrong_cache(db_session):
    class FakeCache(object):
        pass

    with pytest.raises(NotImplementedError):
        SQLAlchemySessionAuthStore(db_session, Role, Permission, RolePermissionAssociation, cache=FakeCache())


@pytest.mark.parametrize('cache', [RedisCache(), MemcachedCache()])
def test_sqlalchemy_auth_datastore_initialization_with_basecache(cache, db_session):
    datastore = SQLAlchemySessionAuthStore(db_session, Role, Permission, RolePermissionAssociation, cache=cache)

    assert datastore.db_session == db_session
    assert datastore.role_model == Role
    assert datastore.permission_model == Permission
    assert datastore.association_model == RolePermissionAssociation
    assert datastore.cache == cache
    assert isinstance(datastore.cache, BaseCache)


def test_sqlalchemy_auth_datastore_get_role(datastore, fixtures):
    role = fixtures.Role()

    assert datastore.get_role(role.uuid) == role


def test_sqlalchemy_auth_datastore_get_roles(datastore, fixtures):
    roles = [fixtures.Role() for _ in range(5)]

    query = datastore.get_roles([r.uuid for r in roles[:2]])

    assert isinstance(query, Query)
    assert query.count() == 2
    assert query.all() == roles[:2]


def test_sqlalchemy_auth_datastore_get_role_permissions(datastore, fixtures):
    permissions = [fixtures.Permission() for _ in range(5)]
    role = fixtures.Role(permissions=permissions)

    query = datastore.get_role_permissions(role.uuid)

    assert isinstance(query, Query)
    assert query.all() == permissions


def test_sqlalchemy_auth_datastore_is_permission_in_roles_sets_cache(datastore, fixtures):
    roles = [fixtures.Role() for _ in range(150)]
    permission = fixtures.Permission(roles=roles[50:75])

    assert not datastore.cache.get(str(permission.uuid))

    assert datastore.is_permission_in_roles(permission_uuid=permission.uuid, role_uuids=[r.uuid for r in roles])

    assert datastore.cache.get(str(permission.uuid)) == {str(r.uuid) for r in roles[50:75]}


def test_sqlalchemy_auth_datastore_is_permission_in_roles_finds_permission_by_string(datastore, fixtures):
    roles = [fixtures.Role() for _ in range(150)]
    permission = fixtures.Permission(roles=roles[50:75])

    assert not datastore.cache.get(str(permission.uuid))

    assert datastore.is_permission_in_roles(
        permission_string=permission.permission, role_uuids=[r.uuid for r in roles]
    )

    assert datastore.cache.get(str(permission.uuid)) == {str(r.uuid) for r in roles[50:75]}


def test_sqlalchemy_auth_datastore_is_permission_in_roles_fails_if_no_role(datastore, fixtures):
    permission = fixtures.Permission()

    assert not datastore.is_permission_in_roles(
        permission_uuid=permission.uuid, role_uuids=[uuid4() for _ in range(10)]
    )


def test_sqlalchemy_auth_datastore_get_permission(datastore, fixtures):
    permission = fixtures.Permission()

    assert datastore.get_permission(permission.uuid) == permission


def test_sqlalchemy_auth_datastore_get_permissions(datastore, fixtures):
    permissions = [fixtures.Permission() for _ in range(5)]

    query = datastore.get_permissions([r.uuid for r in permissions[:2]])

    assert isinstance(query, Query)
    assert query.count() == 2
    assert query.all() == permissions[:2]


def test_sqlalchemy_auth_datastore_get_permission_roles(datastore, fixtures):
    permission = fixtures.Permission()
    roles = [fixtures.Role(permissions=[permission] + [fixtures.Permission() for _ in range(2)]) for _ in range(150)]
    [fixtures.Role() for _ in range(100)]

    query = datastore.get_permission_roles(permission.uuid)

    assert isinstance(query, Query)
    assert query.count() == 150
    assert query.all() == roles
    assert datastore.cache.get(str(permission.uuid)) == {str(r.uuid) for r in roles}


def test_sqlalchemy_auth_datastore_create_role_succeeds(datastore, db_session):
    role_uuid = datastore.create_role(uuid4(), 'superadmin', commit=True)

    assert db_session.query(Role).get(role_uuid)


def test_sqlalchemy_auth_datastore_create_role_fails_if_uuid_already_there(datastore, fixtures):
    role = fixtures.Role()

    with pytest.raises(IntegrityError):
        datastore.create_role(role.uuid, 'superadmin', commit=True)


def test_sqlalchemy_auth_datastore_create_role_fails_if_type_not_unique(datastore, fixtures):
    role = fixtures.Role()

    with pytest.raises(IntegrityError):
        datastore.create_role(uuid4(), role.type, commit=True)


def test_sqlalchemy_auth_datastore_create_role_permission_association_succeeds(datastore, db_session, fixtures):
    role = fixtures.Role()
    permission = fixtures.Permission()
    role_uuid, permission_uuid = datastore.create_role_permission_association(role.uuid, permission.uuid, commit=True)

    assert (role_uuid, permission_uuid) == (role.uuid, permission.uuid)
    assert db_session.query(RolePermissionAssociation).filter(
        RolePermissionAssociation.role_uuid == role_uuid, RolePermissionAssociation.permission_uuid == permission_uuid
    ).one()


def test_sqlalchemy_auth_datastore_create_role_permission_association_does_not_fail_if_previously_created(
        datastore, db_session, fixtures
):
    role = fixtures.Role()
    permission = fixtures.Permission(roles=[role] + [fixtures.Role() for _ in range(10)])

    assert db_session.query(RolePermissionAssociation).filter(
        RolePermissionAssociation.role_uuid == role.uuid, RolePermissionAssociation.permission_uuid == permission.uuid
    ).one()

    role_uuid, permission_uuid = datastore.create_role_permission_association(role.uuid, permission.uuid, commit=True)

    assert (role_uuid, permission_uuid) == (role.uuid, permission.uuid)
    assert db_session.query(RolePermissionAssociation).filter(
        RolePermissionAssociation.role_uuid == role_uuid, RolePermissionAssociation.permission_uuid == permission_uuid
    ).one()


def test_sqlalchemy_auth_datastore_create_role_permission_association_fails_if_uuid_no_permission(datastore, fixtures):
    role = fixtures.Role()

    with pytest.raises(IntegrityError):
        datastore.create_role_permission_association(role.uuid, uuid4(), commit=True)


def test_sqlalchemy_auth_datastore_create_role_permission_association_fails_if_type_not_unique(datastore, fixtures):
    permission = fixtures.Permission()

    with pytest.raises(IntegrityError):
        datastore.create_role_permission_association(uuid4(), permission.uuid, commit=True)


def test_sqlalchemy_auth_datastore_is_permission_in_roles_faster_using_cache(datastore, fixtures):
    roles = [fixtures.Role(permissions=[fixtures.Permission() for _ in range(15)]) for _ in range(150)]
    permission = fixtures.Permission(roles=roles[50:75])

    assert not datastore.cache.get(str(permission.uuid))

    start = datetime.now()
    assert datastore.is_permission_in_roles(permission_uuid=permission.uuid, role_uuids=[r.uuid for r in roles])
    no_cache = datetime.now() - start

    assert datastore.cache.get(str(permission.uuid)) == {str(r.uuid) for r in roles[50:75]}

    start = datetime.now()
    assert datastore.is_permission_in_roles(permission_uuid=permission.uuid, role_uuids=[r.uuid for r in roles])
    cache = datetime.now() - start

    assert datastore.cache.get(str(permission.uuid)) == {str(r.uuid) for r in roles[50:75]}

    print('SimpleCache class - without cache: {} -- with cache: {}'.format(no_cache, cache))

    assert cache < no_cache


def test_sqlalchemy_auth_datastore_is_permission_in_roles_faster_using_redis_cache(datastore, fixtures):
    # change cache class
    datastore.cache = RedisCache(host=environ['REDIS_HOST'], db=environ['REDIS_DB'])

    roles = [fixtures.Role(permissions=[fixtures.Permission() for _ in range(15)]) for _ in range(150)]
    permission = fixtures.Permission(roles=roles[50:75])

    assert not datastore.cache.get(str(permission.uuid))

    start = datetime.now()
    assert datastore.is_permission_in_roles(permission_uuid=permission.uuid, role_uuids=[r.uuid for r in roles])
    no_cache = datetime.now() - start

    assert datastore.cache.get(str(permission.uuid)) == {str(r.uuid) for r in roles[50:75]}

    start = datetime.now()
    assert datastore.is_permission_in_roles(permission_uuid=permission.uuid, role_uuids=[r.uuid for r in roles])
    cache = datetime.now() - start

    assert datastore.cache.get(str(permission.uuid)) == {str(r.uuid) for r in roles[50:75]}

    print('RedisCache class - without cache: {} -- with cache: {}'.format(no_cache, cache))

    assert cache < no_cache


def test_sqlalchemy_auth_datastore_is_permission_in_roles_faster_using_memcached_cache(datastore, fixtures):
    # change cache class
    datastore.cache = MemcachedCache(servers=[environ['MEMCACHED_HOST']], key_prefix=environ['MEMCACHED_KEY'])

    roles = [fixtures.Role(permissions=[fixtures.Permission() for _ in range(15)]) for _ in range(150)]
    permission = fixtures.Permission(roles=roles[50:75])

    assert not datastore.cache.get(str(permission.uuid))

    start = datetime.now()
    assert datastore.is_permission_in_roles(permission_uuid=permission.uuid, role_uuids=[r.uuid for r in roles])
    no_cache = datetime.now() - start

    assert datastore.cache.get(str(permission.uuid)) == {str(r.uuid) for r in roles[50:75]}

    start = datetime.now()
    assert datastore.is_permission_in_roles(permission_uuid=permission.uuid, role_uuids=[r.uuid for r in roles])
    cache = datetime.now() - start

    assert datastore.cache.get(str(permission.uuid)) == {str(r.uuid) for r in roles[50:75]}

    print('MemcachedCache class - without cache: {} -- with cache: {}'.format(no_cache, cache))

    assert cache < no_cache
