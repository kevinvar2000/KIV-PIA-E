from flask import Blueprint, request, jsonify, session
from flask.views import MethodView

customer_service = Blueprint('customer_service', __name__)

# Mock database
projects = []
project_id_counter = 1

def get_current_user_id():
    # Replace with real authentication/session logic
    return session.get('user_id', 1)

class ProjectAPI(MethodView):
    def post(self):
        """Create new project"""
        global project_id_counter
        data = request.json
        project = {
            'id': project_id_counter,
            'customer_id': get_current_user_id(),
            'title': data.get('title'),
            'description': data.get('description'),
            'status': 'pending',
            'translator_feedback': None
        }
        projects.append(project)
        project_id_counter += 1
        return jsonify(project), 201

    def get(self):
        """List own projects"""
        user_id = get_current_user_id()
        user_projects = [p for p in projects if p['customer_id'] == user_id]
        return jsonify(user_projects), 200

@customer_service.route('/projects/<int:project_id>/accept', methods=['POST'])
def accept_project(project_id):
    """Accept completed project"""
    user_id = get_current_user_id()
    for project in projects:
        if project['id'] == project_id and project['customer_id'] == user_id:
            if project['status'] == 'completed':
                project['status'] = 'accepted'
                return jsonify({'message': 'Project accepted.'}), 200
            return jsonify({'error': 'Project not completed yet.'}), 400
    return jsonify({'error': 'Project not found.'}), 404

@customer_service.route('/projects/<int:project_id>/reject', methods=['POST'])
def reject_project(project_id):
    """Reject completed project with feedback"""
    user_id = get_current_user_id()
    data = request.json
    feedback = data.get('feedback')
    for project in projects:
        if project['id'] == project_id and project['customer_id'] == user_id:
            if project['status'] == 'completed':
                project['status'] = 'rejected'
                project['translator_feedback'] = feedback
                return jsonify({'message': 'Project rejected with feedback.'}), 200
            return jsonify({'error': 'Project not completed yet.'}), 400
    return jsonify({'error': 'Project not found.'}), 404

# Register the ProjectAPI view
project_view = ProjectAPI.as_view('project_api')
customer_service.add_url_rule('/projects', view_func=project_view, methods=['POST', 'GET'])