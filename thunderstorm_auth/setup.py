import kombu

from thunderstorm_auth.tasks import group_sync_task, group_sync_queue


def init_group_sync_tasks(celery_app, db_session, group_models):
    """Initialize a Celery app with sync tasks for auth group models.

    For each group model, registers the model's queue to subscribe to and
    creates and registers the sync task.

    Args:
        celery_app (Celery): Celery app to register the sync tasks with.
        db_session (Session): Database session used to sync the model records.
        group_models (list): The Thunderstorm auth group models to synchronize.
    """

    # If task_queues is None, default queue is used,
    # manually add here so we don't exclude.
    # Override before calling init_group_sync_tasks to prevent this.
    if celery_app.conf.task_queues is None:
        celery_app.conf.task_queues = [
            kombu.Queue(celery_app.conf.task_default_queue)
        ]

    for group_model in group_models:
        _register_group_task_and_queue(group_model, celery_app, db_session)


def _register_group_task_and_queue(group_model, celery_app, db_session):
    group_type = group_model.__ts_group_type__

    sync_queue = group_sync_queue(
        group_type=group_type,
        celery_main=celery_app.main
    )
    celery_app.conf.task_queues.append(sync_queue)

    sync_task = group_sync_task(
        model=group_model,
        db_session=db_session
    )
    celery_app.register_task(sync_task)
