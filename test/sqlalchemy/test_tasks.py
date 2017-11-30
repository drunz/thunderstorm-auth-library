import uuid

import pytest

from thunderstorm_auth import group, tasks


@pytest.fixture
def complex_assoc_model(base, metadata):
    model = group.create_group_association_model(
        group.COMPLEX_GROUP_TYPE, base
    )
    metadata.create_all()
    return model


@pytest.fixture
def create_group(complex_assoc_model, db_session):

    def _create_group_with_members(num_members=0):
        group_uuid = uuid.uuid4()
        complex_uuids = [uuid.uuid4() for _ in range(num_members)]
        for complex_uuid in complex_uuids:
            model = complex_assoc_model(
                group_uuid=group_uuid,
                complex_uuid=complex_uuid
            )
            db_session.add(model)
        db_session.flush()
        return group_uuid, complex_uuids

    return _create_group_with_members


@pytest.fixture(autouse=True)
def control_fixtures(create_group):
    return create_group(num_members=1)


def test_get_current_members(create_group, complex_assoc_model, db_session):
    # arrange
    group_uuid, complex_uuids = create_group(num_members=3)

    # act
    members = tasks.get_current_members(
        db_session, complex_assoc_model, group_uuid
    )

    # assert
    assert members == set(complex_uuids)


def test_delete_group_associations(
        create_group, complex_assoc_model, db_session):
    # arrange
    group_uuid, complex_uuids = create_group(num_members=3)

    # act
    tasks.delete_group_associations(
        db_session,
        complex_assoc_model,
        group_uuid,
        {complex_uuids[1], complex_uuids[2]}
    )

    # assert
    remaining_members = db_session.query(
        complex_assoc_model.complex_uuid
    ).filter(
        complex_assoc_model.group_uuid == group_uuid
    )
    remaining_members = {m.complex_uuid for m in remaining_members}
    assert remaining_members == {complex_uuids[0]}


def test_add_group_associations(
        create_group, complex_assoc_model, db_session):
    # arrange
    group_uuid, complex_uuids = create_group(num_members=3)
    new_complexes = {uuid.uuid4() for _ in range(2)}

    # act
    tasks.add_group_associations(
        db_session,
        complex_assoc_model,
        group_uuid,
        new_complexes
    )

    # assert
    members = db_session.query(
        complex_assoc_model.complex_uuid
    ).filter(
        complex_assoc_model.group_uuid == group_uuid
    )
    members = {m.complex_uuid for m in members}
    assert members == set(complex_uuids) | new_complexes
