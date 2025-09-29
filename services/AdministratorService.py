from flask import Blueprint, request, jsonify
from Model import Project, Feedback, User  # Assuming you have these models
from AdministratorService import send_message, send_email  # Placeholder for your messaging/email logic

admin_service = Blueprint('admin_service', __name__)

@admin_service.route('/projects/with-feedback', methods=['GET'])
def get_projects_with_feedback():
    state = request.args.get('state')
    query = Project.query.join(Feedback).distinct()
    if state:
        query = query.filter(Project.state == state)
    projects = query.all()
    result = [
        {
            'id': p.id,
            'name': p.name,
            'state': p.state,
            'feedback_count': len(p.feedbacks)
        }
        for p in projects
    ]
    return jsonify(result), 200

@admin_service.route('/feedback/respond', methods=['POST'])
def respond_to_feedback():
    data = request.json
    feedback_id = data.get('feedback_id')
    message = data.get('message')
    method = data.get('method', 'in-app')  # 'in-app' or 'email'

    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404

    recipient = User.query.get(feedback.user_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404

    if method == 'email':
        send_email(recipient.email, "Response to your feedback", message)
    else:
        send_message(recipient.id, message)

    return jsonify({'status': 'Message sent'}), 200

@admin_service.route('/projects/<int:project_id>/close', methods=['POST'])
def close_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    project.state = 'closed'
    return jsonify({'status': 'Project closed'}), 200