from flask import Blueprint, request, jsonify, send_file, session
from models.Project import ProjectState
from services.ProjectService import ProjectService
from services.AuthService import login_required_api, require_role

proj_bp = Blueprint('proj_bp', __name__)


@proj_bp.route('/projects', methods=['POST'])
@login_required_api
@require_role('CUSTOMER')
def create_project():
    """
    The `create_project` function defines an API endpoint to create a new project with specified details
    and handles exceptions during the process.
    :return: The `create_project` function returns a JSON response based on the outcome of creating a
    new project.
    """

    customer_id = request.form.get('customer_id') if 'customer_id' in request.form else session.get('user', {}).get('user_id')
    project_name = request.form.get('project_name')
    description = request.form.get('description')
    target_language = request.form.get('language')
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
@login_required_api
@require_role('ADMINISTRATOR', 'TRANSLATOR')
def get_all_projects():
    """
    This Python function retrieves all projects using an API endpoint and returns them as JSON, handling
    any ValueErrors that may occur.
    :return: The function `get_all_projects()` is returning a JSON response containing either a list of
    projects under the key 'projects' with a status code of 200 if successful, or an error message under
    the key 'error' with a status code of 400 if an exception of type `ValueError` is caught during the
    process.
    """
    try:
        projects = ProjectService.get_all_projects()
        return jsonify({'projects': projects}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400



@proj_bp.route('/projects/<customer_id>', methods=['GET'])
@login_required_api
@require_role('CUSTOMER', 'ADMINISTRATOR')
def get_projects(customer_id):
    """
    Fetch all projects for a given customer.

    This API endpoint retrieves projects associated with the provided customer ID
    using ProjectService and returns a JSON response with project details.

    Parameters:
        customer_id (int | str): Unique identifier of the customer whose projects are requested.

    Returns:
        tuple:
            - flask.Response: JSON response containing either:
                - {"projects": [{"id": int, "name": str, "description": str, "status": str}, ...]}
                - or {"error": str} if the request is invalid.
            - int: HTTP status code (200 on success, 400 on invalid input).

    Error Handling:
        Returns a 400 response with an error message if ProjectService raises a ValueError.
    """
    try:
        projects = ProjectService.get_projects_by_customer_id(customer_id)
        projects_data = [{'id': p.id, 'name': p.name, 'description': p.description, 'status': p.status} for p in projects]
        return jsonify({'projects': projects_data}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>', methods=['GET'])
@login_required_api
@require_role('CUSTOMER', 'TRANSLATOR', 'ADMINISTRATOR')
def get_project(project_id):
    """
    API endpoint to retrieve a project by its unique ID.

    Parameters:
        project_id (int | str): The identifier of the project to fetch.

    Returns:
        flask.Response: A JSON response containing:
            - 200 OK with {"project": {"id": int, "name": str, "description": str, "status": str}} if found.
            - 404 Not Found with {"error": "Project not found."} if no project exists for the given ID.
            - 400 Bad Request with {"error": "<message>"} if input validation fails or an invalid ID is provided.

    Raises:
        ValueError: If the provided project_id is invalid or cannot be processed.
    """
    try:
        project = ProjectService.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found.'}), 404
        project_data = {'id': project.id, 'name': project.name, 'description': project.description, 'status': project.status}
        return jsonify({'project': project_data}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/status', methods=['PUT'])
@login_required_api
@require_role('CUSTOMER', 'TRANSLATOR', 'ADMINISTRATOR')
def update_project_status(project_id):
    """
    API endpoint to update the status of a project.
    This endpoint expects a JSON payload with a `status` field and attempts to update
    the project's status via the ProjectService. On success, it returns a 200 response
    with a confirmation message; on validation or service errors, it returns a 400 response
    with an error message.
    Parameters:
        project_id (int | str): The unique identifier of the project whose status is being updated.
    Request JSON:
        status (str): The new status to set for the project.
    Returns:
        flask.Response: JSON response containing:
            - On success: {'message': 'Project status updated successfully.'}, HTTP 200.
            - On error: {'error': '<error details>'}, HTTP 400.
    Raises:
        None: Errors are caught and returned as JSON with HTTP 400.
    """
    data = request.json
    status = data.get('status')

    try:
        ProjectService.update_project_status(project_id, status)
        return jsonify({'message': 'Project status updated successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    
@proj_bp.route('/project/<project_id>/assign', methods=['PUT'])
@login_required_api
@require_role('ADMINISTRATOR')
def assign_translator(project_id):
    """API endpoint to assign a translator to a project.
    Consumes a JSON payload containing a 'translator_id' and delegates the assignment
    to ProjectService. Responds with a success message on completion or an error
    message if validation fails.
    Parameters:
        project_id (int | str): Identifier of the project to update. Typically parsed from the URL path.
            Must reference an existing project.
    Request JSON:
        translator_id (int | str): Identifier of the translator to assign.
    Returns:
        flask.Response:
            - 200 OK: {'message': 'Translator assigned successfully.'}
            - 400 Bad Request: {'error': '<validation error message>'}
    Raises:
        ValueError: Propagated from ProjectService.assign_translator_to_project when input
            data is invalid or assignment cannot be performed.
    Side Effects:
        Persists the translator assignment to the project via ProjectService.
    """
    data = request.json
    translator_id = data.get('translator_id')

    try:
        ProjectService.assign_translator_to_project(project_id, translator_id)
        return jsonify({'message': 'Translator assigned successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    

@proj_bp.route('/project/<project_id>/accept', methods=['POST'])
@login_required_api
@require_role('CUSTOMER')
def accept_translation(project_id):
    """Handle the customer’s acceptance of a translation for a given project.

    This endpoint delegates to ProjectService.accept_translation to mark the translation
    as accepted and returns a JSON response indicating success or error.

    Parameters:
        project_id (int): The unique identifier of the project whose translation is being accepted.

    Returns:
        tuple: A Flask response tuple:
            - On success: (jsonify({'message': 'Translation accepted successfully.'}), 200)
            - On error: (jsonify({'error': '<error message>'}), 400)

    Raises:
        ValueError: Propagated from ProjectService.accept_translation when the operation is invalid
                    (e.g., project not found, translation not ready for acceptance).
    """
    """API endpoint for customer to accept a translation."""
    try:
        ProjectService.accept_translation(project_id)
        return jsonify({'message': 'Translation accepted successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/reject', methods=['POST'])
@login_required_api
@require_role('CUSTOMER')
def reject_translation(project_id):
    """
    API endpoint for rejecting a translation for a given project.
    This endpoint expects a JSON payload containing optional feedback from the customer
    explaining the reason for rejection. It delegates the rejection logic to
    ProjectService.reject_translation and returns an appropriate HTTP response.
    Parameters:
        project_id (int or str): Unique identifier of the project whose translation is being rejected.
    Request JSON:
        feedback (str, optional): Customer-provided feedback detailing why the translation is rejected.
    Returns:
        tuple: A Flask response tuple:
            - On success: (jsonify({'message': 'Translation rejected successfully.'}), 200)
            - On client error: (jsonify({'error': <error_message>}), 400)
    Raises:
        ValueError: Propagated from ProjectService.reject_translation when validation fails
                    (e.g., invalid project ID, disallowed state transition, or missing requirements).
    """
    feedback = request.json.get('feedback')

    try:
        ProjectService.reject_translation(project_id, feedback)
        return jsonify({'message': 'Translation rejected successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/close', methods=['POST'])
@login_required_api
@require_role('ADMINISTRATOR')
def close_project(project_id):
    """Close a project by its unique identifier.

    This API endpoint delegates to `ProjectService.close_project` to perform the
    closure operation and returns a JSON response indicating success or failure.

    Parameters:
        project_id (int | str): The unique identifier of the project to close.

    Returns:
        tuple: A tuple of (flask.Response, int) where:
            - On success: JSON response {'message': 'Project closed successfully.'}, HTTP 200.
            - On failure: JSON response {'error': '<error message>'}, HTTP 400.

    Raises:
        ValueError: Propagated from `ProjectService.close_project` when the project
            cannot be closed (e.g., invalid ID, project not found, or business rule violation).
    """
    try:
        ProjectService.close_project(project_id)
        return jsonify({'message': 'Project closed successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/download/original', methods=['GET'])
@login_required_api
@require_role('CUSTOMER', 'TRANSLATOR', 'ADMINISTRATOR')
def download_original_file(project_id):
    """
    API endpoint to download the original file associated with a given project.
    This endpoint retrieves the original file for the specified project ID using
    `ProjectService.get_original_file` and returns it as an attachment via Flask's
    `send_file`. If the project does not exist or the original file cannot be found,
    a JSON error response is returned with HTTP status code 400.
    Args:
        project_id (int): Unique identifier of the project whose original file
            should be downloaded.
    Returns:
        flask.Response: A file download response with the original filename set via
            `download_name` when successful.
        tuple[flask.Response, int]: A JSON error response and HTTP 400 status code
            when a `ValueError` is raised (e.g., invalid project ID or missing file).
    Raises:
        None: Exceptions are handled internally; `ValueError` results in a 400 response.
    """
    try:
        file, filename = ProjectService.get_original_file(project_id)
        return send_file(file,
                        as_attachment=True,
                        download_name=filename)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/download/translation', methods=['GET'])
@login_required_api
@require_role('CUSTOMER', 'TRANSLATOR', 'ADMINISTRATOR')
def download_translated_file(project_id):
    """
    Handle download of a translated file for a given project.
    This controller action retrieves the translated file associated with the provided
    project ID via ProjectService and returns it as a downloadable attachment. If the
    project does not have a translated file or the ID is invalid, a JSON error response
    with HTTP 400 is returned.
    Parameters:
        project_id (int | str): Identifier of the project whose translated file should be downloaded.
    Returns:
        flask.Response: A response that either:
            - sends the translated file as an attachment with the appropriate filename, or
            - returns a JSON error payload with status code 400 if the file cannot be retrieved.
    Raises:
        ValueError: Propagated from ProjectService when the translated file cannot be found or retrieved.
    """

    try:
        file, filename = ProjectService.get_translated_file(project_id)
        return send_file(file,
                         as_attachment=True,
                         download_name=filename)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@proj_bp.route('/project/<project_id>/upload', methods=['POST'])
@login_required_api
@require_role('TRANSLATOR')
def upload_translated_file(project_id):
    """
    Handle uploading of a translated file for a specific project.
    This Flask view function expects a multipart/form-data request containing a file
    under the 'translated_file' key. It delegates the persistence of the uploaded file
    to ProjectService.save_translated_file and returns a JSON response indicating success
    or failure.
    Parameters:
        project_id (int | str): Identifier of the project to which the translated file belongs.
    Request:
        - Method: POST
        - Content-Type: multipart/form-data
        - Form fields:
            - translated_file (FileStorage): The translated file to upload.
    Returns:
        tuple[flask.Response, int]: A JSON response and corresponding HTTP status code.
            - 200 on success with payload: {'message': 'Translated file uploaded successfully.'}
            - 400 on validation or processing error with payload: {'error': '<error message>'}
    Raises:
        None directly. Any ValueError from ProjectService.save_translated_file is caught
        and converted to a 400 response.
    Side Effects:
        Persists the uploaded translated file using ProjectService.save_translated_file.
    Notes:
        - Ensure the request includes 'translated_file' in request.files.
        - The ProjectService is responsible for validating file presence, type, and storage.
    """
    translated_file = request.files.get('translated_file')

    try:
        ProjectService.save_translated_file(project_id, translated_file)
        return jsonify({'message': 'Translated file uploaded successfully.'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400