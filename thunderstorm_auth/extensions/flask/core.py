from sqlalchemy.orm import class_mapper

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
        self.app = app
        self.datastore = datastore

        app.register_blueprint(auth_api_bp)

        app.extensions['ts_auth'] = self.state


class Datastore(object):
    """
    Abstract class to handle db interfacing
    """

    def __init__(self, db_session, model, group_model):
        self.group_model = group_model
        # using private as we may need to increase the models to match/filter by
        self._models = [model]
        self.db_session = db_session

    @property
    def model(self):
        """
        Property to return the model class
        """
        return self._models[0]

    @property
    def model_pk_name(self):
        """
        Property used for convenience to return model pk name
        """
        return class_mapper(self.model).primary_key[0].name

    def get_pks(self, page=1, page_size=100):
        """
        Helper method to return paginated pk values of the model

        # TODO @ashipperizer add model as a parameter so can be useable for multiple mappings
        """
        return self.db_session.query(
            getattr(self.model, self.model_pk_name)
        ).offset((page - 1) * page_size).limit(page_size)
