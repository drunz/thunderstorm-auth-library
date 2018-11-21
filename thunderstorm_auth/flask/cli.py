import uuid

import click

from thunderstorm_auth import permissions


def _permissions():
    """Manage auth permissions"""


def _needs_update(perms):
    return any(perms[key] for key in ['to_insert', 'to_undelete', 'to_delete'])


def _list_permissions(db_session, permission_model):
    def _action():
        """List permissions used in this service"""
        perms = permissions.get_permissions_info(db_session, permission_model)

        click.echo('Permissions in use')
        click.echo('-----------------')
        for permission in perms['registered']:
            click.echo(permission)

        line_tpl = '{:38} {:15} {:6} {:6}'
        click.echo('')
        click.echo('Permissions in DB')
        click.echo('-----------------')
        click.echo(line_tpl.format('uuid', 'permission', 'sent', 'deleted'))
        for p in perms['db']:
            click.echo(line_tpl.format(str(p.uuid), p.permission, p.is_sent, p.is_deleted))

        if _needs_update(perms):
            click.echo('\nAN UPDATE IS NEEDED RUN: \n> flask permissions update')
            raise SystemExit(1)

    return _action


def _update_permissions(app, db_session, permission_model):
    def _action():
        """Create a migration to update permissions if needed"""
        service_name = app.config['TS_SERVICE_NAME']
        perms = permissions.get_permissions_info(db_session, permission_model)

        if _needs_update(perms):
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            from alembic.operations import ops
            from alembic.util import rev_id as alembic_rev_id
            from alembic.autogenerate.api import render_python_code

            insert_tpl = (
                "INSERT INTO permission "
                "(uuid, service_name, permission) VALUES "
                "('{uuid}'::uuid, '{service_name}', '{permission}')"
            )
            update_tpl = (
                "UPDATE permission "
                "SET is_sent = false, is_deleted = {is_deleted} "
                "WHERE uuid = '{uuid}'::uuid"
            )
            delete_tpl = ("DELETE FROM permission " "WHERE permission = '{permission}'")

            config = Config(file_='alembic.ini', ini_section='alembic')
            script_directory = ScriptDirectory.from_config(config)
            upgrade = ops.UpgradeOps(
                [
                    ops.ExecuteSQLOp(
                        insert_tpl.format(uuid=str(uuid.uuid4()), service_name=service_name, permission=permission)
                    ) for permission in perms['to_insert']
                ] + [
                    ops.ExecuteSQLOp(update_tpl.format(is_deleted='false', uuid=p_uuid))
                    for p_uuid in perms['to_undelete']
                ] +
                [ops.ExecuteSQLOp(update_tpl.format(is_deleted='true', uuid=p_uuid)) for p_uuid in perms['to_delete']]
            )
            downgrade = ops.DowngradeOps(
                [ops.ExecuteSQLOp(delete_tpl.format(permission=permission)) for permission in perms['to_insert']] + [
                    ops.ExecuteSQLOp(update_tpl.format(is_deleted='true', uuid=p_uuid))
                    for p_uuid in perms['to_undelete']
                ] + [
                    ops.ExecuteSQLOp(update_tpl.format(is_deleted='false', uuid=p_uuid))
                    for p_uuid in perms['to_delete']
                ]
            )
            kwargs = {
                upgrade.upgrade_token: render_python_code(upgrade),
                downgrade.downgrade_token: render_python_code(downgrade),
            }
            script_directory.generate_revision(
                alembic_rev_id(), 'updating auth permissions', refresh=True, head='head', splice=None, **kwargs
            )

    return _action
