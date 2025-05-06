from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Class
from app import db

users_bp = Blueprint('users', __name__)

def is_school_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.role == 'school'

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not is_school_admin():
        return jsonify({'message': 'Unauthorized'}), 403
    
    role = request.args.get('role')
    query = User.query
    
    if role:
        query = query.filter_by(role=role)
    
    users = query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'full_name': user.full_name,
        'class_id': user.class_id,
        'parent_id': user.parent_id
    } for user in users]), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Check permissions
    if not is_school_admin() and current_user_id != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'full_name': user.full_name,
        'class_id': user.class_id,
        'parent_id': user.parent_id
    }), 200

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    if not is_school_admin():
        return jsonify({'message': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'email' in data:
        user.email = data['email']
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'role' in data:
        user.role = data['role']
    if 'class_id' in data:
        user.class_id = data['class_id']
    if 'parent_id' in data:
        user.parent_id = data['parent_id']
    
    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    if not is_school_admin():
        return jsonify({'message': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

@users_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_classes():
    classes = Class.query.all()
    return jsonify([{
        'id': class_.id,
        'name': class_.name,
        'grade_level': class_.grade_level,
        'teacher_id': class_.teacher_id
    } for class_ in classes]), 200

@users_bp.route('/classes', methods=['POST'])
@jwt_required()
def create_class():
    if not is_school_admin():
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    class_ = Class(
        name=data['name'],
        grade_level=data['grade_level'],
        teacher_id=data.get('teacher_id')
    )
    
    db.session.add(class_)
    db.session.commit()
    
    return jsonify({
        'id': class_.id,
        'name': class_.name,
        'grade_level': class_.grade_level,
        'teacher_id': class_.teacher_id
    }), 201 