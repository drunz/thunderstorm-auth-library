from thunderstorm_auth.tasks import group_sync_task


def init_group_sync_tasks(celery_app, db_session, group_models):
    """Initialize a Celery app with sync tasks for auth group models.

    For each group model, registers the model's queue to subscribe to and
    creates and registers the sync task.

    Args:
        celery_app (Celery): Celery app to register the sync tasks with.
        db_session (Session): Database session used to sync the model records.
        group_models (list): The Thunderstorm auth group models to synchronize.
    """

    if not celery_app.conf.task_queues:
        celery_app.conf.task_queues = []

    for group_model in group_models:
        group_type = group_model.__ts_group_type__
        celery_app.conf.task_queues.append(group_type.queue)

        sync_task = group_sync_task(
            model=group_model,
            db_session=db_session
        )
        celery_app.register_task(sync_task)
