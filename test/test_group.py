from sqlalchemy.ext.declarative import declarative_base

from thunderstorm_auth import group


def test_group_type_attributes():
    # act
    example_type = group.GroupType('example')
    queue_name = example_type.queue_name('my_service')

    # assert
    assert example_type.table_name == 'example_group_association'
    assert example_type.model_name == 'ExampleGroupAssociation'
    assert example_type.member_column_name == 'example_uuid'
    assert example_type.task_name == 'ts_auth.group.example.sync'
    assert example_type.routing_key == 'group.example'
    assert queue_name == 'my_service.ts_auth.group.example'


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
