"""Module for integrating JSON logging with Flask

Usage:
    >>> from flask import Flask
    >>> from thunderstorm_auth.logging.flask import init_app as init_logging
    >>>
    >>> app = Flask(__init__)
    >>> init_logging(app)
"""
import logging
import os
import uuid

from flask import g, request, Flask
from flask.ctx import has_request_context

from . import JSONFormatter, _register_id_getter

__all__ = ['init_app']


def get_flask_request_id():
    """Return the request ID from the Flask request context

    If there is a Flask request context but there is no ``request_id``
    then first we look for a ``TS-Request-ID`` header. If that is also
    not there we generate a new string uuid4.

    Importing this module will register this getter with ``get_request_id``.

    Returns:
        str: the current request ID
    """
    if has_request_context():
        if 'request_id' not in g:
            g.request_id = request.headers.get('TS-Request-ID', str(uuid.uuid4()))
        return g.request_id


_register_id_getter(get_flask_request_id)


def init_app(app: Flask):
    """Initialise logging on a Flask app

    Usage:
        >>> init_app(app)
    """
    handler = logging.StreamHandler()
    log_format = '%(levelname)s %(message)s'

    if 'WERKZEUG_SERVER_FD' in os.environ:
        # Use human readable log formatter when using the Werkzeug dev server
        formatter = logging.Formatter(log_format)
    else:
        formatter = JSONFormatter(
            log_format, ts_log_type='flask', ts_service=app.config.get('TS_SERVICE_NAME', 'unknown')
        )

    handler.setFormatter(formatter)
    handler.addFilter(FlaskRequestIdFilter())

    root_logger = logging.getLogger()
    del root_logger.handlers[:]
    root_logger.addHandler(handler)

    del app.logger.handlers[:]
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    init_after_request(app)


def init_after_request(app: Flask):
    """Initialise logging after request handler on a Flask app

    This handler adds a Flask access log
    """

    @app.after_request
    def after_request(response):
        level = _get_level(response)
        extra = {
            'method': request.method,
            'url': request.url,
            'status': response.status_code,
        }
        app.logger.log(
            level,
            '{method} {url} {status}'.format(**extra),
            extra=extra,
        )
        response.headers['TS-Request-ID'] = get_flask_request_id()

        return response


def _get_level(response):
    """Get logging level from a Flask response"""
    return logging.ERROR if response.status_code // 100 == 5 else logging.INFO


class FlaskRequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_flask_request_id()

        return record


class FlaskJSONFormatter(JSONFormatter):
    """An all in one logging formatter for Flask

    This combines the JSONFormatter and the FlaskRequestIdFilter for
    environments where Filters such as ini file config (gunicorn logging
    relies on this heavily).
    """
    flask_request_id_filter = FlaskRequestIdFilter()

    def _add_request_id(self, log_record, record):
        record = self.flask_request_id_filter.filter(record)
        return super()._add_request_id(log_record, record)
