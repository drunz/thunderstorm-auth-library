from sqlalchemy import and_

from thunderstorm_auth.exceptions import InsufficientPermissions


def filter_for_user(query, user, group_assoc_model, join_column):
    """Filter a query based on a user's groups.

    Args:
        query (Query): Query to filter.
        user (User): User querying results.
        group_assoc_model (Base): The group association model to join to in
            the query.
        join_column (InstrumentedAttribute): The column the group association
            table will join on.

    Returns:
        Query: Filtered query
    """
    group_type = group_assoc_model.__ts_group_type__

    # TODO:
    # When more group types are created, the groups will need to be grouped
    # by group type. Will be wasteful to filter by all the user's groups.

    if not user.groups:
        # saves performing an expensive `WHERE col IN ()` query
        raise InsufficientPermissions('User has no group associations.')

    group_member_column = getattr(
        group_assoc_model,
        group_type.member_column_name
    )
    return query.join(
        group_assoc_model,
        and_(
            group_member_column == join_column,
            group_assoc_model.group_uuid.in_(user.groups)
        )
    )
