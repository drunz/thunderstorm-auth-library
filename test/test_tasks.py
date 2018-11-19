from uuid import uuid4, UUID
from unittest.mock import patch, Mock, call

import celery
import celery.task
import pytest
from sqlalchemy.ext.declarative import declarative_base

from thunderstorm_auth import group, tasks
from thunderstorm_auth.tasks import permission_sync_task

from test.models import Permission


@pytest.fixture
def group_type():
    return group.GroupType('example')


@pytest.fixture
def group_model(group_type):
    base = declarative_base()
    return group.create_group_association_model(group_type, base)


@pytest.fixture(autouse=True)
def _teardown_celery_app(group_type):
    app = celery.current_app
    yield app
    if group_type.task_name in app.tasks:
        app.tasks.unregister(group_type.task_name)


def test_create_group_sync_task(group_model):
    # arrange
    db_session = Mock()

    # act
    task = tasks.group_sync_task(group_model, db_session)

    # assert
    assert isinstance(task, celery.task.Task)
    assert task.name == 'ts_auth.group.example.sync'


@patch('thunderstorm_auth.tasks.get_current_members')
@patch('thunderstorm_auth.tasks.delete_group_associations')
@patch('thunderstorm_auth.tasks.add_group_associations')
def test_group_sync_task_run(add_group_associations, delete_group_associations, get_current_members, group_model):
    # arrange
    db_session = Mock(name='db_session')
    task = tasks.group_sync_task(group_model, db_session)

    group_uuid = uuid4()
    all_members = [uuid4() for _ in range(4)]

    # currently 0, 1, 2
    get_current_members.return_value = set(all_members[:3])
    # updated to 1, 2, 3
    updated_members = all_members[1:]

    # act
    task(group_uuid, updated_members)

    # assert
    get_current_members.assert_called_with(db_session, group_model, group_uuid)
    delete_group_associations.assert_called_with(db_session, group_model, group_uuid, {all_members[0]})
    add_group_associations.assert_called_with(db_session, group_model, group_uuid, {all_members[3]})


@patch('thunderstorm_auth.tasks.send_task')
def test_sync_permissions(mock_send_task, db_session, fixtures):
    # arrange
    fixtures.Permission(
        uuid='0fc466f6-101b-11e8-9cd1-4a0004692f50',
        permission='perm1',
        service_name='test',
        is_deleted=True
    )
    fixtures.Permission(
        uuid='255e8a1e-101b-11e8-8d15-4a0004692f50',
        permission='perm2',
        service_name='test',
        is_deleted=False
    )

    # call task
    permission_sync_task(Permission, db_session)()

    mock_send_task.assert_has_calls(
        [
            call(
                'permissions.delete', (UUID('0fc466f6-101b-11e8-9cd1-4a0004692f50'), ),
                exchange='ts.messaging',
                routing_key='permissions.delete'
            ),
            call(
                'permissions.new', (UUID('255e8a1e-101b-11e8-8d15-4a0004692f50'), 'test', 'perm2'),
                exchange='ts.messaging',
                routing_key='permissions.new'
            )
        ]
    )
