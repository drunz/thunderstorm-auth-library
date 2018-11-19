import collections
import warnings

BaseUser = collections.namedtuple('User', 'username roles permissions groups')


class User(BaseUser):
    @classmethod
    def from_decoded_token(cls, token_data):
        warnings.warn('Token field `permissions` is being deprecated', DeprecationWarning)
        return cls(
            username=token_data['username'],
            roles=token_data.get('roles', []),
            permissions=token_data.get('permissions', {}),
            groups=token_data.get('groups', []),
        )
