from thunderstorm_auth import TOKEN_HEADER, DEFAULT_LEEWAY
from thunderstorm_auth.utils import load_jwks_from_file
from thunderstorm_auth.flask.cli import _permissions, _list_permissions, _update_permissions


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

    def __init__(self, app=None, datastore=None, jwks_path='config/jwks.json', func_get_roles=None, **kwargs):
        """
        Args:
            app (Flask app object): flask application we want to use the ts auth on
            datastore (AuthDatastore object): datastore used for the auth data retrieval
            jwks_path (str): relative path to the private keys
        """
        if all([app, datastore, jwks_path]):
            self.init_app(app, datastore, jwks_path)

    def _set_default_config(self, app, jwks_path):
        jwks = load_jwks_from_file(jwks_path)

        app.config.setdefault('TS_AUTH_SECRET_KEY', app.config.get('SECRET_KEY'))
        app.config.setdefault('TS_AUTH_LEEWAY', DEFAULT_LEEWAY)
        app.config.setdefault('TS_AUTH_TOKEN_HEADER', TOKEN_HEADER)
        app.config.setdefault('TS_AUTH_JWKS', jwks)

    @property
    def state(self):
        """
        Return the state of the extension, useful to be used in other parts of a flask app
        """
        return TsAuthState(self.app, self.datastore)

    def init_app(self, app, datastore, jwks_path):
        """
        Initialize the extension
        """
        self._set_default_config(app, jwks_path)
        self.app = app
        self.datastore = datastore

        group = app.cli.group(name='permissions')(_permissions())
        group.command(name='list')(_list_permissions(datastore.db_session, datastore.permission_model))
        group.command(name='update')(_update_permissions(app, datastore.db_session, datastore.permission_model))

        app.extensions['ts_auth'] = self.state


def init_ts_auth(app=None, datastore=None, jwks_path='config/jwks.json', **kwargs):
    return TsAuth(app, datastore, jwks_path, **kwargs)
