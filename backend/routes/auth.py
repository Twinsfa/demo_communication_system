from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, UserRole, Role, Teacher, Parent, Student, Department
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'password', 'role_type', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400

    # Create user
    user = User(username=data['username'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()  # Get user ID

    # Get role
    role = Role.query.filter_by(name=data['role_type']).first()
    if not role:
        return jsonify({'message': 'Invalid role type'}), 400

    # Assign role to user
    user_role = UserRole(user_id=user.id, role_id=role.id)
    db.session.add(user_role)

    # Create role-specific profile
    if data['role_type'] == 'teacher':
        teacher = Teacher(
            full_name=data.get('full_name'),
            email=data['email'],
            type=data.get('type', 'subject_teacher'),
            user_id=user.id
        )
        db.session.add(teacher)
    elif data['role_type'] == 'parent':
        parent = Parent(
            name=data.get('full_name'),
            email=data['email'],
            phone=data.get('phone'),
            user_id=user.id
        )
        db.session.add(parent)
    elif data['role_type'] == 'student':
        student = Student(
            full_name=data.get('full_name'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            user_id=user.id
        )
        db.session.add(student)

    try:
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error registering user'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role_type = data.get('role_type')  # teacher, student, parent

    if not username or not password or not role_type:
        return jsonify({'message': 'Missing required fields'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid username or password'}), 401

    # Check if user has the requested role
    user_roles = UserRole.query.filter_by(user_id=user.id).all()
    role_ids = [ur.role_id for ur in user_roles]
    roles = Role.query.filter(Role.id.in_(role_ids)).all()
    
    if not any(role.name == role_type for role in roles):
        return jsonify({'message': 'User does not have the requested role'}), 403

    # Get additional user info based on role
    user_info = {}
    if role_type == 'teacher':
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if teacher:
            user_info = {
                'id': teacher.id,
                'full_name': teacher.full_name,
                'type': teacher.type,  # homeroom_teacher or subject_teacher
                'email': teacher.email
            }
    elif role_type == 'parent':
        parent = Parent.query.filter_by(user_id=user.id).first()
        if parent:
            user_info = {
                'id': parent.id,
                'name': parent.name,
                'email': parent.email,
                'phone': parent.phone
            }
    elif role_type == 'student':
        student = Student.query.filter_by(user_id=user.id).first()
        if student:
            user_info = {
                'id': student.id,
                'full_name': student.full_name,
                'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                'gender': student.gender
            }

    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'user_info': user_info,
        'role': role_type
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Get user roles
    user_roles = UserRole.query.filter_by(user_id=user.id).all()
    role_ids = [ur.role_id for ur in user_roles]
    roles = Role.query.filter(Role.id.in_(role_ids)).all()
    
    profile = {
        'username': user.username,
        'roles': [role.name for role in roles],
        'status': user.status
    }

    # Add role-specific information
    for role in roles:
        if role.name == 'teacher':
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            if teacher:
                profile['teacher_info'] = {
                    'id': teacher.id,
                    'full_name': teacher.full_name,
                    'type': teacher.type,
                    'email': teacher.email
                }
        elif role.name == 'parent':
            parent = Parent.query.filter_by(user_id=user.id).first()
            if parent:
                profile['parent_info'] = {
                    'id': parent.id,
                    'name': parent.name,
                    'email': parent.email,
                    'phone': parent.phone
                }
        elif role.name == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                profile['student_info'] = {
                    'id': student.id,
                    'full_name': student.full_name,
                    'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                    'gender': student.gender
                }

    return jsonify(profile), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
        
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'full_name': user.full_name
    }), 200

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role != 'school':
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'full_name': user.full_name,
        'class_name': user.class_name
    } for user in users])

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role != 'school':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        user.role = data['role']
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'class_name' in data:
        user.class_name = data['class_name']
    
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role != 'school':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}) 