import uuid

import pytest
from sqlalchemy import Column
from sqlalchemy.dialects import postgresql as pg

from thunderstorm_auth import group
from thunderstorm_auth.exceptions import InsufficientPermissions
from thunderstorm_auth.query import filter_for_user
from thunderstorm_auth.user import User


@pytest.fixture
def complex_model(base):

    class Complex(base):
        __tablename__ = 'complex'
        uuid = Column(pg.UUID(as_uuid=True), primary_key=True)

    return Complex


@pytest.fixture
def complex_assoc_model(base):
    return group.create_group_association_model(
        group.COMPLEX_GROUP_TYPE, base
    )


@pytest.fixture
def models(metadata, complex_model, complex_assoc_model):
    metadata.create_all()
    return complex_model, complex_assoc_model


def test_query_filter_for_user(db_session, models):
    complex_model, complex_assoc_model = models

    group_uuid = uuid.uuid4()

    complexes = [complex_model(uuid=uuid.uuid4()) for _ in range(3)]
    db_session.add_all(complexes)

    complex_associations = [
        complex_assoc_model(
            complex_uuid=c.uuid,
            group_uuid=group_uuid
        )
        for c in complexes[:2]
    ]
    db_session.add_all(complex_associations)

    user = User(username='test', groups=[group_uuid], permissions=None)

    query = db_session.query(complex_model)
    filtered_query = filter_for_user(
        query, user, complex_assoc_model, complex_model.uuid
    )

    assert query.count() == 3
    assert filtered_query.count() == 2


def test_query_filter_for_user_raises_insufficient_permissions_if_no_groups(
        db_session, models):
    complex_model, complex_assoc_model = models

    user = User(username='test', groups=[], permissions=None)

    query = db_session.query(complex_model)
    with pytest.raises(InsufficientPermissions):
        filter_for_user(
            query, user, complex_assoc_model, complex_model.uuid
        )
