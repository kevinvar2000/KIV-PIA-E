from flask import Blueprint, request, jsonify
from models import Project, Feedback, User
from services.EmailService import send_message, send_email

email_bp = Blueprint('email_bp', __name__)


@email_bp.route('/feedback/respond', methods=['POST'])
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
