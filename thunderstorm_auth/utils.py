import json


def load_jwks_from_file(path):
    with open(path, 'r') as f:
        try:
            jwks = json.load(f)
            assert len(jwks['keys']) > 0
            return jwks
        except (ValueError, KeyError, AssertionError):
            raise ValueError('Invalid JWK Set at {}'.format(path))
