from unittest.mock import patch, call, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import DBAPIError

from test.models import ComplexGroupComplexAssociation


@patch('thunderstorm_auth.groups.group')
def test_handle_group_data(m_group, db_session, celery, fixtures):
    handle_group_data = celery.tasks['ts_auth.group.complex.sync']

    m_add_group_association = MagicMock()
    m_delete_group_association = MagicMock()

    group_uuid = uuid4()
    new_uuid = uuid4()
    complex_uuids = [fixtures.ComplexGroupComplexAssociation(group_uuid=group_uuid).complex_uuid for _ in range(4)]

    with patch.dict(
        celery.tasks,
        {
            'thunderstorm_auth.groups.add_group_association': m_add_group_association,
            'thunderstorm_auth.groups.delete_group_association': m_delete_group_association
        }
    ):
        handle_group_data(group_uuid, [new_uuid] + complex_uuids[:2])

    m_delete_group_association.si.assert_has_calls([call(group_uuid, str(c)) for c in complex_uuids[2:]], any_order=True)
    m_add_group_association.si.assert_called_once_with(group_uuid, str(new_uuid))


def test_add_group_association_creates_group_association(db_session, celery, fixtures):
    add_group_association = celery.tasks['thunderstorm_auth.groups.add_group_association']

    group_uuid = uuid4()
    complex_uuid = uuid4()
    [fixtures.ComplexGroupComplexAssociation(group_uuid=group_uuid) for _ in range(4)]

    assert db_session.query(ComplexGroupComplexAssociation).count() == 4

    add_group_association(group_uuid, complex_uuid)

    assert db_session.query(ComplexGroupComplexAssociation).count() == 5



def test_add_group_association_fails_if_group_association_exists(db_session, celery, fixtures):
    add_group_association = celery.tasks['thunderstorm_auth.groups.add_group_association']

    group_uuid = uuid4()
    complex_uuid = uuid4()
    fixtures.ComplexGroupComplexAssociation(group_uuid=group_uuid, complex_uuid=complex_uuid)

    assert db_session.query(ComplexGroupComplexAssociation).count() == 1

    with pytest.raises(DBAPIError):
        add_group_association(group_uuid, complex_uuid)
        assert db_session.query(ComplexGroupComplexAssociation).count() == 1



def test_delete_group_association_deletes_group_association(db_session, celery, fixtures):
    delete_group_association = celery.tasks['thunderstorm_auth.groups.delete_group_association']

    group_uuid = uuid4()
    complex_uuid = uuid4()
    fixtures.ComplexGroupComplexAssociation(group_uuid=group_uuid, complex_uuid=complex_uuid)

    assert db_session.query(ComplexGroupComplexAssociation).count() == 1

    delete_group_association(group_uuid, complex_uuid)

    assert db_session.query(ComplexGroupComplexAssociation).count() == 0



def test_delete_group_association_keeps_going_if_group_association_does_not_exists(db_session, celery, fixtures):
    delete_group_association = celery.tasks['thunderstorm_auth.groups.delete_group_association']

    group_uuid = uuid4()
    complex_uuid = uuid4()

    assert db_session.query(ComplexGroupComplexAssociation).count() == 0

    delete_group_association(group_uuid, complex_uuid)

    assert db_session.query(ComplexGroupComplexAssociation).count() == 0
