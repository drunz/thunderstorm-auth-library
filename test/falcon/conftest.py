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
def middleware(jwk_set):
    return TsAuthMiddleware(
        jwk_set,
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
