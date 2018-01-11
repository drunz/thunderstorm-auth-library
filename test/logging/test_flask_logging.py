from unittest import mock

from flask import g

from thunderstorm_auth.logging.flask import (
    get_flask_request_id,
    FlaskRequestIdFilter,
    FlaskJSONFormatter,
)


def test_flask_request_id_from_global(flask_app):
    with flask_app.test_request_context('/'):
        g.request_id = 'global-request-id'

        assert get_flask_request_id() == 'global-request-id'


def test_flask_request_id_from_header(flask_app):
    headers = {
        'TS-Request-ID': 'header-request-id'
    }
    with flask_app.test_request_context('/', headers=headers):
        assert get_flask_request_id() == 'header-request-id'


@mock.patch('thunderstorm_auth.logging.flask.uuid.uuid4')
def test_flask_request_id_from_new(mock_uuid4, flask_app):
    with flask_app.test_request_context('/'):
        mock_uuid4.return_value = 'new-request-id'

        assert get_flask_request_id() == 'new-request-id'


def test_flask_request_id_filter(flask_app, record):
    with flask_app.test_request_context('/'):
        g.request_id = 'global-request-id'

        filter = FlaskRequestIdFilter()
        record = filter.filter(record)

        assert record.request_id == 'global-request-id'


def test_flask_json_formatter(flask_app, record):
    with flask_app.test_request_context('/'):
        g.request_id = 'global-request-id'

        formatter = FlaskJSONFormatter('%(message)s')

        log_record = {}

        formatter.add_fields(log_record, record, {})

        assert log_record['request_id'] == 'global-request-id'
