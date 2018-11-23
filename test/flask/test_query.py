from uuid import uuid4

import pytest

from thunderstorm_auth.exceptions import InsufficientPermissions
from thunderstorm_auth.query import filter_for_user
from thunderstorm_auth.user import User

from test.models import ComplexGroupComplexAssociation, Complex


def test_create_complex_group_assoc_model_insert(fixtures, db_session):
    db_session.add(fixtures.ComplexGroupComplexAssociation(group_uuid=uuid4(), complex_uuid=uuid4()))

    assert db_session.query(ComplexGroupComplexAssociation).count() == 1


def test_query_filter_for_user(fixtures, db_session):
    group_uuid = uuid4()

    complexes = [fixtures.Complex(uuid=uuid4()) for _ in range(3)]
    db_session.add_all(complexes)

    complex_associations = [
        fixtures.ComplexGroupComplexAssociation(complex_uuid=c.uuid, group_uuid=group_uuid) for c in complexes[:2]
    ]
    db_session.add_all(complex_associations)

    user = User(username='test', roles=[], groups=[group_uuid])

    query = db_session.query(Complex)
    filtered_query = filter_for_user(query, user, ComplexGroupComplexAssociation, Complex.uuid)

    assert query.count() == 3
    assert filtered_query.count() == 2


def test_query_filter_for_user_raises_insufficient_permissions_if_no_groups(fixtures, db_session):
    user = User(username='test', roles=[], groups=[])

    query = db_session.query(Complex)

    with pytest.raises(InsufficientPermissions):
        filter_for_user(query, user, ComplexGroupComplexAssociation, Complex.uuid)
