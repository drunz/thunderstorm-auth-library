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

Not yet implemented for Falcon

#### Defining permissions

Not yet implemented for Falcon

#### Deploying permissions

Not yet implemented for Falcon
