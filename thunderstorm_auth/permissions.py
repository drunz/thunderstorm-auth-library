from collections.abc import Mapping
from uuid import uuid4

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID

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


def create_permission_model(base):
    """Create an SQLAlchemy Permission

    This is intended to be used in apps that have permissions.

    Args:
        base (Base): Declarative base of database schema to add model to.

    Returns:
        SQLAlchemy Permission model
    """

    return type(
        'Permission',
        (base,),
        {
            key: value for key, value in Permission.__dict__.items()
            if not key.startswith('__') or key == '__tablename__'
        }
    )


class Permission:
    __tablename__ = 'permission'

    uuid = Column(
        UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid4())
    )
    service_name = Column(String(255), nullable=False)
    permission = Column(String(255), nullable=False, unique=True)
    is_deleted = Column(Boolean(), nullable=False, default=False)
    is_sent = Column(Boolean(), nullable=False, default=False)
