from marshmallow import fields, Schema


class AuditSchema(Schema):
    username = fields.String(required=True)
    organization_uuid = fields.UUID(required=True, allow_none=True)
    action = fields.String(required=True)
    endpoint = fields.String(required=True)
    status = fields.String(required=True)
    method = fields.String(required=True)


class AuditConf(object):
    """
    Auditing configuration object
    """

    def __init__(self, enabled=False, exclude_paths=None):
        """
        Args:
            enabled (bool or None): Defines whether or not auditing is enabled for API calls.
            exclude_paths (list): list of paths to exclude from auditing.
        """
        self.enabled = enabled or False
        self.exclude_paths = exclude_paths or []
