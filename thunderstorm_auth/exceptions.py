from thunderstorm_auth import TOKEN_HEADER


class ThunderstormAuthError(Exception):
    pass


class AuthSecretKeyNotSet(ThunderstormAuthError):
    pass


class TokenError(ThunderstormAuthError):
    pass


class TokenHeaderMissing(TokenError):

    def __init__(self):
        super().__init__('Missing auth header: {}'.format(TOKEN_HEADER))


class BrokenTokenError(TokenError):
    pass


class ExpiredTokenError(TokenError):
    pass