from flask import Blueprint, jsonify, current_app
from werkzeug.local import LocalProxy


# pagination defaults
PAGE_SIZE = 100
PAGE = 1

# references to the ts_auth extension, ::LocalProxy:: means they will be instantiated at runtime on first call
_TsAuth = LocalProxy(lambda: current_app.extensions['ts_auth'])
_datastore = LocalProxy(lambda: _TsAuth.datastore)


auth_api_bp = Blueprint('ts_auth', __name__, url_prefix='/api/auth/v0')


# starting with a single model to be exposable per service
@auth_api_bp.route('/model', methods=['GET'])
def expose_pks():
    """
    Endpoint to expose the model and respective pks

    # TODO @shipperizer add pagination
    # TODO @shipperizer make it able to handle multiple models (different endpoints /models/<modelA>)
    """
    pk_name = _datastore.model_pk_name
    return jsonify(
        {
            _datastore.model.__class__.__name__: {
                pk_name: [_datastore.get_pks()],
            },
            'page': PAGE,
            'page_size': PAGE_SIZE
        }
    )


@auth_api_bp.route('/groups', methods=['PUT'])
def associate_group():
    """
    Endpoint used by the Auth service to push associations between group and models pks

    Using PUT as we need an UPSERT, create if not present otherwise update group
    """

    return jsonify(), 204
