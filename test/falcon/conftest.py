import falcon
import falcon.testing
import pytest

from thunderstorm_auth.falcon import TsAuthMiddleware


@pytest.fixture
def resource():
    class Resource:

        requires_auth = True

        def on_get(self, req, resp):
            resp.body = 'ok'

    return Resource()


@pytest.fixture
def middleware(jwk_set, datastore):
    return TsAuthMiddleware(
        jwk_set,
        datastore=datastore,
        with_permission='perm-a',
        service_name='test-service',
    )


@pytest.fixture
def falcon_app(resource, middleware):
    app = falcon.API(middleware=middleware)
    app.add_route('/', resource)
    return app


@pytest.fixture
def client(falcon_app):
    return falcon.testing.TestClient(falcon_app)


@pytest.fixture
def audit_client(jwk_set, datastore, resource):
    app = falcon.API(
        middleware=TsAuthMiddleware(
            jwk_set,
            datastore=datastore,
            with_permission='perm-a',
            service_name='test-service',
            auditing=True
        )
    )
    app.add_route('/', resource)

    return falcon.testing.TestClient(app)
