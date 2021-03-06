from flask import request, g, current_app
import logging
from thunderstorm.messaging import send_ts_task, SchemaError

from thunderstorm_auth import TOKEN_HEADER, DEFAULT_LEEWAY
from thunderstorm_auth.auditing import AuditSchema, AuditConf
from thunderstorm_auth.exceptions import TokenError
from thunderstorm_auth.utils import load_jwks_from_file
from thunderstorm_auth.flask.cli import _permissions, _list_permissions, _update_permissions
from thunderstorm_auth.flask.utils import _decode_token
from thunderstorm_auth.user import User

logger = logging.getLogger(__name__)


class TsAuthState(object):
    """
    State object so that the flask extension can be used with the flask extension pattern
    """

    def __init__(self, app, datastore):
        self.app = app
        self.datastore = datastore


class TsAuth(object):
    """
    Thunderstorm Authorization extension for flask
    """

    def __init__(self, app=None, datastore=None, jwks_path='config/jwks.json', auditing=None, **kwargs):
        """
        Args:
            app (Flask app object): flask application we want to use the ts auth on
            datastore (AuthDatastore object): datastore used for the auth data retrieval
            jwks_path (str): relative path to the private keys
            auditing (bool or AuditConf): Defines whether or not auditing is enabled for API calls
        """
        if all([app, datastore, jwks_path]):
            self.init_app(app, datastore, jwks_path, auditing=auditing, **kwargs)

    def _set_default_config(self, app, jwks_path):
        jwks = load_jwks_from_file(jwks_path)

        app.config.setdefault('TS_AUTH_SECRET_KEY', app.config.get('SECRET_KEY'))
        app.config.setdefault('TS_AUTH_LEEWAY', DEFAULT_LEEWAY)
        app.config.setdefault('TS_AUTH_TOKEN_HEADER', TOKEN_HEADER)
        app.config.setdefault('TS_AUTH_JWKS', jwks)
        app.config.setdefault('TS_AUTH_AUDIT_MSG_EXP', 3600)

    @property
    def state(self):
        """
        Return the state of the extension, useful to be used in other parts of a flask app
        """
        return TsAuthState(self.app, self.datastore)

    def init_app(self, app, datastore, jwks_path, auditing=None):
        """
        Initialize the extension
        """
        self._set_default_config(app, jwks_path)
        self.app = app
        self.datastore = datastore
        self.auditing = auditing if isinstance(auditing, AuditConf) else AuditConf(auditing)

        group = app.cli.group(name='permissions')(_permissions())
        group.command(name='list')(_list_permissions(datastore.db_session, datastore.permission_model))
        group.command(name='update')(_update_permissions(app, datastore.db_session, datastore.permission_model))

        if self.auditing.enabled:
            @app.after_request
            def after_request_auditing(response):
                if request.path in self.auditing.exclude_paths:
                    return response

                try:
                    user = g.user if hasattr(g, 'user') else User.from_decoded_token(_decode_token())
                except TokenError as exc:
                    app.logger.warning('AUDIT -- {}'.format(exc))
                else:
                    message = {
                        'method': request.method,
                        'action': request.endpoint,
                        'endpoint': request.path,
                        'username': user.username,
                        'organization_uuid': user.organization,
                        'roles': user.roles,
                        'groups': user.groups,
                        'status': response.status
                    }
                    try:
                        send_ts_task('audit.data', AuditSchema(), message, expires=current_app.config['TS_AUTH_AUDIT_MSG_EXP'])
                    except SchemaError as ex:
                        logger.error(
                            'Error sending audit message, please contact the Thunderstorm team if you see this message: {}'.format(ex)
                        )
                finally:
                    return response

        app.extensions['ts_auth'] = self.state


def init_ts_auth(app=None, datastore=None, jwks_path='config/jwks.json', auditing=False, **kwargs):
    return TsAuth(app, datastore, jwks_path, auditing=auditing, **kwargs)
