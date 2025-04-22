from flask import Blueprint, render_template, Response, jsonify

views_bp = Blueprint('main', __name__)

@views_bp.route('/')
def index():
    return render_template('index.html')

@views_bp.route("/cockpit")
def cockpit():
    return render_template('cockpit.html')

@views_bp.route('/preview')
def preview():
    return render_template('preview.html')

@views_bp.route('/files')
def files():
    return render_template('filebrowser.html')

@views_bp.route('/parameters')
def parameters():
    return render_template('parameters.html')

@views_bp.route('/app_settings')
def app_settings_page():
    return render_template('app_settings.html')

focus_mode_enabled = False

