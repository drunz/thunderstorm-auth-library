from sqlalchemy.orm import class_mapper


class Datastore(object):
    """
    Base class to handle db interfacing

    associate function needs func_match to be a proper callable, matching needs to be handled
    by the user instantiating the class
    """

    def __init__(self, db_session, model, group_model, func_match=None):
        """
        Args:
            db_session (SqlAlchemy Session object): database session used for querying the db
            model (SqlAlchemy Declarative Base model): target model that is going to be related to a group
            group_model (SqlAlchemy Declarative Base model): group model used as a proxy for filtering
            func_match (callable): function used to match groups and target models, needs to be defined
                                   instantiation
        """
        self.group_model = group_model
        # using private as we may need to increase the models to match/filter by
        self._models = [model]
        self.db_session = db_session
        self.func_match = func_match

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

    def get_groups(self, page=1, page_size=100):
        """
        Helper method to return group objects (paginated)
        """
        return self.db_session.query(self.group_model).offset((page - 1) * page_size).limit(page_size).all()

    def get_group(self, uuid, page=1, page_size=100):
        """
        Helper method to return a group object and relative mappings (paginated)
        """
        group = self.db_session.query(self.group_model).get(uuid)
        # TODO @shipperizer add pagination on relationship
        return group

    def get_pks(self, page=1, page_size=100):
        """
        Helper method to return paginated pk values of the model

        # TODO @shipperizer add model as a parameter so can be useable for multiple mappings

        Return:
            List of pks (list): eg ["dd4e5cb3-4809-4098-8204-5c5fc3f55683", "e833d552-2c43-4f29-be41-25d4c4daec87",
                                    "20409d97-c63b-4e60-9468-714b7753194b"]
        """
        records = self.db_session.query(
            getattr(self.model, self.model_pk_name)
        ).offset((page - 1) * page_size).limit(page_size).all()

        # records is a list of lists, each containing just the pk of the record
        return [record[0] for record in records]

    def associate(self, data, *args, **kwargs):
        """
        Association method to map groups to target models/instances
        self.func_match must be defined by the user for this to work
        """
        if self.func_match is None:
            raise NotImplementedError('Need to define func_match in the constructor')
        elif not callable(self.func_match):
            raise TypeError('func_match not a function')
        else:
            self.func_match(data, db_session=self.db_session, model=self.model, group_model=self.group_model)
