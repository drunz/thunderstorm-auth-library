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


class HTTPError(ThunderstormAuthError):
    """To be used when raising exceptions to be caught by the flask app
    """
    def __init__(self, message='Error', code=None):
        super().__init__()
        self.message = message
        self.code = code
