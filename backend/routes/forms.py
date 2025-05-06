from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Form, User
from app import db
from datetime import datetime

forms_bp = Blueprint('forms', __name__)

def is_school_or_teacher():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.role in ['school', 'teacher']

@forms_bp.route('/', methods=['GET'])
@jwt_required()
def get_forms():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Get query parameters
    form_type = request.args.get('type')
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Base query
    query = Form.query
    
    # Filter based on user role
    if user.role == 'parent':
        query = query.filter_by(sender_id=user_id)
    elif user.role == 'teacher':
        # Teachers can see forms from parents of their students
        query = query.join(User, Form.sender_id == User.id).filter(
            (User.parent_id == user_id) |  # Forms from their students' parents
            (Form.receiver_id == user_id)  # Forms directly sent to them
        )
    elif user.role == 'school':
        # School can see all forms
        pass
    else:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Apply additional filters
    if form_type:
        query = query.filter_by(form_type=form_type)
    if status:
        query = query.filter_by(status=status)
    
    # Order by creation date and paginate
    forms = query.order_by(Form.created_at.desc()).offset(offset).limit(limit).all()
    
    return jsonify([{
        'id': form.id,
        'title': form.title,
        'content': form.content,
        'sender_id': form.sender_id,
        'sender_name': User.query.get(form.sender_id).full_name,
        'receiver_id': form.receiver_id,
        'receiver_name': User.query.get(form.receiver_id).full_name,
        'form_type': form.form_type,
        'status': form.status,
        'created_at': form.created_at.isoformat(),
        'response': form.response,
        'response_date': form.response_date.isoformat() if form.response_date else None,
        'attachments': form.attachments
    } for form in forms]), 200

@forms_bp.route('/', methods=['POST'])
@jwt_required()
def create_form():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'parent':
        return jsonify({'message': 'Only parents can submit forms'}), 403
    
    data = request.get_json()
    
    # Validate receiver exists and is appropriate
    receiver = User.query.get(data['receiver_id'])
    if not receiver:
        return jsonify({'message': 'Receiver not found'}), 404
    
    if receiver.role not in ['school', 'teacher']:
        return jsonify({'message': 'Invalid receiver role'}), 400
    
    form = Form(
        title=data['title'],
        content=data['content'],
        sender_id=user_id,
        receiver_id=data['receiver_id'],
        form_type=data['form_type'],
        attachments=data.get('attachments')
    )
    
    db.session.add(form)
    db.session.commit()
    
    return jsonify({
        'id': form.id,
        'title': form.title,
        'content': form.content,
        'sender_id': form.sender_id,
        'receiver_id': form.receiver_id,
        'form_type': form.form_type,
        'status': form.status,
        'created_at': form.created_at.isoformat(),
        'attachments': form.attachments
    }), 201

@forms_bp.route('/<int:form_id>/respond', methods=['POST'])
@jwt_required()
def respond_to_form(form_id):
    if not is_school_or_teacher():
        return jsonify({'message': 'Unauthorized'}), 403
    
    form = Form.query.get(form_id)
    if not form:
        return jsonify({'message': 'Form not found'}), 404
    
    data = request.get_json()
    
    form.status = data['status']
    form.response = data['response']
    form.response_date = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'id': form.id,
        'status': form.status,
        'response': form.response,
        'response_date': form.response_date.isoformat()
    }), 200

@forms_bp.route('/<int:form_id>', methods=['GET'])
@jwt_required()
def get_form(form_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    form = Form.query.get(form_id)
    if not form:
        return jsonify({'message': 'Form not found'}), 404
    
    # Check permissions
    if user.role == 'parent' and form.sender_id != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    elif user.role == 'teacher' and form.receiver_id != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify({
        'id': form.id,
        'title': form.title,
        'content': form.content,
        'sender_id': form.sender_id,
        'sender_name': User.query.get(form.sender_id).full_name,
        'receiver_id': form.receiver_id,
        'receiver_name': User.query.get(form.receiver_id).full_name,
        'form_type': form.form_type,
        'status': form.status,
        'created_at': form.created_at.isoformat(),
        'response': form.response,
        'response_date': form.response_date.isoformat() if form.response_date else None,
        'attachments': form.attachments
    }), 200 