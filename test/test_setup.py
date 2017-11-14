from unittest import mock

import celery
import pytest
from sqlalchemy.ext.declarative import declarative_base

from thunderstorm_auth import group, setup


@pytest.fixture
def group_types():
    return [
        group.GroupType('foo'),
        group.GroupType('bar')
    ]


@pytest.fixture
def models(group_types):
    base = declarative_base()
    foo_type, bar_type = group_types
    return [
        group.create_group_association_model(foo_type, base),
        group.create_group_association_model(bar_type, base)
    ]


@pytest.fixture
def celery_app(group_types):
    foo_type, bar_type = group_types
    app = celery.Celery()
    yield app
    app.tasks.unregister(foo_type.task_name)
    app.tasks.unregister(bar_type.task_name)


def test_init_group_sync_tasks(celery_app, models, group_types):
    # arrange
    foo_type, bar_type = group_types
    db_session = mock.Mock()

    # act
    setup.init_group_sync_tasks(celery_app, db_session, models)

    # assert
    assert {q.alias for q in celery_app.conf.task_queues} == {
        foo_type.task_name,
        bar_type.task_name
    }
    assert foo_type.task_name in celery_app.tasks
    assert bar_type.task_name in celery_app.tasks
