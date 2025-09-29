from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from app import app
import os


UPLOAD_FOLDER = 'files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route: List assigned projects (not closed) with customer feedback
@app.route('/projects', methods=['GET'])
def list_projects():
    translator = request.args.get('translator')
    assigned_projects = [] # TODO: Get from DB based on translator and not closed status
    return jsonify(assigned_projects)

# Route: Download original project file
@app.route('/projects/<int:project_id>/download', methods=['GET'])
def download_original_file(project_id):
    project = []
    if not project or not project["original_file"]:
        return jsonify({"error": "Project or file not found"}), 404
    return send_file(project["original_file"], as_attachment=True)

# Route: Submit translated file
@app.route('/projects/<int:project_id>/submit', methods=['POST'])
def submit_translated_file(project_id):
    project = []
    if not project or project["status"] == "closed":
        return jsonify({"error": "Project not found or already closed"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(f"translated_{project_id}_" + file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    project["translated_file"] = filepath
    # Optionally, update project status here

    return jsonify({"message": "File uploaded successfully", "file": filename})