from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from thunderstorm_auth.group import create_group_association_model, COMPLEX_GROUP_TYPE
from thunderstorm_auth.permissions import PermissionMixin
from thunderstorm_auth.roles import RoleMixin, RolePermissionAssociationMixin

Base = declarative_base()

ComplexGroupComplexAssociation = create_group_association_model(COMPLEX_GROUP_TYPE, Base)


class Role(Base, RoleMixin):
    pass


class RolePermissionAssociation(Base, RolePermissionAssociationMixin):
    pass


class Permission(Base, PermissionMixin):
    pass


class Complex(Base):
    __tablename__ = 'complex'

    uuid = Column(UUID(as_uuid=True), primary_key=True)
