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
    # If task_queues is None, default queue is used,
    # manually add here so we don't exclude.
    # Override value before calling init_group_sync_tasks to prevent this.
    if celery_app.conf.task_queues is None:
        celery_app.conf.task_queues = [
            kombu.Queue(celery_app.conf.task_default_queue)
        ]

    routing_keys = [
        group_model.__ts_group_type__.routing_key
        for group_model in group_models
    ]
    sync_queue = group_sync_queue(
        celery_main=celery_app.main,
        routing_keys=routing_keys
    )
    celery_app.conf.task_queues.append(sync_queue)


def _register_sync_tasks(celery_app, db_session, group_models):
    for group_model in group_models:
        sync_task = group_sync_task(
            model=group_model,
            db_session=db_session
        )
        celery_app.register_task(sync_task)


def group_sync_queue(celery_main, routing_keys):
    """Create the queue which group sync tasks will be consumed from.

    Args:
        celery_main (str): Value of `celery_app.main` for the service adding
            the queue.
        routing_keys (list): Routing keys with which to bind to the exchange.

    Returns:
        kombu.Queue: Queue that group sync tasks will be published to.
    """
    return kombu.Queue(
        '{celery_main}.ts_auth.group'.format(celery_main=celery_main),
        [
            kombu.binding(EXCHANGE, routing_key=routing_key)
            for routing_key in routing_keys
        ]
    )
