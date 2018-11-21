from unittest import mock

from thunderstorm_auth.logging.celery import (get_celery_request_id, CeleryTaskFilter)


@mock.patch('thunderstorm_auth.logging.celery.get_current_task')
def test_celery_request_id(mock_get_current_task):
    # arrange
    mock_request = mock.Mock()
    mock_request.get.return_value = 'request-id'
    mock_task = mock.Mock()
    mock_task.request = mock_request
    mock_get_current_task.return_value = mock_task

    # assert
    assert get_celery_request_id() == 'request-id'
    mock_request.get.assert_called_with('x_request_id', None)


def test_celery_request_id_passed_in_request():
    # arrange
    mock_request = mock.Mock()
    mock_request.get.return_value = 'request-id'
    mock_task = mock.Mock()
    mock_task.request = mock_request

    # assert
    assert get_celery_request_id(mock_request) == 'request-id'
    mock_request.get.assert_called_with('x_request_id', None)


@mock.patch('thunderstorm_auth.logging.celery.get_celery_request_id')
@mock.patch('thunderstorm_auth.logging.celery.get_current_task')
def test_celery_task_filter_with_task_and_request(mock_get_current_task, mock_get_celery_request_id, record):
    # arrange
    mock_task = mock.Mock()
    mock_task.request = mock.Mock()
    mock_task.request.id = 'task-id'
    mock_task.name = 'task-name'
    mock_get_celery_request_id.return_value = 'request-id'
    mock_get_current_task.return_value = mock_task
    filter = CeleryTaskFilter()

    # act
    record = filter.filter(record)

    # assert
    assert record.task_id == 'task-id'
    assert record.request_id == 'request-id'
    assert record.task_name == 'task-name'


@mock.patch('thunderstorm_auth.logging.celery.get_current_task')
def test_celery_task_filter_with_no_task(mock_get_current_task, record):
    # arrange
    mock_get_current_task.return_value = None
    filter = CeleryTaskFilter()

    # act
    record = filter.filter(record)

    # assert
    assert record.task_id is None
    assert record.request_id is None
    assert record.task_name is None


@mock.patch('thunderstorm_auth.logging.celery.get_current_task')
def test_celery_task_filter_with_task_no_request(mock_get_current_task, record):
    # arrange
    mock_task = mock.Mock()
    mock_task.request = None
    mock_get_current_task.return_value = mock_task
    filter = CeleryTaskFilter()

    # act
    record = filter.filter(record)

    # assert
    assert record.task_id is None
    assert record.request_id is None
    assert record.task_name is None
