import uuid
from unittest import mock

import celery
import celery.task
import kombu.common
import pytest
from sqlalchemy.ext.declarative import declarative_base

from thunderstorm_auth import group, tasks


@pytest.fixture
def group_type():
    return group.GroupType('example')


@pytest.fixture
def model(group_type):
    base = declarative_base()
    return group.create_group_association_model(group_type, base)


@pytest.fixture(autouse=True)
def _teardown_celery_app(group_type):
    app = celery.current_app
    yield app
    if group_type.task_name in app.tasks:
        app.tasks.unregister(group_type.task_name)


def test_create_group_sync_queue(group_type):
    # arrange
    celery_app = celery.Celery('test_app')

    # act
    queue = tasks.group_sync_queue(group_type, celery_app.main)

    # assert
    assert isinstance(queue, kombu.common.Broadcast)
    assert queue.alias == 'thunderstorm_auth.example_group.sync'
    assert queue.name == 'thunderstorm_auth.example_group.sync.bcast.test_app'
    assert queue.exchange.name == 'thunderstorm_auth.example_group.sync'


def test_create_group_sync_task(model):
    # arrange
    db_session = mock.Mock()

    # act
    task = tasks.group_sync_task(model, db_session)

    # assert
    assert isinstance(task, celery.task.Task)
    assert task.name == 'thunderstorm_auth.example_group.sync'


@mock.patch('thunderstorm_auth.tasks.get_current_members')
@mock.patch('thunderstorm_auth.tasks.delete_group_associations')
@mock.patch('thunderstorm_auth.tasks.add_group_associations')
def test_group_sync_task_run(
        add_group_associations, delete_group_associations, get_current_members, model):
    # arrange
    db_session = mock.Mock(name='db_session')
    task = tasks.group_sync_task(model, db_session)

    group_uuid = uuid.uuid4()
    all_members = [uuid.uuid4() for _ in range(4)]

    get_current_members.return_value = set(all_members[:3])  # currently 0, 1, 2
    updated_members = all_members[1:]  # updated to 1, 2, 3

    # act
    task(group_uuid, updated_members)

    # assert
    get_current_members.assert_called_with(
        db_session,
        model,
        group_uuid
    )
    delete_group_associations.assert_called_with(
        db_session,
        model,
        group_uuid,
        {all_members[0]}
    )
    add_group_associations.assert_called_with(
        db_session,
        model,
        group_uuid,
        {all_members[3]}
    )
