import collections

BaseUser = collections.namedtuple('User', 'username roles permissions groups')


class User(BaseUser):
    @classmethod
    def from_decoded_token(cls, token_data):
        return cls(
            username=token_data['username'],
            roles=token_data.get('roles', []),
            permissions=token_data.get('permissions', {}),
            groups=token_data.get('groups', []),
        )
