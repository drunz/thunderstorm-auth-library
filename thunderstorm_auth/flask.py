from functools import wraps
import uuid

from flask import g
import click

from thunderstorm_auth import TOKEN_HEADER, DEFAULT_LEEWAY
from thunderstorm_auth.decoder import decode_token
from thunderstorm_auth import permissions
from thunderstorm_auth.exceptions import (
    TokenError, TokenHeaderMissing, AuthJwksNotSet, ThunderstormAuthError,
    ExpiredTokenError, InsufficientPermissions
)
from thunderstorm_auth.user import User

try:
    from flask import current_app, jsonify, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


FLASK_JWKS = 'TS_AUTH_JWKS'
FLASK_LEEWAY = 'TS_AUTH_LEEWAY'


def ts_auth_required(func=None, *, with_permission=None):
    """Flask decorator to check the authentication token X-Thunderstorm-Key

    If token decode fails for any reason, an an error is logged and a 401
    Unauthorized is returned to the caller.

    Args:
        func (Callable):       View to decorate
        with_permission (str): Permission string required for this view

    Raises:
        ThunderstormAuthError: If Flask is not installed.
    """
    if not HAS_FLASK:
        raise ThunderstormAuthError(
            'Cannot decorate Flask route as Flask is not installed.'
        )

    if with_permission is not None:
        permissions.register_permission(with_permission)

    def wrapper(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            try:
                decoded_token_data = _decode_token()
                _validate_permission(decoded_token_data, with_permission)
            except (TokenError, InsufficientPermissions) as error:
                return _bad_token(error)

            g.user = User.from_decoded_token(decoded_token_data)
            return func(*args, **kwargs)

        return decorated_function

    if callable(func):
        return wrapper(func)
    elif func is None:
        return wrapper
    else:
        raise ThunderstormAuthError('Non-callable provided for decorator')


def _decode_token():
    token = _get_token()
    jwks = _get_jwks()
    leeway = current_app.config.get(FLASK_LEEWAY, DEFAULT_LEEWAY)
    return decode_token(token, jwks, leeway)


def _get_token():
    token = request.headers.get(TOKEN_HEADER)
    if token is None:
        raise TokenHeaderMissing()
    return token


def _get_jwks():
    try:
        current_app.config[FLASK_JWKS]['keys']
        return current_app.config[FLASK_JWKS]
    except KeyError:
        message = (
            '{} missing from Flask config or JWK set not structured '
            'correctly'
        ).format(FLASK_JWKS)

        raise AuthJwksNotSet(message)


def _validate_permission(token_data, permission):
    if permission:
        service_name = current_app.config['TS_SERVICE_NAME']
        permissions.validate_permission(token_data, service_name, permission)


def _bad_token(error):
    if isinstance(error, ExpiredTokenError):
        current_app.logger.info(error)
    else:
        current_app.logger.error(error)
    status_code = 403 if isinstance(error, InsufficientPermissions) else 401
    return jsonify(message=str(error)), status_code


def init_auth(app, db_session, permission_model):
    group = app.cli.group(name='permissions')(_permissions)
    group.command(name='list')(
        _list_permissions(db_session, permission_model)
    )
    group.command(name='update')(
        _update_permissions(app, db_session, permission_model)
    )


def _permissions():
    """Manage auth permissions"""


def _needs_update(perms):
    return any(
        perms[key] for key in ['to_insert', 'to_undelete', 'to_delete']
    )


def _list_permissions(db_session, permission_model):
    def _action():
        """List permissions used in this service"""
        perms = permissions.get_permissions_info(db_session, permission_model)

        click.echo('Permissions in use')
        click.echo('-----------------')
        for permission in perms['registered']:
            click.echo(permission)

        click.echo('')
        click.echo('Permissions in DB')
        click.echo('-----------------')
        click.echo(f'{"uuid":38} {"permission":15} {"sent":6} {"deleted":6}')
        for p in perms['db']:
            click.echo(
                f'{str(p.uuid):38} {p.permission:15} '
                f'{p.is_sent}  {p.is_deleted}'
            )

        if _needs_update(perms):
            click.echo(
                '\nAN UPDATE IS NEEDED RUN: \n> flask permissions update'
            )
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

            config = Config(file_='alembic.ini', ini_section='alembic')
            script_directory = ScriptDirectory.from_config(config)
            upgrade = ops.UpgradeOps(
                [
                    ops.ExecuteSQLOp(
                        f"INSERT INTO permission (uuid, service_name, permission) VALUES ('{str(uuid.uuid4())}'::uuid, '{service_name}', '{permission}')"  # noqa
                    ) for permission in perms['to_insert']
                ] + [
                    ops.ExecuteSQLOp(
                        f"UPDATE permission SET is_deleted=false, is_sent=false WHERE uuid = '{p_uuid}'::uuid"  # noqa
                    ) for p_uuid in perms['to_undelete']
                ] + [
                    ops.ExecuteSQLOp(
                        f"UPDATE permission SET is_deleted=true, is_sent=false WHERE uuid = '{p_uuid}'::uuid"  # noqa
                    ) for p_uuid in perms['to_delete']
                ]
            )
            downgrade = ops.DowngradeOps(
                [
                    ops.ExecuteSQLOp(
                        f"DELETE FROM permission WHERE permission = '{permission}'"  # noqa
                    ) for permission in perms['to_insert']
                ] + [
                    ops.ExecuteSQLOp(
                        f"UPDATE permission SET is_deleted=true, is_sent=false WHERE uuid = '{p_uuid}'::uuid"  # noqa
                    ) for p_uuid in perms['to_undelete']
                ] + [
                    ops.ExecuteSQLOp(
                        f"UPDATE permission SET is_deleted=false, is_sent=false WHERE uuid = '{p_uuid}'::uuid"  # noqa
                    ) for p_uuid in perms['to_delete']
                ]
            )
            kwargs = {
                upgrade.upgrade_token: render_python_code(upgrade),
                downgrade.downgrade_token: render_python_code(downgrade),
            }
            script_directory.generate_revision(
                alembic_rev_id(),
                'updating auth permissions',
                refresh=True,
                head='head', splice=None,
                **kwargs
            )

    return _action
