from sqlalchemy.orm import class_mapper


class Datastore(object):
    """
    Abstract class to handle db interfacing
    """

    def __init__(self, db_session, model, group_model):
        """

        Args:
            db_session (SqlAlchemy Session object): database session used for querying the db
            model (SqlAlchemy Declarative Base model): target model that is going to be related to a group
            group_model (SqlAlchemy Declarative Base model): group model used as a proxy for filtering
        """
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

        # TODO @shipperizer add model as a parameter so can be useable for multiple mappings
        """
        return self.db_session.query(
            getattr(self.model, self.model_pk_name)
        ).offset((page - 1) * page_size).limit(page_size)
