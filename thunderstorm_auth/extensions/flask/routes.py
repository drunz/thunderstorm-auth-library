from flask import Blueprint, jsonify, current_app, url_for, request
from marshmallow import fields, Schema
from werkzeug.local import LocalProxy


# pagination defaults
PAGE_SIZE = 100
PAGE = 1

# references to the ts_auth extension, ::LocalProxy:: means they will be instantiated at runtime on first call
_TsAuth = LocalProxy(lambda: current_app.extensions['ts_auth'])
_datastore = LocalProxy(lambda: _TsAuth.datastore)


auth_api_bp = Blueprint('ts_auth', __name__, url_prefix='/api/auth/v0')


class TsAuthGroupSchema(Schema):
    """
    Schema for TsAuthGroup model

    resource will be a link to the detailed view of the specific group
    """
    uuid = fields.UUID(required=True)
    name = fields.String(required=True)
    resource = fields.Method("resource_url")

    def resource_url(self, obj):
        return url_for('ts_auth.group_detail', uuid=obj.uuid)


# class TsAuthGroupMatchSchema(Schema):
#     """
#     Schema for TsAuthGroup model on the associate/match endpoint
#
#     resource will be a link to the detailed view of the specific group
#     """
#     uuid = fields.UUID(required=True)
#     name = fields.String(required=True)
#     resource = fields.Method("resource_url")
#
#     def resource_url(self, obj):
#         return url_for('ts_auth.group_detail', uuid=obj.uuid)


# starting with a single model to be exposable per service
@auth_api_bp.route('/model', methods=['GET'])
def expose_pks():
    """
    Endpoint to expose the model and respective pks
    """
    # TODO @shipperizer add pagination
    # TODO @shipperizer make it able to handle multiple models (different endpoints /models/<modelA>)
    # http://exploreflask.com/en/latest/views.html#custom-converters
    pk_name = _datastore.model_pk_name
    return jsonify(
        {
            'data': {
                _datastore.model.__name__.lower(): {
                    pk_name: [_datastore.get_pks()],
                },
            },
            'page': PAGE,
            'page_size': PAGE_SIZE
        }
    )


@auth_api_bp.route('/group', methods=['GET'])
def groups():
    """
    Endpoint used by the Auth service to check the groups present/mapped
    """
    # TODO @shipperizer add pagination
    groups = _datastore.get_groups()
    return jsonify(data=TsAuthGroupSchema(many=True).dump(groups).data)


@auth_api_bp.route('/group/<uuid:uuid>', methods=['GET'])
def group_detail(uuid):
    """
    Endpoint used by the Auth service to check the groups present/mapped
    """
    group = _datastore.get_group(uuid)

    if not group:
        return jsonify(), 404
    return jsonify(TsAuthGroupSchema(only=('uuid', 'name')).dump(group).data)


@auth_api_bp.route('/group', methods=['PUT'])
def associate_group():
    """
    Endpoint used by the Auth service to push associations between group and models pks

    Using PUT as we need an UPSERT, create if not present otherwise update group

    Payload:
        data (dict): payload expected in a form of
            {
             <group_a>: {'complex_uuids': [<model_1>, <model_7>], 'name': <name_a>}
             <group_b>: {'complex_uuids': [<model_1>, <model_3>, ..], 'name': <name_b>}
            }
    """
    # TODO @shipperizer fidn a way to introduce the Marshmallow schema
    data = request.get_json(force=True, silent=True)
    _datastore.associate(data)
    return jsonify(), 204
