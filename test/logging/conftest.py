import logging as pylogging

import flask
import pytest

from thunderstorm_auth import logging


@pytest.fixture
def record():
    return pylogging.LogRecord(
        'test.name', pylogging.INFO, '/example/path.py', 123, 'example message', tuple(), dict(), None
    )


@pytest.fixture
def formatter():
    return logging.JSONFormatter('%(message)s')


@pytest.fixture
def flask_app(jwk_set):
    app = flask.Flask('test_app')

    @app.route('/')
    def hello_world():
        return 'Hello, World!'

    return app
