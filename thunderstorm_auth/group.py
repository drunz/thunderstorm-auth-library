from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID


SCHEMA = 'ts_auth'


def _camel_case(value):
    return ''.join(part.capitalize() for part in value.split('_'))


class GroupType:
    """Definition of a auth group type.

    Provides sync task name, model name, table names, mapping column name.
    """

    _table_name_tmpl = '{}_group_map'
    _map_column_name_tmpl = '{}_uuid'
    _task_name_tmpl = 'thunderstorm_auth.group.sync.{}'

    def __init__(self, name):
        self.name = name.lower()
        self.table_name = self._table_name_tmpl.format(self.name)
        self.model_name = _camel_case(self.table_name)
        self.map_column_name = self._map_column_name_tmpl.format(self.name)

        self.task_name = self._task_name_tmpl.format(self.name)


COMPLEX_GROUP_TYPE = GroupType('complex')


def create_group_map_model(group_type, base):
    """
    Create a SQLAlchemy model representing the mapping of data to groups.

    Args:
        group_type (GroupType): Type of group model to create.
        base (Base): Declarative base of database schema to add model to.

    Returns:
        SQLALchemy model of group mapping. Depending on `group_type`.
    """
    return type(
        group_type.model_name,
        (base,),
        {
            '__ts_group_type__': group_type,
            '__tablename__': group_type.table_name,
            '__table_args__ ': {'schema': SCHEMA},
            'group_uuid': Column(UUID(as_uuid=True), primary_key=True),
            group_type.map_column_name: Column(UUID(as_uuid=True), primary_key=True)
        }
    )
