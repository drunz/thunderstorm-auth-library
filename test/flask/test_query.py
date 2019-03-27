from uuid import uuid4

from test.models import ComplexGroupComplexAssociation


def test_create_complex_group_assoc_model_insert(fixtures, db_session):
    db_session.add(fixtures.ComplexGroupComplexAssociation(group_uuid=uuid4(), complex_uuid=uuid4()))

    assert db_session.query(ComplexGroupComplexAssociation).count() == 1
