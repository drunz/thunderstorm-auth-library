import uuid
from unittest import mock

import celery
import celery.task
import pytest
from sqlalchemy.ext.declarative import declarative_base

from thunderstorm_auth import group, tasks

from .test_permissions import make_permission


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
    db_session = mock.Mock()

    # act
    task = tasks.group_sync_task(group_model, db_session)

    # assert
    assert isinstance(task, celery.task.Task)
    assert task.name == 'ts_auth.group.example.sync'


@mock.patch('thunderstorm_auth.tasks.get_current_members')
@mock.patch('thunderstorm_auth.tasks.delete_group_associations')
@mock.patch('thunderstorm_auth.tasks.add_group_associations')
def test_group_sync_task_run(
    add_group_associations, delete_group_associations, get_current_members,
    group_model
):
    # arrange
    db_session = mock.Mock(name='db_session')
    task = tasks.group_sync_task(group_model, db_session)

    group_uuid = uuid.uuid4()
    all_members = [uuid.uuid4() for _ in range(4)]

    # currently 0, 1, 2
    get_current_members.return_value = set(all_members[:3])
    # updated to 1, 2, 3
    updated_members = all_members[1:]

    # act
    task(group_uuid, updated_members)

    # assert
    get_current_members.assert_called_with(
        db_session,
        group_model,
        group_uuid
    )
    delete_group_associations.assert_called_with(
        db_session,
        group_model,
        group_uuid,
        {all_members[0]}
    )
    add_group_associations.assert_called_with(
        db_session,
        group_model,
        group_uuid,
        {all_members[3]}
    )


@mock.patch('thunderstorm_auth.tasks.send_task')
def test_sync_permissions(mock_send_task):
    # arrange
    permission_model = mock.Mock()
    db_session = mock.Mock()

    task = tasks.permission_sync_task(permission_model, db_session)

    db_session.query.return_value.filter.return_value = [
        make_permission(
            uuid='0fc466f6-101b-11e8-9cd1-4a0004692f50',
            permission='perm1',
            is_deleted=True,
        ),
        make_permission(
            uuid='255e8a1e-101b-11e8-8d15-4a0004692f50',
            permission='perm2',
            is_deleted=False,
        )
    ]

    task()

    mock_send_task.assert_has_calls(
        [
            mock.call(
                'permissions.delete',
                ('0fc466f6-101b-11e8-9cd1-4a0004692f50',),
                exchange='ts.messaging',
                routing_key='permissions.delete'
            ),
            mock.call(
                'permissions.new',
                ('255e8a1e-101b-11e8-8d15-4a0004692f50', 'test', 'perm2'),
                exchange='ts.messaging',
                routing_key='permissions.new'
            )
        ]
    )
    assert db_session.commit.call_count == 2
    assert db_session.add.call_count == 2
