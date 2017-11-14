from sqlalchemy.ext.declarative import declarative_base

from thunderstorm_auth import group


def test_create_complex_group_model():
    # arrange
    base = declarative_base()

    # act
    model = group.create_group_association_model(
        group.COMPLEX_GROUP_TYPE, base
    )

    # assert
    assert model.__name__ == 'ComplexGroupAssociation'
    assert model.__tablename__ == 'complex_group_association'
    assert model.__ts_group_type__ == group.COMPLEX_GROUP_TYPE
    assert issubclass(model, base)
    assert hasattr(model, 'group_uuid')
    assert hasattr(model, 'complex_uuid')
