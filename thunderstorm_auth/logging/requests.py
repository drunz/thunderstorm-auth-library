from requests import *  # noqa

from functools import wraps as _wraps

from requests import request as _request
from requests import head as _head
from requests import get as _get
from requests import post as _post
from requests import put as _put
from requests import patch as _patch
from requests import delete as _delete
from requests import options as _options

from thunderstorm_auth.logging import get_request_id as _get_request_id


@_wraps(_request)
def request(method, url, **kwargs):
    return _request(method, url, **_add_request_id(kwargs))


@_wraps(_head)
def head(url, **kwargs):
    return _head(url, **_add_request_id(kwargs))


@_wraps(_get)
def get(url, **kwargs):
    return _get(url, **_add_request_id(kwargs))


@_wraps(_post)
def post(url, **kwargs):
    return _post(url, **_add_request_id(kwargs))


@_wraps(_put)
def put(url, **kwargs):
    return _put(url, **_add_request_id(kwargs))


@_wraps(_patch)
def patch(url, **kwargs):
    return _patch(url, **_add_request_id(kwargs))


@_wraps(_delete)
def delete(url, **kwargs):
    return _delete(url, **_add_request_id(kwargs))


@_wraps(_options)
def options(url, **kwargs):
    return _options(url, **_add_request_id(kwargs))


def _add_request_id(kwargs):
    headers = kwargs.get('headers', {})
    headers.setdefault('TS-Request-ID', _get_request_id())
    kwargs['headers'] = headers

    return kwargs
