import uuid

from thunderstorm_auth import group


def test_create_complex_group_assoc_model_insert(metadata, base, db_session):
    model = group.create_group_association_model(group.COMPLEX_GROUP_TYPE, base)
    metadata.create_all()
    db_session.add(
        model(
            group_uuid=uuid.uuid4(),
            complex_uuid=uuid.uuid4()
        )
    )
    db_session.commit()
    assert db_session.query(model).count() == 1
