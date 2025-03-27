from flask import Blueprint, render_template, send_file, request, jsonify
from app.utils import json, xml
from app.config.settings import PARAMETERS_JSON, CURRENT_XML, STREAM_IMAGE_PATH

web_routes = Blueprint('web_routes', __name__)

# Store a reference to camera_controller that will be set later
camera_controller = None

def set_camera_controller(controller):
    global camera_controller
    camera_controller = controller

@web_routes.route("/")
def index():
    return render_template('index.html')

@web_routes.route("/cockpit")
def cockpit():
    return render_template('cockpit.html')


@web_routes.route('/stream')
def stream():
    return render_template('stream.html')

@web_routes.route('/last_frame')
def last_frame():
    return send_file(STREAM_IMAGE_PATH, mimetype='image/jpeg')

@web_routes.route('/parameters')
def parameters():
    parameters = json.get_parameters(PARAMETERS_JSON)  
    values = xml.get_values_from_xml(CURRENT_XML, parameters)
    
    print(f" Parameters: {parameters}")
    print(f" Values : {values}")

    return render_template('parameters.html', parameters=parameters, values=values)


@web_routes.route('/files')
def files():
    return render_template('filebrowser.html')

@web_routes.route('/set_transect_name', methods=['POST'])
def set_transect_name():
    if camera_controller is None:
        return jsonify(status="error", message="Camera controller not initialized")
        
    data = request.get_json()
    if data and 'transect_name' in data:
        camera_controller.transect_name = data['transect_name'].strip() or 'transect'
    return jsonify(status="success")

@web_routes.route('/get_transect_name')
def get_transect_name():
    if camera_controller is None:
        return jsonify(status="error", message="Camera controller not initialized")
        
    return jsonify(transect_name=camera_controller.transect_name)