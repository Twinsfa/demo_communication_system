from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import RewardAndDiscipline, User, Student, Department, UserRole, Role
from app import db
from datetime import datetime

rewards_bp = Blueprint('rewards', __name__)

def get_user_roles(user_id):
    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    return Role.query.filter(Role.id.in_(role_ids)).all()

@rewards_bp.route('/', methods=['POST'])
@jwt_required()
def create_reward_discipline():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user is department
    roles = get_user_roles(user_id)
    if not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Only departments can create rewards/discipline records'}), 403
    
    # Validate required fields
    if not all(k in data for k in ['type', 'content', 'date', 'student_id']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Validate type
    if data['type'] not in ['reward', 'discipline']:
        return jsonify({'message': 'Invalid type'}), 400
    
    # Validate student exists
    student = Student.query.get(data['student_id'])
    if not student:
        return jsonify({'message': 'Student not found'}), 404
    
    # Get department
    department = Department.query.filter_by(user_id=user_id).first()
    if not department:
        return jsonify({'message': 'Department profile not found'}), 404
    
    # Create record
    record = RewardAndDiscipline(
        type=data['type'],
        content=data['content'],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        student_id=student.id,
        department_id=department.id
    )
    
    db.session.add(record)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Record created successfully',
            'record_id': record.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error creating record'}), 500

@rewards_bp.route('/', methods=['GET'])
@jwt_required()
def get_rewards_discipline():
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    # Base query
    query = RewardAndDiscipline.query
    
    # Filter based on user role
    if any(role.name == 'student' for role in roles):
        # Students can only see their own records
        student = Student.query.filter_by(user_id=user_id).first()
        if student:
            query = query.filter_by(student_id=student.id)
    elif any(role.name == 'parent' for role in roles):
        # Parents can see records of their children
        parent = User.query.get(user_id).parent
        if parent:
            student_ids = [student.id for student in parent.students]
            query = query.filter(RewardAndDiscipline.student_id.in_(student_ids))
    elif any(role.name == 'department' for role in roles):
        # Departments can see all records
        pass
    else:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Apply filters
    record_type = request.args.get('type')
    student_id = request.args.get('student_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if record_type:
        query = query.filter_by(type=record_type)
    if student_id:
        query = query.filter_by(student_id=student_id)
    if start_date:
        query = query.filter(RewardAndDiscipline.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(RewardAndDiscipline.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    records = query.order_by(RewardAndDiscipline.date.desc()).all()
    
    return jsonify([{
        'id': record.id,
        'type': record.type,
        'content': record.content,
        'date': record.date.isoformat(),
        'student': {
            'id': record.student.id,
            'full_name': record.student.full_name
        },
        'department': {
            'id': record.department.id,
            'name': record.department.name
        }
    } for record in records]), 200

@rewards_bp.route('/<int:record_id>', methods=['GET'])
@jwt_required()
def get_record(record_id):
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    record = RewardAndDiscipline.query.get(record_id)
    if not record:
        return jsonify({'message': 'Record not found'}), 404
    
    # Check permissions
    if any(role.name == 'student' for role in roles):
        student = Student.query.filter_by(user_id=user_id).first()
        if not student or record.student_id != student.id:
            return jsonify({'message': 'Unauthorized'}), 403
    elif any(role.name == 'parent' for role in roles):
        parent = User.query.get(user_id).parent
        if not parent or record.student_id not in [student.id for student in parent.students]:
            return jsonify({'message': 'Unauthorized'}), 403
    elif not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify({
        'id': record.id,
        'type': record.type,
        'content': record.content,
        'date': record.date.isoformat(),
        'student': {
            'id': record.student.id,
            'full_name': record.student.full_name
        },
        'department': {
            'id': record.department.id,
            'name': record.department.name
        }
    }), 200

@rewards_bp.route('/<int:record_id>', methods=['PUT'])
@jwt_required()
def update_record(record_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user is department
    roles = get_user_roles(user_id)
    if not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Only departments can update records'}), 403
    
    record = RewardAndDiscipline.query.get(record_id)
    if not record:
        return jsonify({'message': 'Record not found'}), 404
    
    # Update fields
    if 'content' in data:
        record.content = data['content']
    if 'date' in data:
        record.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    try:
        db.session.commit()
        return jsonify({'message': 'Record updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating record'}), 500

@rewards_bp.route('/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_record(record_id):
    user_id = get_jwt_identity()
    
    # Check if user is department
    roles = get_user_roles(user_id)
    if not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Only departments can delete records'}), 403
    
    record = RewardAndDiscipline.query.get(record_id)
    if not record:
        return jsonify({'message': 'Record not found'}), 404
    
    db.session.delete(record)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Record deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error deleting record'}), 500 