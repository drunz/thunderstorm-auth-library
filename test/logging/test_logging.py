import pytest

from thunderstorm_auth import logging


def test_get_request_id_with_no_getters():
    # arrange
    del logging._ID_GETTERS[:]

    # assert
    assert logging.get_request_id() is None


def test_get_request_id_with_one_getter():
    # arrange
    del logging._ID_GETTERS[:]
    logging._register_id_getter(lambda: 'one')

    # assert
    assert logging.get_request_id() == 'one'


def test_get_request_id_with_two_getters():
    # arrange
    del logging._ID_GETTERS[:]
    logging._register_id_getter(lambda: 'one')
    logging._register_id_getter(lambda: 'two')

    # assert
    assert logging.get_request_id() == 'one'


class TestJSONFormatter:
    def test_required_fields_are_added(self, formatter, record):
        # arrange
        log_record = {}

        # act
        formatter.add_fields(log_record, record, {})

        # assert
        assert log_record['name'] == 'test.name'
        assert log_record['levelname'] == 'INFO'
        assert log_record['pathname'] == '/example/path.py'
        assert log_record['lineno'] == 123

    def test_missing_required_fields_cause_failure(self, formatter, record):
        # arrange
        log_record = {}
        delattr(record, 'name')

        # assert
        with pytest.raises(AttributeError):
            formatter.add_fields(log_record, record, {})

    def test_grouping_fields_are_added(self, formatter, record):
        # arrange
        formatter = logging.JSONFormatter(
            '%(message)s',
            ts_log_type='test-type',
            ts_service='test-service'
        )
        log_record = {}

        # act
        formatter.add_fields(log_record, record, {})

        # assert
        assert log_record['service'] == 'test-service'
        assert log_record['log_type'] == 'test-type'

    def test_grouping_fields_defaults(self, formatter, record):
        # arrange
        log_record = {}

        # act
        formatter.add_fields(log_record, record, {})

        # assert
        assert log_record['service'] == 'unknown'
        assert log_record['log_type'] == 'unknown'

    def test_request_id_is_added_if_present(self, formatter, record):
        # arrange
        log_record = {}
        record.request_id = 'test-id'

        # act
        formatter.add_fields(log_record, record, {})

        # assert
        assert log_record['request_id']
        assert log_record['data']['request_id']

    def test_request_id_is_not_added_if_missing(self, formatter, record):
        # arrange
        log_record = {}

        # act
        formatter.add_fields(log_record, record, {})

        # assert
        assert 'request_id' not in log_record
        assert 'data' not in log_record

    def test_timestamp_is_added(self, formatter, record):
        # arrange
        log_record = {}

        # act
        formatter.add_fields(log_record, record, {})

        # assert
        assert 'timestamp' in log_record
