from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

SCHEMA = 'ts_auth'


def _camel_case(value):
    return ''.join(part.capitalize() for part in value.split('_'))


class GroupType:
    """Definition of a auth group type.

    Attrs:
        - `table_name`: db table name
        - `model_name`: orm model name
        - `member_column_name`: member association column name
        - `task_name`: sync task name
        - `routing_key`: sync task routing key
    Methods:
        - `queue_name(celery_app)`: sync task queue name

    Example:
        ```
        gt = GroupType('foo')

        gt.table_name           # 'foo_group_association'
        gt.model_name           # 'FooGroupAssociation'
        gt.member_column_name   # 'foo_uuid'

        gt.task_name            # 'ts_auth.group.foo.sync'
        gt.queue_name           # 'my_service.ts_auth.group.foo'
        gt.routing_key          # 'group.foo'
        ```
    """

    def __init__(self, name):
        self.name = name.lower()

        # model attrs
        self.table_name = '{name}_group_association'.format(name=self.name)
        self.model_name = _camel_case(self.table_name)
        self.member_column_name = '{name}_uuid'.format(name=self.name)

        # task attrs
        self.routing_key = 'group.{name}'.format(name=self.name)
        self.task_name = 'ts_auth.group.{name}.sync'.format(name=self.name)

    def queue_name(self, celery_main):
        return '{celery_main}.ts_auth.group.{name}'.format(celery_main=celery_main, name=self.name)


COMPLEX_GROUP_TYPE = GroupType('complex')


def create_group_association_model(group_type, base):
    """
    Create a SQLAlchemy model representing the association of data to groups.

    Args:
        group_type (GroupType): Type of group model to create.
        base (Base): Declarative base of database schema to add model to.

    Returns:
        SQLALchemy model of TS auth group association defined by `group_type`.
    """
    return type(
        group_type.model_name, (base, ), {
            '__ts_group_type__': group_type, '__tablename__': group_type.table_name, 'group_uuid':
            Column(UUID(as_uuid=True),
                   primary_key=True), group_type.member_column_name: Column(UUID(as_uuid=True), primary_key=True)
        }
    )
