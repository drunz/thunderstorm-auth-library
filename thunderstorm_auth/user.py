import collections

BaseUser = collections.namedtuple('User', 'username permissions groups')


class User(BaseUser):

    @classmethod
    def from_decoded_token(cls, token_data):
        return cls(
            username=token_data['username'],
            permissions=token_data.get('permissions', {}),
            groups=token_data.get('groups', []),
        )
