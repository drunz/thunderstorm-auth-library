from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from thunderstorm_auth.groups import ComplexGroupAssociationMixin
from thunderstorm_auth.permissions import PermissionMixin
from thunderstorm_auth.roles import RoleMixin, RolePermissionAssociationMixin

Base = declarative_base()


class Role(Base, RoleMixin):
    pass


class RolePermissionAssociation(Base, RolePermissionAssociationMixin):
    pass


class Permission(Base, PermissionMixin):
    pass


class ComplexGroupComplexAssociation(Base, ComplexGroupAssociationMixin):
    pass


class Complex(Base):
    __tablename__ = 'complex'

    uuid = Column(UUID(as_uuid=True), primary_key=True)
