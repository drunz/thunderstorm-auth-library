from thunderstorm_auth import TOKEN_HEADER


class ThunderstormAuthError(Exception):
    pass


class AuthJwksNotSet(ThunderstormAuthError):
    pass


class TokenError(ThunderstormAuthError):
    pass


class MissingKeyErrror(TokenError):
    pass


class TokenDecodeError(TokenError):
    pass


class TokenHeaderMissing(TokenError):

    def __init__(self):
        super().__init__('Missing auth header: {}'.format(TOKEN_HEADER))


class BrokenTokenError(TokenError):
    pass


class ExpiredTokenError(TokenError):
    pass


class InsufficientPermissions(ThunderstormAuthError):
    pass


# TODO: Review in future whether or not this should be pulled from the
# thunderstorm library. for now try and keep them in sync
class HTTPError(ThunderstormAuthError):
    """To be used when creating HTTP exceptions to be caught by the flask app
    """
    def __init__(self, message='Error', code=None):
        self.message = message
        self.code = code


class Unauthorized(HTTPError):
    def __init__(self, message='Unauthorized'):
        super().__init__(message=message, code=401)


class Forbidden(HTTPError):
    def __init__(self, message='Forbidden'):
        super().__init__(message=message, code=403)
