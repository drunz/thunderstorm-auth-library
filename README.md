# Thunderstorm Auth Library

[![Build Status](https://ts-jenkins.aamts.io/buildStatus/icon?job=AAM/thunderstorm-auth-library/master)](https://ts-jenkins.aamts.io/job/AAM/thunderstorm-auth-library/master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/d55a251ae0fa4511af518cd994e034c7)](https://www.codacy.com/app/AAM/thunderstorm-auth-library?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=artsalliancemedia/thunderstorm-auth-library&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/d55a251ae0fa4511af518cd994e034c7)](https://www.codacy.com/app/AAM/thunderstorm-auth-library?utm_source=github.com&utm_medium=referral&utm_content=artsalliancemedia/thunderstorm-auth-library&utm_campaign=Badge_Coverage)

**Note: This is a public repo**

Thunderstorm auth library is a package mainly for integrating authentication
provided by the [&#169;Thunderstorm User service](https://github.com/artsalliancemedia/user-service).
It also provides access to other common tools such as logging until we find a
better place for them.

This document provides instructions and examples for
[Flask](https://flask.readthedocs.io/en/stable/) apps. For
[Falcon](https://falconframework.org/) apps see the [Falcon doc](./docs/falcon.md)


## Contents

- [Installation](#installation)
- [Authentication](#authentication)
  - [Basic usage](#basic-usage)
  - [Roles and Permissions](#permissions)
- [Logging](#logging)
- [Development](#development)
- [Testing](#testing)
- [Releasing](#releasing)


## Installation
\[[Falcon](./docs/falcon.md#installation)\]

Install this library from a tarball on Github.
Optionally add the web framework of choice as an extra to install extra
components for those frameworks.

e.g. for Flask:
```shell
> pip install https://github.com/artsalliancemedia/thunderstorm-auth-library/releases/download/vX.Y.Z/thunderstorm-auth-lib-X.Y.Z.tar.gz
> pip install thunderstorm-auth-lib[flask]
```

# ############################### ## Special installation notes ## ############################### #

* Upgrading from `<v0.5` to `v0.6`: **It is strongly advised to do a 2-step upgrade, first to `v0.5` and after at least 1 hour upgrade to `v0.6`**
The reason for this is due to the scheduling of roles broadcasting which happens once every *60minutes*, so if you upgrade straight to `v0.6` there is a chance that your application will not function correctly for up to *one hour* (no roles would have been received and each api call would result in a `401 UNAUTHORIZED`). `v.0.5` is backwards compatible (by which we mean it can still use permissions in the token) which is why we recommend upgrading to that first for one hour so that when you move to `v.0.6` the roles will have been cached locally at that point.
  no roles would have been received and each api call would result in a `401 UNAUTHORIZED`, therefore *1h of missing data and not functioning services*


# ################################################################################################ #

## Authentication

Authentication is provided by the [user service](https://github.com/artsalliancemedia/user-service)
with [JWTs](https://jwt.io/).

You will need to include the `TS_AUTH_JWKS` config variable in your Flask
config. The JWKs stored in this variable will be used for decoding JWTs.
See [Thunderstorm User Service](https://github.com/artsalliancemedia/user-service#using-your-jwt).

### Basic usage
\[[Falcon](./docs/falcon.md#basic-usage)\]

The following decorator will make your views require the JWT issued by the `user-service`.

```python
from thunderstorm_auth.flask import ts_auth_required

@route('/hello', methods=['GET'])
@ts_auth_required(with_permission='read')
def hello():
    return jsonify({'message': 'hello world'})
```

The authenticated user object can be accessed through the `flask.g`.

```python
from flask import g

@route('/hello', methods=['GET'])
@ts_auth_required(with_permission='read')
def hello():
    return jsonify({'message': f'hello {g.user}'})
```

The user object has four properties, `username`, `roles`, `permissions` (to be deprecated) and `groups`.

When making a request to this endpoint, you must supply your JWT in a HTTP
header called `X-Thunderstorm-Key`.

For example:

```shell
> http localhost:8888/hello X-Thunderstorm-Key:eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6Im1hZnJvMiIsInBlcm1pc3Npb25zIjoiKiIsImV4cCI6MTUwMTg0NTk0OH0.uhRFnfqIaZ91A5xgbqKqQPjdBuOYsuMzIEHA7-j0mzM
HTTP/1.0 200 OK
Content-Length: 31
Content-Type: application/json
Date: Fri, 04 Aug 2017 09:55:19 GMT
Server: Werkzeug/0.12.2 Python/3.5.3

{
    "message": "hello world"
}
```

When authentication fails:

```shell
> http localhost:8888/hello X-Thunderstorm-Key:egg
HTTP/1.0 401 UNAUTHORIZED
Content-Length: 48
Content-Type: application/json
Date: Fri, 04 Aug 2017 11:37:40 GMT
Server: Werkzeug/0.12.2 Python/3.5.3

{
    "message": "Token authentication failed."
}
```

If this header is missing, the request will receive a 401:

```shell
> http localhost:8888/hello
HTTP/1.0 401 UNAUTHORIZED
Content-Length: 53
Content-Type: application/json
Date: Fri, 04 Aug 2017 09:55:24 GMT
Server: Werkzeug/0.12.2 Python/3.5.3

{
    "message": "Missing X-Thunderstorm-Key header"
}
```

### Roles and Permissions

Each service owns it's permissions so the first thing that must be done to
start integrating permissions is to add a `Permission` model to their database.
Also each service is proxying `Roles` and `RolePermissionAssociation` in its database
to allow future functionalities around roles and aso the removal of `permissions` form the token.

At the moment we only support SQLAlchemy models.

```python
from sqlalchemy.ext.declarative import declarative_base
from thunderstorm_auth.permissions import PermissionMixin
from thunderstorm_auth.roles import RoleMixin, RolePermissionAssociationMixin


Base = declarative_base()

class Role(Base, RoleMixin):
    pass


class RolePermissionAssociation(Base, RolePermissionAssociationMixin):
    pass


class Permission(Base, PermissionMixin):
    pass
```

Once you have a role, permission and the association models you can integrate it with your flask app.
to give you access to the permission management CLI commands.

```python
from thunderstorm_auth.datastore import SQLAlchemySessionAuthStore
from thunderstorm_auth.flask import init_ts_auth

from .database import db
from .models import Role, Permission, RolePermissionAssociation


def init_app(app):
    """Flask app initialisation and bootstrap"""
    app.ts_auth = init_ts_auth(
        app,
        SQLAlchemySessionAuthStore(
          db.session, Role, Permission, RolePermissionAssociation
        )
    )
```

The [SQLAlchemySessionAuthStore](https://github.com/artsalliancemedia/thunderstorm-auth-library/blob/master/thunderstorm_auth/datastore.py#L121) is an object that is used to control access to the storage layer, it inherits from a set of base classes which case be used to create custom datastore objects to support your ORM of choice.


Now that this is integrated you will be able to manage your permissions from
the flask CLI (we haven't created any permissions yet so there won't be any).

```shell
> docker-compose exec myapp flask permissions --help
```

Finally we need to integrate the sync task with our celery app so that our
permissions can be synced up to the user service.

```python
from thunderstorm_auth.setup import init_permissions, init_ts_auth_tasks

from .database import db
from .models import Permission, ComplexGroupComplexAssociation

def init_celery(celery_app):
    """Celery app initialisation"""
    datastore = SQLAlchemySessionAuthStore(db.session, Role, Permission, RolePermissionAssociation)
    init_permissions(celery_app, db.session, Permission)
    # this will kickstart roles and complex groups sync
    init_ts_auth_tasks(celery_app, db.session, [ComplexGroupComplexAssociation], datastore, False)
```


## **New change since `v0.5`**

To initialize the tasks for groups and roles, **init_ts_auth_tasks** is now being used in place of **init_group_sync_tasks**,

The former will perform the initialization of both, the **latter is back to just group initialization**


#### Defining permissions

\[[Falcon](./docs/falcon.md#defining-permissions)\]

Now that we have the permissions model, CLI and syncing fully integrated we
can start using permissions.

To require a specific permission for a flask route add the `with_permission`
keyword argument to the `ts_auth_required` route decorator.

```python
from thunderstorm_auth.flask import ts_auth_required


@myapp.route('/foo/bar', methods=['GET'])
@ts_auth_required(with_permission='special')
def get_foo_bar():
    ...
```

Now a request to the `/foo/bar` route will only be allowed if it has a valid
authentication token and that token contains the `special` permission for your
service. In order for that to be possible the user service needs to be made
aware of this new permission.

If you're using flask you can use the flask CLI to manage your service's
permissions. First let's see our permissions.

```shell
> docker-compose exec myapp flask permissions list
Permissions in use
------------------
special

Permissions in DB
-----------------
uuid                                   permission      sent   deleted

AN UPDATE IS NEEDED RUN:
flask permissions update
```

This is telling us that we have one permission in use (`special`) but no
permissions in our database. We need to create a migration to ensure the
appropriate permission record is created in the database. If we're using
alembic we can generate a migration with the CLI

```shell
> docker-compose exec myapp flask permissions update
Generating /var/app/migrations/versions/cab5c9a70124_updating_auth_permissions.py ... done
```

If we run `alembic upgrade` and then `permissions list` again we can see our
permission has been created but not yet sent to the user service. Next time
we start our celery app it will automatically run a task that will send
any unsent permissions up to the user service.

```shell
> docker-compose exec myapp flask permissions upgrade
Permissions in use
------------------
special

Permissions in DB
-----------------
uuid                                   permission      sent   deleted
5c0b17c4-1595-11e8-8c3f-4a0004692f50   special              0      0
```

#### Deploying permissions

When restricting access to a resource we usually want to add the permission to
the users that need access to the resource before adding the restriction so as
to avoid any downtime where authorised users cannot access the resource. In
order to achieve this we must ensure that the migration is deployed to an
environment before the decorator change.

## Logging

Logging shouldn't really live in this library but until we have a better
place for it, here is where it lives.

The logging facility emits JSON formatted logs with some standardised fields
pulled out to make searching across services easier. This format should be
used for anything that is on the request path and emits logs that we can control.

| Field      | Description | Example |
| ---------- | ----------- | ------- |
| `service`  | The service name, this should uniquely identify the service across thunderstorm. Set it with the `TS_SERVICE_NAME` environment variable. | `agent-service` |
| `log_type` | The facility the logs came from, usually either `flask`, `nginx` or `celery` | `flask` |
| `request_id` | A unique identifier for a request across services and facilities. See [Request IDs](#request-ids) | `1f4ea2be-18b6-11e8-a5c1-4a0004692f50` |
| `timestamp` | A UTC ISO8601 timestamp. | `2018-02-23T16:26:40+00:00` |
| `message` | Standard log message field | anything |
| `method` | HTTP request method string | `GET` |
| `url` | HTTP request URL | `http://172.31.105.16/version` |
| `status` | HTTP status code | `200` |
| `task_name` | Celery task name | `check_flm_status` |
| `task_id` | Celery task id | `e7469c1e-019d-405a-b086-8a6725925292` |

### Request IDs

Request IDs are identifiers that can be used to see all log messages associated
with a given request across all services that properly handle them. A request
ID is generated when a log message is created if there is no existing request
ID. An existing request ID can come from the `TS-Request-ID` HTTP header or
the `x_request_id` Celery header. If the [Celery task class](./thunderstorm_auth/logging/celery.py#L74)
and [requests wrappers](./thunderstorm_auth/logging/requests.py) are used
these request IDs will be propagated automatically.

### Flask

```python
from thunderstorm_auth.logging.flask import init_app as init_logging

def init_flask(flask_app):
    init_logging(flask_app)
```

### Celery

```python
import celery.signals

from thunderstorm_auth.logging.celery import (
    CeleryRequestIDTask,
    on_celery_setup_logging,
)

celery.signals.setup_logging.connect(
  on_celery_setup_logging('agent-service'),
  weak=False
)

def init_celery(celery_app):
    celery_app.Task = CeleryRequestIDTask

    # If you need to extend task yourself ensure you do it on top
    # of CeleryRequestIDTask
    class MyTask(CeleryRequestIDTask):
        pass
    celery_app.Task = CeleryRequestIDTask
```

### Nginx

```nginx
http {
  ...
  log_format json_combined escape=json '{ "log_type": "nginx", '
    '"service": "agent-service", '
    '"timestamp": "$time_iso8601", '
    '"msec": "$msec", '
    '"request_time": "$request_time", '
    '"request_length": "$request_length", '
    '"request_id": "$upstream_http_ts_request_id", '
    '"request": "$request", '
    '"message": "$request $status $request_time", '
    '"status": "$status", '
    '"amzn_trace_id": "$http_x_amzn_trace_id", '
    '"user_agent": "$http_user_agent" }';
	...
}
```

### Gunicorn

Basically disable logging ready for the handler to be overriden by the flask
logging setup. Once `19.8.0` comes out we'll be able to revisit this.

```ini
[loggers]
keys=root, gunicorn

[handlers]
keys=null

[formatters]
keys=

[logger_root]
level=INFO
handlers=null

[logger_gunicorn]
level=INFO
handlers=null
propagate=0
qualname=gunicorn

# disable Gunicorn logs until 19.8.0
# see: https://github.com/benoitc/gunicorn/issues/1634
# and: https://github.com/benoitc/gunicorn/commit/610596c9d93b3c9086becd6212ab4ba81d476dc4
[handler_null]
class=NullHandler
args=(1,)
```

### Requests

Simply import `thunderstorm_auth.logging.requests` instead of `requests`.

## Exceptions

The exception `AuthJwksNotSet` will be raised when `TS_AUTH_JWKS` is missing
from the Flask config.

Both Flask and Falcon raise the following exceptions:
`ExpiredTokenError` - If the token supplied for decoding has expired.
`BrokenTokenError` - If the token supplied was malformed or the token does not match the JWK indicated in its 'Headers' section.

## Development

First you will need to pick a service to develop against.

If, for example, you are working on the `complex-service`, first clone this
repo as a subdirectory of that project.

Next, modify the installation of the auth library. The [complex-service](https://github.com/artsalliancemedia/complex-service/blob/master/env_conf/Dockerfile#L27)
has a line in its `Dockerfile` installing this library from a tarball. Change
this line to the following two lines:

```dockerfile
COPY thunderstorm-auth-library /var/app/thunderstorm-auth-library
RUN pip install -e file:/var/app/thunderstorm-auth-library
```

### Avoiding Exchange Not Found errors in tests

By default an Exchange Not Found error is raised by `init_group_sync_tasks` if
the exchange does not exist. This is useful in deployed environments where
we want to avoid an app silently not binding to the correct exchange. However,
this causes tests to fail because there is no exchange there. To avoid this
set `ensure_exchange_exists` to `False`.

## Testing

At present the library needs to support python versions 3.4, 3.5 and 3.6. The docker-compose file in this repo has individual services for each python version.
e.g. to run unit tests for python 3.4:

```bash
> docker-compose run --rm python34 make test
```

## Releasing

New releases can be easily created using [github-release](https://github.com/aktau/github-release).
Increment the version number in [`thunderstorm_auth/__init__.py`](./thunderstorm_auth/__init__.py),
ensure you have a valid github token and run the following command (replacing
your github token with `{github token}`).

```shell
> GITHUB_TOKEN={github token} release
```
