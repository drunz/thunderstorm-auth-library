from abc import ABC

from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from werkzeug.contrib.cache import BaseCache, SimpleCache


class AuthStore(ABC):
    """
    Abstract auth store
    """

    # TODO @shipperizer implement also permission creation

    def __init__(self, role_model, permission_model, association_model, group_association_model):
        """
        Args:
            role_model (object): A role model class definition
            permission_model (object): A permission model class definition
            association_model (object): An association role-permission model class definition
            group_association_model (object): A group model class definition (eg complex-group)
        """
        self.role_model = role_model
        self.permission_model = permission_model
        self.association_model = association_model
        self.group_association_model = group_association_model

    def create_role(self, role_uuid, role_type):
        """
        Args:
            role_uuid (object): primary identifier of a role
            role_type (object): type of a role
        """
        raise NotImplementedError

    def get_role(self, role_uuid):
        """
        Args:
            role_uuid (object): primary identifier of a role
        """
        raise NotImplementedError

    def get_role_permissions(self, role_uuid):
        """
        Args:
            role_uuid (object): primary identifier of a role
        """
        raise NotImplementedError

    def get_roles(self, role_uuids):
        """
        Args:
            role_uuids (list of objects): primary identifiers of roles
        """
        raise NotImplementedError

    def get_roles_permissions(self, role_uuids):
        """
        Args:
            permission_uuid (object): primary identifier of a permission
        """
        raise NotImplementedError

    def is_permission_in_roles(self, permission_uuid=None, permission_string=None, role_uuids=None):
        """
        Args:
            permission_uuid (object): primary identifier of a permission
            permission_string (object): string of a permission
            role_uuids (list of objects): primary identifiers of roles
        """
        raise NotImplementedError

    def get_permission(self, permission_uuid):
        """
        Args:
            permission_uuid (object): primary identifier of a permission
        """
        raise NotImplementedError

    def get_permission_roles(self, permission_uuid):
        """
        Args:
            permission_uuid (object): primary identifier of a permission
        """
        raise NotImplementedError

    def get_permissions(self, permission_uuids):
        """
        Args:
            permission_uuid (list of objects): primary identifiers of permissions
        """
        raise NotImplementedError

    def create_role_permission_association(self, role_uuid, permission_uuid):
        """
        Args:
            role_uuid (object): primary identifier of a role
            permission_uuid (object): primary identifier of a permission
        """
        raise NotImplementedError

    def group_associations_exist(self):
        raise NotImplementedError

    def get_group_associations_(self, group_uuids):
        """
        Args:
            group_uuids (list of objects): primary identifiers of group
        """
        raise NotImplementedError

    def create_group_association(self, group_uuid, complex_uuid):
        """
        Args:
            group_uuid (object): primary identifier of a group
            complex_uuid (object): primary identifier of a complex
        """
        raise NotImplementedError

    def delete_group_association(self, group_uuid, complex_uuid):
        """
        Args:
            group_uuid (object): primary identifier of a group
            complex_uuid (object): primary identifier of a complex
        """
        raise NotImplementedError


class SQLAlchemySessionStore(object):
    """
    SQLAlchemy store implementation
    """

    def __init__(self, db_session):
        """
        Args:
            db_session (sqlalchemy session): database session
        """
        self.db_session = db_session

    def commit(self):
        """
        Commit method
        """
        try:
            self.db_session.commit()
        except (DBAPIError, SQLAlchemyError):
            self.db_session.rollback()
            raise


