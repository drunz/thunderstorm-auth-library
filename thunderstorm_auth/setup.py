import kombu

from thunderstorm_auth.tasks import group_sync_task


EXCHANGE = kombu.Exchange('ts_auth.group')


def init_group_sync_tasks(celery_app, db_session, group_models):
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
    """
    _register_task_queue(celery_app, group_models)
    _register_sync_tasks(celery_app, db_session, group_models)


def _register_task_queue(celery_app, group_models):
    """Create and register the service's auth group sync queue to the
    ts_auth.sync exchange.

    Args:
        celery_app (Celery): The service's `Celery` app instance.
        group_models (list): List of all the group models the service
            subscribes to.
    """
    # asserts that the exchange exists
    EXCHANGE.declare(
        passive=True,
        channel=celery_app.broker_connection().channel()
    )

    routing_keys = _routing_keys(group_models)
    bindings = _bindings(EXCHANGE, routing_keys)

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
    return (
        group_model.__ts_group_type__.routing_key
        for group_model in group_models
    )


def _bindings(exchange, routing_keys):
    return (
        kombu.binding(exchange, routing_key=routing_key)
        for routing_key in routing_keys
    )
