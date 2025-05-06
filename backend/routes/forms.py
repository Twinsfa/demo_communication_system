from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import RequestForm, User, Parent, Department, UserRole, Role
from app import db
from datetime import datetime

forms_bp = Blueprint('forms', __name__)

def get_user_roles(user_id):
    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    return Role.query.filter(Role.id.in_(role_ids)).all()

@forms_bp.route('/', methods=['POST'])
@jwt_required()
def submit_form():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user is a parent
    roles = get_user_roles(user_id)
    if not any(role.name == 'parent' for role in roles):
        return jsonify({'message': 'Only parents can submit forms'}), 403
    
    # Validate required fields
    if not all(k in data for k in ['type', 'content']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Get parent
    parent = Parent.query.filter_by(user_id=user_id).first()
    if not parent:
        return jsonify({'message': 'Parent profile not found'}), 404
    
    # Create form
    form = RequestForm(
        type=data['type'],
        content=data['content'],
        parent_id=parent.id,
        department_id=data.get('department_id'),  # Optional, can be assigned later
        status='pending'
    )
    
    db.session.add(form)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Form submitted successfully',
            'form_id': form.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error submitting form'}), 500

@forms_bp.route('/', methods=['GET'])
@jwt_required()
def get_forms():
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    # Base query
    query = RequestForm.query
    
    # Filter based on user role
    if any(role.name == 'parent' for role in roles):
        # Parents can only see their own forms
        parent = Parent.query.filter_by(user_id=user_id).first()
        if parent:
            query = query.filter_by(parent_id=parent.id)
    elif any(role.name == 'department' for role in roles):
        # Departments can see all forms
        pass
    else:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Apply filters
    form_type = request.args.get('type')
    status = request.args.get('status')
    
    if form_type:
        query = query.filter_by(type=form_type)
    if status:
        query = query.filter_by(status=status)
    
    forms = query.order_by(RequestForm.submission_date.desc()).all()
    
    return jsonify([{
        'id': form.id,
        'type': form.type,
        'content': form.content,
        'submission_date': form.submission_date.isoformat(),
        'status': form.status,
        'parent': {
            'id': form.parent.id,
            'name': form.parent.name,
            'email': form.parent.email
        } if form.parent else None,
        'department': {
            'id': form.department.id,
            'name': form.department.name
        } if form.department else None
    } for form in forms]), 200

@forms_bp.route('/<int:form_id>', methods=['GET'])
@jwt_required()
def get_form(form_id):
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    form = RequestForm.query.get(form_id)
    if not form:
        return jsonify({'message': 'Form not found'}), 404
    
    # Check permissions
    if any(role.name == 'parent' for role in roles):
        parent = Parent.query.filter_by(user_id=user_id).first()
        if not parent or form.parent_id != parent.id:
            return jsonify({'message': 'Unauthorized'}), 403
    elif not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify({
        'id': form.id,
        'type': form.type,
        'content': form.content,
        'submission_date': form.submission_date.isoformat(),
        'status': form.status,
        'parent': {
            'id': form.parent.id,
            'name': form.parent.name,
            'email': form.parent.email
        } if form.parent else None,
        'department': {
            'id': form.department.id,
            'name': form.department.name
        } if form.department else None
    }), 200

@forms_bp.route('/<int:form_id>/status', methods=['PUT'])
@jwt_required()
def update_form_status(form_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user is department
    roles = get_user_roles(user_id)
    if not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Only departments can update form status'}), 403
    
    if 'status' not in data:
        return jsonify({'message': 'Status is required'}), 400
    
    if data['status'] not in ['pending', 'processing', 'completed']:
        return jsonify({'message': 'Invalid status'}), 400
    
    form = RequestForm.query.get(form_id)
    if not form:
        return jsonify({'message': 'Form not found'}), 404
    
    form.status = data['status']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Form status updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating form status'}), 500

@forms_bp.route('/<int:form_id>/assign', methods=['PUT'])
@jwt_required()
def assign_form(form_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user is department
    roles = get_user_roles(user_id)
    if not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Only departments can assign forms'}), 403
    
    if 'department_id' not in data:
        return jsonify({'message': 'Department ID is required'}), 400
    
    form = RequestForm.query.get(form_id)
    if not form:
        return jsonify({'message': 'Form not found'}), 404
    
    department = Department.query.get(data['department_id'])
    if not department:
        return jsonify({'message': 'Department not found'}), 404
    
    form.department_id = department.id
    form.status = 'processing'
    
    try:
        db.session.commit()
        return jsonify({'message': 'Form assigned successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error assigning form'}), 500 