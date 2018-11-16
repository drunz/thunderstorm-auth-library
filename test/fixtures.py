from uuid import uuid4

from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import BaseFuzzyAttribute, FuzzyText

from test import models


class FuzzyUuid(BaseFuzzyAttribute):
    def fuzz(self):
        return uuid4()


class Complex(SQLAlchemyModelFactory):
    class Meta:
        model = models.Complex

    uuid = FuzzyUuid()


class ComplexGroupComplexAssociation(SQLAlchemyModelFactory):
    class Meta:
        model = models.ComplexGroupComplexAssociation

    complex_uuid = FuzzyUuid()
    group_uuid = FuzzyUuid()


class Role(SQLAlchemyModelFactory):
    class Meta:
        model = models.Role

    uuid = FuzzyUuid()
    type = FuzzyText()


class Permission(SQLAlchemyModelFactory):
    class Meta:
        model = models.Permission

    uuid = FuzzyUuid()
    service_name = FuzzyText()
    permission = FuzzyText()
    is_deleted = False
    is_sent = False


class RolePermissionAssociation(SQLAlchemyModelFactory):
    class Meta:
        model = models.RolePermissionAssociation

    role_uuid = FuzzyUuid()
    permission_uuid = FuzzyUuid()
