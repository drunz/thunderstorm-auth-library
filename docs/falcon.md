# Falcon docs

This document is an extension of the [main README](../README.md) with examples
and instructions tailored for the [Falcon](https://falconframework.org/)
framework. The main README is where most of the context is so start there
and come here for the Falcon examples.

## Installation

```shell
> pip install https://github.com/artsalliancemedia/thunderstorm-auth-library/releases/download/vX.Y.Z/thunderstorm-auth-lib-X.Y.Z.tar.gz
> pip install thunderstorm-auth-lib[falcon]
```

## Authentication

### Basic usage

The following middleware will make your resources require the JWT issued by
the `thunderstorm-user-service` so long as your resource class has a
`requires_auth` property set to `True`.

For the app config:
```python
import os
from thunderstorm_auth.falcon import TsAuthMiddleware

auth_middleware = TsAuthMiddleware(os.environ['TS_AUTH_JWKS'])
falcon_app = falcon.API(middleware=auth_middleware)
falcon_app.add_route('/', MyResource())
```

For the resource config:
```python
class MyResource:
  requires_auth = True

  def on_get(self, req, resp):
    resp.body = 'ok'
```

The authenticated user object can be accessed through the `req.context`.

```python
class MyResource:
  requires_auth = True

  def on_get(self, req, resp):
    resp.body = f'Hi, {req.context["user"]}'
```

### Permissions

See \[[Flask docs](/README.md#permissions)\] for managing the Permission model.

#### Defining permissions

Now that we have the permissions model, CLI and syncing fully integrated we
can start using permissions.

To require a specific permission for a given middleware instance add
the `with_permission` and `service_name` keyword arguments to the
`TsAuthMiddleware` constructor.

```python
auth_middleware = TsAuthMiddleware(
  os.environ['TS_AUTH_JWKS'],
  with_permission='my-permission',
  service_name=os.environ['TS_SERVICE_NAME'],
)
...
```

Now a request through this middleware will only be allowed if it has a valid
authentication token and that token contains the `my-permission` permission
for the given service. In order for that to be possible the user service needs
to be made aware of this new permission. See the 
[Flask docs](/README.md#defining-permissions) managing the Permission model.

#### Deploying permissions

See \[[Flask docs](/README.md#deploying-permissions)\] for managing the Permission model.
Not yet implemented for Falcon
