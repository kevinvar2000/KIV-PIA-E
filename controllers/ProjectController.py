import os
from flask import Blueprint, request, jsonify, send_file, session
from models.Project import ProjectState
from services.ProjectService import ProjectService

proj_bp = Blueprint('proj_bp', __name__)


@proj_bp.route('/projects', methods=['POST'])
def create_project():
    """API endpoint to create a new project."""

    customer_id = request.form.get('customer_id') if 'customer_id' in request.form else session.get('user', {}).get('user_id')
    project_name = request.form.get('project_name')
    description = request.form.get('description')
    target_language = request.form.get('target_language')
    source_file = request.files.get('source_file')

    try:
        project = ProjectService.create_project(customer_id, project_name, description, target_language, source_file)

        if not project:
            return jsonify({'error': 'Project creation failed.'}), 500
        
        if project.state == ProjectState.CLOSED:
            return jsonify({'error': 'No translators available. Project closed.'}), 400

        return jsonify({'message': 'Project created successfully.'}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/projects', methods=['GET'])
def get_all_projects():
    """API endpoint to get all projects."""
    try:
        projects = ProjectService.get_all_projects()
        return jsonify({'projects': projects}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400



@proj_bp.route('/projects/<customer_id>', methods=['GET'])
def get_projects(customer_id):
    """API endpoint to get all projects for a customer."""
    try:
        projects = ProjectService.get_projects_by_customer_id(customer_id)
        projects_data = [{'id': p.id, 'name': p.name, 'description': p.description, 'status': p.status} for p in projects]
        return jsonify({'projects': projects_data}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id):
    """API endpoint to get a project by its ID."""
    try:
        project = ProjectService.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found.'}), 404
        project_data = {'id': project.id, 'name': project.name, 'description': project.description, 'status': project.status}
        return jsonify({'project': project_data}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/status', methods=['PUT'])
def update_project_status(project_id):
    """API endpoint to update the status of a project."""
    data = request.json
    status = data.get('status')

    try:
        ProjectService.update_project_status(project_id, status)
        return jsonify({'message': 'Project status updated successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    
@proj_bp.route('/project/<project_id>/assign', methods=['PUT'])
def assign_translator(project_id):
    """API endpoint to assign a translator to a project."""
    data = request.json
    translator_id = data.get('translator_id')

    try:
        ProjectService.assign_translator_to_project(project_id, translator_id)
        return jsonify({'message': 'Translator assigned successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    

@proj_bp.route('/project/<project_id>/accept', methods=['POST'])
def accept_translation(project_id):
    """API endpoint for customer to accept a translation."""
    try:
        ProjectService.accept_translation(project_id)
        return jsonify({'message': 'Translation accepted successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/reject', methods=['POST'])
def reject_translation(project_id):
    """API endpoint for customer to reject a translation."""
    feedback = request.form.get('feedback')

    try:
        ProjectService.reject_translation(project_id, feedback)
        return jsonify({'message': 'Translation rejected successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/download/original', methods=['GET'])
def download_original_file(project_id):
    """API endpoint to download the original file of a project."""

    try:
        file = ProjectService.get_original_file(project_id)
        return send_file(file,
                        as_attachment=True,
                        download_name=os.path.basename(file))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/download/translation', methods=['GET'])
def download_translated_file(project_id):
    """API endpoint to download the translated file of a project."""

    try:
        file = ProjectService.get_translated_file(project_id)
        return send_file(file,
                         as_attachment=True,
                         download_name=os.path.basename(file))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/upload', methods=['POST'])
def upload_translated_file(project_id):
    """API endpoint for translator to upload the translated file."""
    translated_file = request.files.get('translated_file')

    try:
        ProjectService.save_translated_file(project_id, translated_file)
        return jsonify({'message': 'Translated file uploaded successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400