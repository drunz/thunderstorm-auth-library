from unittest import mock

import celery
import kombu
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
    app = celery.Celery('example_service')
    yield app
    app.tasks.unregister(foo_type.task_name)
    app.tasks.unregister(bar_type.task_name)


def test_exchange_name():
    assert setup.EXCHANGE.name == 'ts_auth.group'


def test_init_group_sync_tasks(celery_app, models, group_types):
    # arrange
    foo_type, bar_type = group_types
    db_session = mock.Mock()

    # act
    setup.init_group_sync_tasks(celery_app, db_session, models)

    # assert
    assert foo_type.task_name in celery_app.tasks
    assert bar_type.task_name in celery_app.tasks


def test_init_group_sync_queue(celery_app, models, group_types):
    # arrange
    foo_type, bar_type = group_types
    db_session = mock.Mock()

    # act
    setup.init_group_sync_tasks(celery_app, db_session, models)

    # assert
    queues = [
        q for q in celery_app.conf.task_queues
        if q.name != celery_app.conf.task_default_queue
    ]
    assert len(queues) == 1, queues
    queue = queues[0]
    assert isinstance(queue, kombu.Queue)
    assert queue.name == 'example_service.ts_auth.group'
    assert {binding.exchange for binding in queue.bindings} == {
        setup.EXCHANGE
    }
    assert {binding.routing_key for binding in queue.bindings} == {
        foo_type.routing_key,
        bar_type.routing_key
    }
