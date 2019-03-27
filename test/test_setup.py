from thunderstorm_auth.setup import init_ts_auth_tasks, init_permissions


def test_init_group_sync_tasks(celery_app, datastore):
    # arrange
    init_ts_auth_tasks(celery_app, datastore)

    # assert
    assert 'handle_role_data' in celery_app.tasks
    assert 'auth.request_groups_republish' in celery_app.tasks
    assert 'auth.request_groups_republish' in celery_app.tasks
    assert 'thunderstorm_auth.roles.create_role_permission_associations_if_not_exist' in celery_app.tasks
    assert 'thunderstorm_auth.roles.create_role_if_not_exists' in celery_app.tasks
    assert 'thunderstorm_auth.groups.add_group_association' in celery_app.tasks
    assert 'thunderstorm_auth.roles.create_role_permission_association_if_not_exists' in celery_app.tasks
    assert 'ts_auth.group.complex.sync' in celery_app.tasks
    assert 'thunderstorm_auth.roles.remove_role_orphan_permission_associations' in celery_app.tasks
    assert 'thunderstorm_auth.groups.delete_group_association' in celery_app.tasks


def test_init_permissions(celery_app, datastore):
    # arrange
    init_permissions(datastore)

    # assert
    assert 'ts_auth.permissions.sync' in celery_app.tasks
