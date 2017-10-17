from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship


class AuthGroupMixin(object):
    """
    Base model mixin for the group
    table name must be left untouched as a relationship depends on it
    """
    @declared_attr
    def __tablename__(cls):
        return 'ts_auth_group'

    uuid = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)


class AuthGroupAssociationMixin(object):
    """
    Base model mixin for the group association
    Using an association table so we can adapt to any type of relationship
    (m2m in the specific) without adding a foreign key on the target model
    """
    # @declared_attr
    # def __tablename__(cls):
    #     return 'ts_auth_group_association'

    @declared_attr
    def group_uuid(cls):
        return Column(UUID(as_uuid=True), ForeignKey('ts_auth_group.uuid'), primary_key=True)

    relationship(
        'ts_auth_group',
        backref=backref('group_associations', passive_deletes='all')
    )
