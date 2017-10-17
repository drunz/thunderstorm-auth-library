from thunderstorm_auth import TOKEN_HEADER, DEFAULT_LEEWAY
from thunderstorm_auth.extensions.flask.routes import auth_api_bp


class TsAuthState(object):
    """
    State object so that the flask extension can be used with the pattern
    """
    def __init__(self, app, datastore):
        self.app = app
        self.datastore = datastore


class TsAuth(object):
    """
    Thunderstorm Authorization extension for flask
    """
    def __init__(self, app=None, datastore=None, **kwargs):
        self.app = app
        self.datastore = datastore

        if all([app is not None, datastore is not None]):
            self.init_app(app, datastore)

    def _set_default_config(self, app):
        app.config.setdefault('TS_AUTH_SECRET_KEY', app.config.get('SECRET_KEY'))
        app.config.setdefault('TS_AUTH_LEEWAY', DEFAULT_LEEWAY)
        app.config.setdefault('TS_AUTH_TOKEN_HEADER', TOKEN_HEADER)
        app.config.setdefault('TS_AUTH_JWKS', None)

    @property
    def state(self):
        """
        Return the state of the extension, useful to be used in other parts of a flask app
        """
        return TsAuthState(app=self.app, datastore=self.datastore)

    def init_app(self, app, datastore=None):
        """
        Initialize the extension, set the datastore and register the blueprint
        """
        self._set_default_config(app)
        self.app = app
        self.datastore = datastore

        app.register_blueprint(auth_api_bp)

        app.extensions['ts_auth'] = self.state
