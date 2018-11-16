from uuid import uuid4

from thunderstorm_auth import tasks
from test.models import ComplexGroupComplexAssociation


def test_get_current_members(fixtures, db_session):
    # arrange
    group_uuid = uuid4()
    complexes = [fixtures.Complex() for i in range(3)]
    [fixtures.ComplexGroupComplexAssociation(group_uuid=group_uuid, complex_uuid=c.uuid) for c in complexes]

    # act
    members = tasks.get_current_members(db_session, ComplexGroupComplexAssociation, group_uuid)

    # assert
    assert members == {c.uuid for c in complexes}


def test_delete_group_associations(fixtures, db_session):
    # arrange
    group_uuid = uuid4()
    complexes = [fixtures.Complex() for i in range(3)]
    [fixtures.ComplexGroupComplexAssociation(group_uuid=group_uuid, complex_uuid=c.uuid) for c in complexes]

    # act
    tasks.delete_group_associations(
        db_session, ComplexGroupComplexAssociation, group_uuid, {c.uuid
                                                                 for c in complexes[1:]}
    )

    # assert
    remaining_members = db_session.query(ComplexGroupComplexAssociation.complex_uuid
                                        ).filter(ComplexGroupComplexAssociation.group_uuid == group_uuid)

    remaining_members = {m.complex_uuid for m in remaining_members}
    assert remaining_members == {complexes[0].uuid}


def test_add_group_associations(fixtures, db_session):
    # arrange
    group_uuid = uuid4()
    complexes = [fixtures.Complex() for i in range(3)]
    [fixtures.ComplexGroupComplexAssociation(group_uuid=group_uuid, complex_uuid=c.uuid) for c in complexes]
    new_complexes = {uuid4() for _ in range(2)}

    # act
    tasks.add_group_associations(db_session, ComplexGroupComplexAssociation, group_uuid, new_complexes)

    # assert
    members = db_session.query(ComplexGroupComplexAssociation.complex_uuid
                              ).filter(ComplexGroupComplexAssociation.group_uuid == group_uuid)

    members = {m.complex_uuid for m in members}
    assert members == {c.uuid for c in complexes} | new_complexes
