from thunderstorm_auth.user import User


def test_create_user_from_decoded_token():
    decoded_token_data = {
        'username': 'test-user',
        'permissions': {
            'foo': 'r',
            'bar': 'w'
        },
        'groups': [
            'a',
            'b'
        ]
    }

    user = User.from_decoded_token(decoded_token_data)

    assert user == User(
        username='test-user',
        permissions={
            'foo': 'r',
            'bar': 'w'
        },
        groups=[
            'a',
            'b'
        ]
    )
