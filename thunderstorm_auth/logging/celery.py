import logging

import celery
from celery import Task as CeleryTask
from celery._state import get_current_task

from . import JSONFormatter, get_request_id, _register_id_getter


_CELERY_X_HEADER = 'x_request_id'


def get_celery_request_id(request=None):
    if not request:
        task = get_current_task()
        if task and task.request:
            request = task.request
    if request:
        return request.get(_CELERY_X_HEADER, None)


_register_id_getter(get_celery_request_id)


class CeleryTaskFilter(logging.Filter):
    """Celery logging filter

    This adds in the task name and ID and also the request ID if it was
    added by the `CeleryRequestIDTask'
    """
    def filter(self, record):
        task = get_current_task()
        if task and task.request:
            record.task_id = task.request.id
            record.request_id = get_celery_request_id(task.request)
            record.task_name = task.name
        else:
            record.task_id = '???'
            record.request_id = None
            record.task_name = '???'

        return record


class CeleryRequestIDTask(CeleryTask):
    """Celery Task that adds request ID header

    This adds the request ID as a celery header so that it can be logged
    in celery task logs
    """
    def apply_async(self, *args, **kwargs):
        kwargs.setdefault('headers', {})
        request_id = get_request_id()
        kwargs['headers'][_CELERY_X_HEADER] = request_id

        return super().apply_async(*args, **kwargs)


def on_celery_setup_logging(service_name):
    """Set up celery logging

    This should be hooked up to the celery `setup_logging` signal to
    override celery's logging
    """
    def _get_celery_handler(log_format):
        handler = logging.StreamHandler()
        formatter = JSONFormatter(
            log_format,
            ts_log_type='celery',
            ts_service=service_name
        )
        handler.setFormatter(formatter)

        return handler

    def do_setup_logging(**kwargs):
        logging.getLogger().addHandler(
            _get_celery_handler('%(name)s %(levelname)s %(message)s')
        )

        handler = _get_celery_handler(
            '[%(levelname)s/%(processName)s] %(message)s'
        )
        celery.utils.log.worker_logger.addHandler(handler)
        celery.utils.log.worker_logger.propagate = False

        handler = _get_celery_handler(
            '[%(levelname)s/%(processName)s]'
            '%(task_name)s %(task_id)s %(message)s'
        )
        handler.addFilter(CeleryTaskFilter())
        celery.utils.log.task_logger.addHandler(handler)
        celery.utils.log.task_logger.propagate = False

    return do_setup_logging
