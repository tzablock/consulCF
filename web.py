import os
from flask import Flask, jsonify, make_response, request, Response, abort
from functools import wraps


app = Flask(__name__)

log = app.logger

X_BROKER_API_MAJOR_VERSION = 2
X_BROKER_API_MINOR_VERSION = 10
X_BROKER_API_VERSION_NAME = 'X-Broker-Api-Version'

# Service plans
plan_one = {
    "id": "standard_plan",
    "name": "standard_plan",
    "description": "Standard plan which provide Consul link.",
    "free": True
}

# Services
my_service = {
    'id': 'consul-service',
    'name': 'c-service',
    'description': 'Provide access to Consul cluster.',
    'bindable': True,
    'plans': [plan_one]
}

my_services = {"services": [my_service]}

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    if not (username == os.environ['BROKER_USERNAME'] and password == os.environ['BROKER_PASSWORD']):
        log.warning('Authentication failed')
    return username == os.environ['BROKER_USERNAME'] and password == os.environ['BROKER_PASSWORD']


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    """Cloud Controller (final release v145+) authenticates with the Broker
    using HTTP basic authentication (the Authorization: header) on every
    request and will reject any broker registrations that do not contain a
    username and password. The broker is responsible for checking the username
    and password and returning a 401 Unauthorized message if credentials are
    invalid.
    Cloud Controller supports connecting to a broker using SSL if additional
    security is desired."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def api_version_is_valid(api_version):
    version_data = api_version.split('.')
    result = True
    if (float(version_data[0]) < X_BROKER_API_MAJOR_VERSION or
       (float(version_data[0]) == X_BROKER_API_MAJOR_VERSION and
       float(version_data[1]) < X_BROKER_API_MINOR_VERSION)):
                result = False
    return result


def requires_api_version(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_version = request.headers.get('X-Broker-Api-Version')
        if (not api_version or not (api_version_is_valid(api_version))):
            abort(412)
        return f(*args, **kwargs)
    return decorated


@app.errorhandler(412)
def version_mismatch(error):
    return 'Version mismatch. Expected: {}: {}.{}'.format(
        X_BROKER_API_VERSION_NAME,
        X_BROKER_API_MAJOR_VERSION,
        X_BROKER_API_MINOR_VERSION), 412

@app.route('/v2/catalog')
@requires_auth
@requires_api_version
def catalog():
    return jsonify(my_services)


@app.route('/v2/service_instances/<instance_id>', methods=['PUT'])
def create_service_instances(instance_id):
    if request.method == 'PUT':
        return make_response(jsonify({"consul_server_address": "10.26.224.171:8301"}), 201)
    else:
        return jsonify({})


@app.route('/v2/service_instances/<instance_id>', methods=['DELETE'])
def delete_service_instances(instance_id):
    if request.method == 'PUT':
        return make_response(jsonify({"consul_server_address": "10.26.224.171:8301"}), 201)
    else:
        return jsonify({})


@app.route('/v2/service_instances/<instance_id>/service_bindings/<binding_id>', methods=['DELETE'])
def binding_delete(instance_id, binding_id):
    return make_response(jsonify({}), 200)


@app.route('/v2/service_instances/<instance_id>/service_bindings/<binding_id>', methods=['PUT'])
def binding_instances(instance_id, binding_id):
    return make_response(jsonify({"credentials": {"consul_server_address" : "10.26.224.171:8301"}}), 200)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('VCAP_APP_PORT', '5000')))
