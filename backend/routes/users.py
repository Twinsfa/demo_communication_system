from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, UserRole, Role, Teacher, Parent, Student, Department
from app import db
from datetime import datetime

users_bp = Blueprint('users', __name__)

def get_user_roles(user_id):
    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    return Role.query.filter(Role.id.in_(role_ids)).all()

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    # Check if user has permission to view all users
    if not any(role.name in ['school', 'department'] for role in roles):
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Get query parameters
    role_type = request.args.get('role_type')
    status = request.args.get('status')
    search = request.args.get('search')
    
    # Base query
    query = User.query
    
    # Apply filters
    if role_type:
        role = Role.query.filter_by(name=role_type).first()
        if role:
            query = query.join(UserRole).filter(UserRole.role_id == role.id)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(User.username.ilike(f'%{search}%'))
    
    users = query.all()
    
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'status': user.status,
        'roles': [role.name for role in get_user_roles(user.id)],
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'profile': get_user_profile(user)
    } for user in users]), 200

def get_user_profile(user):
    roles = get_user_roles(user.id)
    profile = {}
    
    for role in roles:
        if role.name == 'teacher':
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            if teacher:
                profile['teacher'] = {
                    'id': teacher.id,
                    'full_name': teacher.full_name,
                    'type': teacher.type,
                    'email': teacher.email,
                    'phone': teacher.phone
                }
        elif role.name == 'parent':
            parent = Parent.query.filter_by(user_id=user.id).first()
            if parent:
                profile['parent'] = {
                    'id': parent.id,
                    'full_name': parent.full_name,
                    'email': parent.email,
                    'phone': parent.phone,
                    'address': parent.address
                }
        elif role.name == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                profile['student'] = {
                    'id': student.id,
                    'full_name': student.full_name,
                    'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                    'gender': student.gender,
                    'address': student.address
                }
        elif role.name == 'department':
            department = Department.query.filter_by(user_id=user.id).first()
            if department:
                profile['department'] = {
                    'id': department.id,
                    'name': department.name,
                    'email': department.email,
                    'phone': department.phone
                }
    
    return profile

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    roles = get_user_roles(current_user_id)
    
    # Check if user has permission to view other users
    if not any(role.name in ['school', 'department'] for role in roles):
        if current_user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'status': user.status,
        'roles': [role.name for role in get_user_roles(user.id)],
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'profile': get_user_profile(user)
    }), 200

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    roles = get_user_roles(current_user_id)
    
    # Check if user has permission to update users
    if not any(role.name in ['school', 'department'] for role in roles):
        if current_user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update basic user info
    if 'email' in data:
        user.email = data['email']
    if 'status' in data:
        if any(role.name in ['school', 'department'] for role in roles):
            user.status = data['status']
    
    # Update role-specific profile
    user_roles = get_user_roles(user.id)
    for role in user_roles:
        if role.name == 'teacher' and 'teacher' in data:
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            if teacher:
                if 'full_name' in data['teacher']:
                    teacher.full_name = data['teacher']['full_name']
                if 'phone' in data['teacher']:
                    teacher.phone = data['teacher']['phone']
        
        elif role.name == 'parent' and 'parent' in data:
            parent = Parent.query.filter_by(user_id=user.id).first()
            if parent:
                if 'full_name' in data['parent']:
                    parent.full_name = data['parent']['full_name']
                if 'phone' in data['parent']:
                    parent.phone = data['parent']['phone']
                if 'address' in data['parent']:
                    parent.address = data['parent']['address']
        
        elif role.name == 'student' and 'student' in data:
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                if 'full_name' in data['student']:
                    student.full_name = data['student']['full_name']
                if 'address' in data['student']:
                    student.address = data['student']['address']
        
        elif role.name == 'department' and 'department' in data:
            department = Department.query.filter_by(user_id=user.id).first()
            if department:
                if 'name' in data['department']:
                    department.name = data['department']['name']
                if 'phone' in data['department']:
                    department.phone = data['department']['phone']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'status': user.status,
                'roles': [role.name for role in get_user_roles(user.id)],
                'profile': get_user_profile(user)
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating user'}), 500

@users_bp.route('/<int:user_id>/status', methods=['PUT'])
@jwt_required()
def update_user_status(user_id):
    current_user_id = get_jwt_identity()
    roles = get_user_roles(current_user_id)
    
    # Only school and department can update user status
    if not any(role.name in ['school', 'department'] for role in roles):
        return jsonify({'message': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    if 'status' not in data:
        return jsonify({'message': 'Status is required'}), 400
    
    if data['status'] not in ['active', 'inactive', 'suspended']:
        return jsonify({'message': 'Invalid status'}), 400
    
    user.status = data['status']
    
    try:
        db.session.commit()
        return jsonify({'message': 'User status updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating user status'}), 500

@users_bp.route('/<int:user_id>/roles', methods=['PUT'])
@jwt_required()
def update_user_roles(user_id):
    current_user_id = get_jwt_identity()
    roles = get_user_roles(current_user_id)
    
    # Only school can update user roles
    if not any(role.name == 'school' for role in roles):
        return jsonify({'message': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    if 'roles' not in data:
        return jsonify({'message': 'Roles are required'}), 400
    
    # Validate roles
    valid_roles = ['school', 'department', 'teacher', 'parent', 'student']
    if not all(role in valid_roles for role in data['roles']):
        return jsonify({'message': 'Invalid role(s)'}), 400
    
    # Remove existing roles
    UserRole.query.filter_by(user_id=user_id).delete()
    
    # Add new roles
    for role_name in data['roles']:
        role = Role.query.filter_by(name=role_name).first()
        if role:
            user_role = UserRole(user_id=user_id, role_id=role.id)
            db.session.add(user_role)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'User roles updated successfully',
            'roles': data['roles']
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating user roles'}), 500 