import celery
from sqlalchemy.exc import SQLAlchemyError


def group_sync_task(model, db_session):
    """Create a sync task for a group model.

    Creates a task which is not registered with any app. The task should be
    created and registered to an app using
    `thunderstorm_auth.setup.init_group_sync_tasks`.

    Task takes two args, `group_uuid`, `members`: the UUID of the group to
    update and a list of UUIDs of the latest members of that group. The task
    updates the members by adding new member records and deleting ones no
    longer reported.

    Args:
        model (Base): Group association model to define the task for.
        db_session: Session object used to perform the inserts/deletes.

    Returns:
        Task: Celery task to sync group data.
    """
    task_name = model.__ts_group_type__.task_name

    @celery.task(name=task_name)
    def sync_group_data(group_uuid, members):
        """Synchronizes group membership data.

        Updates the group membership by adding new member records and deleting
        ones no longer reported.

        Args:
            group_uuid (UUID): UUID of group to synchronize.
            members (list): list of UUIDs of desired group members.
        """
        current_members = get_current_members(db_session, model, group_uuid)
        latest_members = set(members)

        removed = current_members - latest_members
        added = latest_members - current_members

        if removed:
            delete_group_associations(
                db_session,
                model,
                group_uuid,
                removed
            )
        if added:
            add_group_associations(
                db_session,
                model,
                group_uuid,
                added
            )
        try:
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            raise

    return sync_group_data


def get_current_members(db_session, model, group_uuid):
    """The current members of a group.

    Args:
        db_session (Session): Database session used to query the records.
        model (Base): Group association model being queried.
        group_uuid (UUID): UUID of the group whose members to fetch

    Returns:
        set: Set of UUIDs of current members.
    """
    members = db_session.query(
        model
    ).filter(
        model.group_uuid == group_uuid
    )

    def member_column(item):
        member_column_name = model.__ts_group_type__.member_column_name
        return getattr(item, member_column_name)

    return {
        member_column(member)
        for member in members
    }


def delete_group_associations(db_session, model, group_uuid, removed):
    """Delete group members.

    Args:
        db_session (Session): Database session used to delete the records.
        model (Base): Group association model being updated.
        group_uuid (UUID): UUID of the group whose members to fetch
        removed (set): UUIDs of members being removed.
    """
    member_column = getattr(model, model.__ts_group_type__.member_column_name)

    db_session.query(
        model
    ).filter(
        model.group_uuid == group_uuid,
        member_column.in_(removed)
    ).delete(
        synchronize_session=False
    )


def add_group_associations(db_session, model, group_uuid, added):
    """Add members to a group.

    Args:
        db_session (Session): Database session used to create the records.
        model (Base): Group association model being updated.
        group_uuid (UUID): UUID of the group whose members to fetch
        added (set): UUIDs of members being added.
    """
    db_session.bulk_insert_mappings(model, [
        {
            'group_uuid': group_uuid,
            model.__ts_group_type__.member_column_name: member_id
        }
        for member_id in added
    ])
