"""Core JSON logging module

You probably do not want to use this directly.
See:
    thunderstorm_auth.logging.flask
    thunderstorm_auth.logging.celery
"""
import datetime

from pythonjsonlogger.jsonlogger import JsonFormatter as BaseJSONFormatter


__all__ = [
    'JSONFormatter', 'get_request_id'
]


REQUIRED_FIELDS = [
    'name', 'levelname', 'pathname', 'lineno'
]


class JSONFormatter(BaseJSONFormatter):
    """JSON logging Formatter for Thunderstorm apps

    Adds thunderstorm fields to JSON logging
    """
    def __init__(self, *args, **kwargs):
        self._ts_log_type = kwargs.pop('ts_log_type', 'unknown')
        self._ts_service = kwargs.pop('ts_service', 'unknown')
        super().__init__(*args, **kwargs)

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record = self._add_required_fields(log_record, record)
        log_record = self._add_grouping_fields(log_record, record)
        log_record = self._add_request_id(log_record, record)
        log_record = self._add_timestamp(log_record, record)

    def _add_required_fields(self, log_record, record):
        log_record.update({
            name: getattr(record, name) for name in REQUIRED_FIELDS
        })

        return log_record

    def _add_grouping_fields(self, log_record, record):
        log_record.update({
            'service': self._ts_service,
            'log_type': self._ts_log_type,
        })

        return log_record

    def _add_request_id(self, log_record, record):
        if getattr(record, 'request_id', None):
            log_record['request_id'] = record.request_id
            log_record.setdefault('data', {})
            log_record['data']['request_id'] = record.request_id

        return log_record

    def _add_timestamp(self, log_record, record):
        log_record['timestamp'] = datetime.datetime.utcnow().isoformat()

        return log_record


_ID_GETTERS = []


def _register_id_getter(getter):
    _ID_GETTERS.append(getter)


def get_request_id():
    """Return the current request ID

    Return the current request ID from whichever ID getters have been
    registered. An ID getter is registered when it's module is included.
    For example; if the ``thunderstorm_auth.logging.flask`` module is imported
    the ``get_flask_request_id`` is registered.

    Returns:
        str the current request ID
    """
    for getter in _ID_GETTERS:
        request_id = getter()
        if request_id:
            return request_id
