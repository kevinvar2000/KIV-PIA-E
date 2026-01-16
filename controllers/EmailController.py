from flask import Blueprint, request, jsonify
from services.EmailService import EmailService
from services.UserService import UserService
from services.ProjectService import ProjectService
from services.AuthService import login_required_api, require_role

email_bp = Blueprint('email_bp', __name__)

@login_required_api
@require_role('ADMINISTRATOR')
@email_bp.route('/email/respond', methods=['POST'])
def respond_to_feedback():
    """
    Admin sends a response message via email to either the customer or translator.
    Expected JSON:
    {
      "project_id": "...",
      "recipient_user_id": "...",
      "subject": "...",
      "body": "..."
    }
    """
    data = request.get_json(silent=True) or {}

    project_id = data.get('project_id')
    recipient_user_id = data.get('recipient_user_id')
    subject = (data.get('subject') or '').strip()
    body = (data.get('body') or '').strip()

    if not project_id:
        print(f"[EmailController.py] project_id is missing in request.", flush=True)
        return jsonify({'error': 'project_id is required'}), 400
    if not recipient_user_id:
        print(f"[EmailController.py] recipient_user_id is missing in request.", flush=True)
        return jsonify({'error': 'recipient_user_id is required'}), 400
    if not subject:
        print(f"[EmailController.py] subject is missing in request.", flush=True)
        return jsonify({'error': 'subject is required'}), 400
    if not body:
        print(f"[EmailController.py] body is missing in request.", flush=True)
        return jsonify({'error': 'body is required'}), 400

    project = ProjectService.get_project_by_id(project_id)
    if not project:
        print(f"[EmailController.py] Project not found: {project_id}", flush=True)
        return jsonify({'error': 'Project not found'}), 404

    project_customer_id = project.customer_id
    project_translator_id = project.translator_id

    if recipient_user_id not in [project_customer_id, project_translator_id]:
        print(f"[EmailController.py] Recipient user ID {recipient_user_id} does not belong to project {project_id}", flush=True)
        return jsonify({'error': 'Recipient does not belong to this project'}), 400

    recipient = UserService.get_user_by_id(recipient_user_id)
    if not recipient:
        print(f"[EmailController.py] Recipient user not found: {recipient_user_id}", flush=True)
        return jsonify({'error': 'Recipient not found'}), 404

    recipient_email = recipient.email if hasattr(recipient, 'email') else recipient.get('email') if isinstance(recipient, dict) else None
    if not recipient_email:
        print(f"[EmailController.py] Recipient has no email: {recipient_user_id}", flush=True)
        return jsonify({'error': 'Recipient has no email'}), 400

    try:
        EmailService.send_email(recipient_email, subject, body)
    except Exception as e:
        print(f"[EmailController.py] Failed to send email to {recipient_email}: {e}", flush=True)
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500

    return jsonify({
        'status': 'Message sent',
        'project_id': project_id,
        'recipient_user_id': recipient_user_id,
    }), 200
