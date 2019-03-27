from celery import shared_task, group, current_app
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from statsd.defaults.env import statsd


class ComplexGroupAssociationMixin(object):
    @declared_attr
    def __tablename__(cls):
        return 'complex_group_association'

    group_uuid = Column(UUID(as_uuid=True), primary_key=True)
    complex_uuid = Column(UUID(as_uuid=True), primary_key=True, index=True)


def _init_group_tasks(datastore):
    """
    Create and init shared tasks for handling group associations, no need to register them as they are
    shared_task

    Creates a task which is not registered with any app. The task should be
    created and registered to an app using `thunderstorm_auth.setup.init_group_sync_tasks`.

    Args:
        datastore (AuthDatastore): datastore object from the thunderstorm-auth library

    Returns:
        list: tasks needed for handling group associations
    """
    @shared_task
    @statsd.timer('tasks.delete_group_association.time')
    def delete_group_association(group_uuid, complex_uuid):
        """
        Delete group association

        Args:
            group_uuid (uuid): uuid of the group whose members to fetch
            complex_uuid (uuid): uuid of the complex to be deleted
        """
        datastore.delete_group_association(group_uuid, complex_uuid, commit=True)


    @shared_task
    @statsd.timer('tasks.add_group_associations.time')
    def add_group_association(group_uuid, complex_uuid):
        """
        Add a group association

        Args:
            group_uuid (uuid): uuid of the group whose members to fetch
            complex_uuid (uuid): uuid of the complex being added.
        """
        datastore.create_group_association(group_uuid, complex_uuid, commit=True)

    @shared_task(name='auth.request_groups_republish')
    @statsd.timer('tasks.request_group_republish.time')
    def request_groups_republish():
        """
        Request updated groups if none are present in the db
        """
        if not datastore.have_group_associations():
            current_app.send_task(
                'complex-group.republish',
                ({},),
                exchange='ts.messaging',
                routing_key='complex-group.republish'
            )

    # TODO @shipperizer: change name on the user service so that this can be standardized
    @shared_task(name='ts_auth.group.complex.sync')
    @statsd.timer('tasks.handle_group_data.time')
    def handle_group_data(group_uuid, complex_uuids):
        """
        Synchronizes group membership data.

        Updates the group membership by adding new member records and deleting
        ones no longer reported.

        Args:
            group_uuid (UUID): UUID of group to synchronize.
            complex_uuids (list): list of UUIDs of desired group members (complexes).
        """
        current_members = {str(gca.complex_uuid) for gca in datastore.get_group_associations([group_uuid])}
        latest_members = set([str(c) for c in complex_uuids])

        removed = current_members - latest_members
        added = latest_members - current_members

        group([delete_group_association.si(group_uuid, complex_uuid) for complex_uuid in removed])()
        group([add_group_association.si(group_uuid, complex_uuid) for complex_uuid in added])()

    return [handle_group_data, delete_group_association, add_group_association, request_groups_republish]


def _complex_group_task_routing_key():
    """
    Routing key for group tasks
    """
    return 'group.complex.data'