class SQLAlchemySessionAuthStore(SQLAlchemySessionStore, AuthStore):
    """
    SQLAlchemy auth store implementation
    """

    def __init__(self, db_session, role_model, permission_model, association_model, group_association_model, bootstrap=False, cache=None):
        """
        Args:
            db_session (sqlalchemy session): database session
            role_model (sqlalchemy model): a role model class definition
            association_model (sqlalchemy model): a role-permission association model class definition
            permission_model (sqlalchemy model): a permission model class definition
            group_association_model (sqlalchemy model): A group model class definition (eg complex-group)
            bootstrap (bool): defines if the class should preload the permissions and roles into the cache
            cache (werkzeug.contrib.cache.BaseCache): cache object, defaults to SimpleCache is None
        """
        SQLAlchemySessionStore.__init__(self, db_session)
        AuthStore.__init__(self, role_model, permission_model, association_model, group_association_model)

        # default in-memory cache with 7.5mins timeout and max 500 elements cached
        if cache and not isinstance(cache, BaseCache):
            raise NotImplementedError('Cache class {} not supported'.format(type(cache)))
        self.cache = cache or SimpleCache(default_timeout=450)

        if bootstrap:
            self.preload_cache()

    def preload_cache(self):
        """
        Setup the cache for all the permissions in the db
        """
        for permission in self.db_session.query(self.permission_model):
            self.get_permission_roles(permission.uuid)

    def get_role(self, role_uuid):
        """
        Args:
            role_uuid (uuid): primary identifier of a role

        Returns:
            Role (sqlalchemy model instance): record object with the id passed
            None: no role found with that id
        """
        return self.db_session.query(self.role_model).get(role_uuid)

    def get_role_permissions(self, role_uuid):
        """
        Args:
            role_uuid (object): primary identifier of a role

        Returns:
            query (sqlalchemy query object): query with all the permissions with a specific role_uuid
        """
        subquery = self.db_session.query(
            self.association_model.permission_uuid
        ).filter(self.association_model.role_uuid == role_uuid)

        return self.db_session.query(self.permission_model).filter(self.permission_model.uuid.in_(subquery))

    def get_roles(self, role_uuids):
        """
        Args:
            role_uuids (list of uuids): primary identifiers of roles

        Returns:
            query (sqlalchemy query object): query with all the roles with those ids
        """
        return self.db_session.query(self.role_model).filter(self.role_model.uuid.in_(role_uuids))

    def get_roles_permissions(self, role_uuids):
        """
        Args:
            role_uuids (list of uuids): primary identifiers of roles

        Returns:
            query (sqlalchemy query object): query with all the permissions with a specifics role_uuids
        """
        subquery = self.db_session.query(self.association_model.permission_uuid).filter(
            self.association_model.role_uuid.in_(role_uuids)
        )

        return self.db_session.query(self.permission_model).filter(self.permission_model.uuid.in_(subquery))

    # TODO @shipperizer add permission service otherwise user-service won't work due to permission string not being
    # unique across different service
    def is_permission_in_roles(self, permission_uuid=None, permission_string=None, role_uuids=None):
        """
        Checks if a permission is belonging to any of those roles, if cache value is set, skips the query

        Args:
            permission_uuid (uuid): primary identifier of a permission
            permission_string (str): permission name and definition
            role_uuids (list of uuids): primary identifiers of roles

        Returns:
            bool: permission belongs to at least one role
        """
        if any([(not (permission_uuid or permission_string)), (not role_uuids)]):
            return False

        if permission_string and not permission_uuid:
            permission = self.db_session.query(
                self.permission_model
            ).filter(self.permission_model.permission == permission_string).one_or_none()
            if permission:
                permission_uuid = permission.uuid
            else:
                return False

        # check if this works on other types of cache
        if not self.cache.get(str(permission_uuid)):
            # call get_permission_roles to set cache
            self.get_permission_roles(permission_uuid)

        # return True if there is intersection
        if self.cache.get(str(permission_uuid)) & {str(role_uuid) for role_uuid in role_uuids}:
            return True
        return False

    def get_permission(self, permission_uuid):
        """
        Args:
            permission_uuid (object): primary identifier of a permission

        Returns:
            Permission (sqlalchemy model instance): record object with the id passed
            None: no permission found with that id
        """
        return self.db_session.query(self.permission_model).get(permission_uuid)

    def get_permission_roles(self, permission_uuid):
        """
        Args:
            permission_uuid (object): primary identifier of a permission

        Returns:
            query (sqlalchemy query object): query with all the roles owning a specifics permission_uuid
        """
        subquery = self.db_session.query(
            self.association_model.role_uuid
        ).filter(self.association_model.permission_uuid == permission_uuid)

        # subquery values are a 1 element lists of UUIDS: [[UUID], [UUID], [UUID]]
        # setting the cache with permission_uuid as key and roles_uuids as string values
        self.cache.set(str(permission_uuid), {str(role[0]) for role in subquery})

        return self.db_session.query(self.role_model).filter(self.role_model.uuid.in_(subquery))

    def get_permissions(self, permission_uuids):
        """
        Args:
            permission_uuids (list of uuid): primary identifiers of permissions

        Returns:
            query (sqlalchemy query object): query with all the permissions with those ids
        """
        return self.db_session.query(self.permission_model).filter(self.permission_model.uuid.in_(permission_uuids))

    def create_role(self, role_uuid, role_type, commit=False):
        """
        Args:
            role_uuid (uuid): primary identifier of a role
            role_type (str): type of a role
            commit (bool): commit or not the db session

        Returns:
            role_uuid (uuid): identifier of the role created
        """
        self.db_session.add(self.role_model(uuid=role_uuid, type=role_type))

        if commit:
            self.commit()

        return role_uuid

    def create_role_permission_association(self, role_uuid, permission_uuid, commit=False):
        """
        Args:
            role_uuid (uuid): primary identifier of a role
            permission_uuid (uuid): primary identifier of a permission
            commit (bool): commit or not the db session

        Returns:
            (role_uuid, permission_uuid) (tuple): identifier of the role-permission association created
        """
        query = self.get_role_permissions(role_uuid).filter(self.permission_model.uuid == permission_uuid)
        if not query.one_or_none():
            self.db_session.add(self.association_model(role_uuid=role_uuid, permission_uuid=permission_uuid))

        if commit:
            self.commit()

        return (role_uuid, permission_uuid)

    def delete_role_permission_association(self, role_uuid, permission_uuid, commit=False):
        """
        Args:
            role_uuid (uuid): primary identifier of a role
            permission_uuid (uuid): primary identifier of a permission
            commit (bool): commit or not the db session

        Returns:
            (role_uuid, permission_uuid) (tuple): identifier of the role-permission association created
        """

        association = self.db_session.query(self.association_model).get((role_uuid, permission_uuid))

        if association:
            self.db_session.delete(association)

            if commit:
                self.commit()

        return (role_uuid, permission_uuid)

    def group_associations_exist(self):
        """
        Checks if there is any group instance in the group table

        Returns:
            bool: True if at least one group is present, False otherwise
        """
        return True if self.db_session.query(self.group_association_model).first() else False

    def get_group_associations(self, group_uuids):
        """
        Args:
            group_uuids (list of uuids): primary identifiers of groups

        Returns:
            query (sqlalchemy query object): query with all the group associations with those group uuids
        """
        if len(group_uuids) == 1:
            return self.db_session.query(self.group_association_model).filter(self.group_association_model.group_uuid == group_uuids[0])
        return self.db_session.query(self.group_association_model).filter(self.group_association_model.group_uuid.in_(group_uuids))

    def create_group_association(self, group_uuid, complex_uuid, commit=False):
        """
        Args:
            group_uuid (uuid): primary identifier of a group
            complex_uuid (uuid): primary identifier of a complex
            commit (bool): commit or not the db session

        Returns:
            (group_uuid, complex_uuid) (tuple): identifier of the group association created
        """
        self.db_session.add(self.group_association_model(group_uuid=group_uuid, complex_uuid=complex_uuid))

        if commit:
            self.commit()

        return (group_uuid, complex_uuid)

    def delete_group_association(self, group_uuid, complex_uuid, commit=False):
        """
        Args:
            group_uuid (uuid): primary identifier of a group
            complex_uuid (uuid): primary identifier of a complex
            commit (bool): commit or not the db session

        Returns:
            (group_uuid, complex_uuid) (tuple): identifier of the group association created
        """
        association = self.db_session.query(self.group_association_model).get((group_uuid, complex_uuid))

        if association:
            self.db_session.delete(association)

            if commit:
                self.commit()

        return (group_uuid, complex_uuid)
