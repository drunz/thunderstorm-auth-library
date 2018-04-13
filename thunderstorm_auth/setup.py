import itertools

import kombu
from celery import signals

from thunderstorm_auth.tasks import group_sync_task, permission_sync_task


LEGACY_EXCHANGE = kombu.Exchange('ts_auth.group')
EXCHANGE = kombu.Exchange('ts.messaging')


def init_group_sync_tasks(
    celery_app, db_session, group_models,
    ensure_exchange_exists=True
):
    """
    Initialize a Celery app with a queue and sync tasks for auth group models.

    Creates and registers a sync task for each group association model.
    Creates a queue for the service to consume these tasks from and binds the
    queue to the `ts_auth.group` exchange, binding it with the routing keys of
    the group types of the group association models.

    Args:
        celery_app (Celery): Celery app to register the sync tasks with.
        db_session (Session): Database session used to sync the model records.
        group_models (list): The Thunderstorm auth group models to synchronize.
        ensure_exchange_exists (bool): Whether to error if exchange does not
                                       exist.
    """
    _register_task_queue(
        celery_app, group_models, ensure_exchange_exists
    )
    _register_sync_tasks(celery_app, db_session, group_models)


def _register_task_queue(celery_app, group_models, ensure_exchange_exists):
    """Create and register the service's auth group sync queue to the
    ts_auth.sync exchange.

    Args:
        celery_app (Celery): The service's `Celery` app instance.
        group_models (list): List of all the group models the service
            subscribes to.
    """
    # asserts that the exchange exists
    LEGACY_EXCHANGE.declare(
        passive=ensure_exchange_exists,
        channel=celery_app.broker_connection().channel()
    )
    EXCHANGE.declare(
        passive=ensure_exchange_exists,
        channel=celery_app.broker_connection().channel()
    )

    routing_keys = _routing_keys(group_models)
    bindings = itertools.chain(
        _bindings(EXCHANGE, routing_keys),
        _bindings(LEGACY_EXCHANGE, routing_keys),
    )

    queue = _service_task_queue(celery_app, bindings)

    celery_app.conf.task_queues = celery_app.conf.task_queues or []
    celery_app.conf.task_queues.append(queue)


def _service_task_queue(celery_app, bindings):
    """Create the queue which group sync tasks will be consumed from.

    Args:
        celery_app (Celery): The service's `Celery` app instance.

    Returns:
        kombu.Queue: Queue that group sync tasks will be published to.
    """
    queue_name = '{}.ts_auth.group'.format(celery_app.main)
    return kombu.Queue(queue_name, list(bindings))


def _register_sync_tasks(celery_app, db_session, group_models):
    """Create Celery tasks for syncing each group model and register with the
    Celery app.

    Args:
        celery_app (Celery): The service's `Celery` app instance.
        db_session (Session): The service's (scoped) database session
        group_models (list): List of all the group models the service
            subscribes to.
    """
    for group_model in group_models:
        sync_task = group_sync_task(group_model, db_session)
        celery_app.register_task(sync_task)


def _routing_keys(group_models):
    return [
        group_model.__ts_group_type__.routing_key
        for group_model in group_models
    ]


def _bindings(exchange, routing_keys):
    return [
        kombu.binding(exchange, routing_key=routing_key)
        for routing_key in routing_keys
    ]


@signals.worker_ready.connect
def do_ready(sender, **kwargs):
    if 'ts_auth.permissions.sync' in sender.app.tasks:
        sender.app.tasks['ts_auth.permissions.sync'].delay()


def init_permissions(celery_app, db_session, permission_model):
    """
    Initialize a Celery app with the permission syncing task

    Args:
        celery_app (Celery): Celery app to register the sync task with
        db_session (Session): SQLAlchemy session
        permission_model (Permission): SQLAlchemy declarative permissions model
    """
    task = permission_sync_task(permission_model, db_session)
    celery_app.register_task(task)
