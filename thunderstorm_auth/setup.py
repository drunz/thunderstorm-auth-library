from kombu import Exchange, Queue, binding

from thunderstorm_auth.roles import _init_role_tasks, _role_task_routing_key
from thunderstorm_auth.groups import _init_group_tasks, _complex_group_task_routing_key
from thunderstorm_auth.permissions import _init_permission_tasks


def init_ts_auth_tasks(celery_app, datastore):
    """
    Initialize a Celery app with a queue and sync tasks for auth group models and roles.

    Args:
        celery_app (Celery): Celery app to register the sync tasks with.
        datastore (AuthStore): a datastore
    """
    messaging_exchange = Exchange('ts.messaging')
    bindings = (
        binding(messaging_exchange, routing_key=routing_key)
        for routing_key in [_complex_group_task_routing_key(), _role_task_routing_key()]
    )

    celery_app.conf.task_queues = celery_app.conf.task_queues or []

    celery_app.conf.task_queues.append(
        Queue('{}.ts_auth.group'.format(celery_app.main), list(bindings))
    )

    _init_group_tasks(datastore)
    _init_role_tasks(datastore)


def init_permissions(datastore):
    """
    Initialize a Celery app with the permission syncing task

    Args:
        celery_app (Celery): Celery app to register the sync task with
        db_session (Session): SQLAlchemy session
        permission_model (Permission): SQLAlchemy declarative permissions model
    """
    _init_permission_tasks(datastore)
