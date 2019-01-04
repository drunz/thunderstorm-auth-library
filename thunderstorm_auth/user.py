import collections

BaseUser = collections.namedtuple('User', 'username roles groups organization')


class User(BaseUser):
    @classmethod
    def from_decoded_token(cls, token_data):
        organization = token_data.get('organization', {})
        return cls(
            username=token_data['username'],
            roles=token_data.get('roles', []),
            groups=token_data.get('groups', []),
            organization=organization.get('uuid') if organization else None
        )
