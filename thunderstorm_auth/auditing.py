from marshmallow import fields, Schema


class AuditSchema(Schema):
    username = fields.String(required=True)
    organization_uuid = fields.UUID(required=True, allow_none=True)
    action = fields.String(required=True)
    endpoint = fields.String(required=True)
    status = fields.String(required=True)
    method = fields.String(required=True)
