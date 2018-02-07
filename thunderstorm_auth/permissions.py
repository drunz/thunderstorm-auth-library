from collections.abc import Mapping

from thunderstorm_auth.exceptions import (
    InsufficientPermissions, BrokenTokenError
)


def validate_permission(token_data, service_name, permission):
    """Validate a permission is present in a token string

    Args:
        token_data (dict): The data from the auth token
        service_name (str): The name of the service
        permission (str): The permission string required

    Raises:
        BrokenTokenError: If the token data is not valid
        InsufficientPermissions: If the token does not contain the required
                                 permission
    """
    if not isinstance(token_data, Mapping):
        raise BrokenTokenError()
    elif not isinstance(token_data.get('permissions'), Mapping):
        raise BrokenTokenError()
    elif permission not in token_data['permissions'].get(service_name, []):
        raise InsufficientPermissions()
