from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Reward, User, Class
from app import db
from datetime import datetime

rewards_bp = Blueprint('rewards', __name__)

def is_school_or_teacher():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.role in ['school', 'teacher']

@rewards_bp.route('/', methods=['GET'])
@jwt_required()
def get_rewards():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Get query parameters
    student_id = request.args.get('student_id')
    reward_type = request.args.get('type')
    category = request.args.get('category')
    class_id = request.args.get('class_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = Reward.query
    
    # Filter based on user role
    if user.role == 'student':
        query = query.filter_by(student_id=user_id)
    elif user.role == 'parent':
        # Parents can see rewards of their children
        query = query.join(User, Reward.student_id == User.id).filter(User.parent_id == user_id)
    elif user.role == 'teacher':
        # Teachers can see rewards of their students
        query = query.join(User, Reward.student_id == User.id).filter(User.class_id == user.class_id)
    elif user.role == 'school':
        # School can see all rewards
        pass
    else:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Apply additional filters
    if student_id:
        query = query.filter_by(student_id=student_id)
    if reward_type:
        query = query.filter_by(type=reward_type)
    if category:
        query = query.filter_by(category=category)
    if class_id:
        query = query.join(User, Reward.student_id == User.id).filter(User.class_id == class_id)
    if start_date:
        query = query.filter(Reward.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Reward.date <= datetime.fromisoformat(end_date))
    
    rewards = query.order_by(Reward.date.desc()).all()
    
    return jsonify([{
        'id': reward.id,
        'student_id': reward.student_id,
        'student_name': User.query.get(reward.student_id).full_name,
        'type': reward.type,
        'description': reward.description,
        'date': reward.date.isoformat(),
        'teacher_id': reward.teacher_id,
        'teacher_name': User.query.get(reward.teacher_id).full_name,
        'points': reward.points,
        'category': reward.category
    } for reward in rewards]), 200

@rewards_bp.route('/', methods=['POST'])
@jwt_required()
def create_reward():
    if not is_school_or_teacher():
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    user_id = get_jwt_identity()
    
    # Validate student exists
    student = User.query.get(data['student_id'])
    if not student or student.role != 'student':
        return jsonify({'message': 'Invalid student'}), 400
    
    reward = Reward(
        student_id=data['student_id'],
        type=data['type'],
        description=data['description'],
        date=datetime.fromisoformat(data['date']),
        teacher_id=user_id,
        points=data.get('points'),
        category=data.get('category')
    )
    
    db.session.add(reward)
    db.session.commit()
    
    return jsonify({
        'id': reward.id,
        'student_id': reward.student_id,
        'type': reward.type,
        'description': reward.description,
        'date': reward.date.isoformat(),
        'teacher_id': reward.teacher_id,
        'points': reward.points,
        'category': reward.category
    }), 201

@rewards_bp.route('/<int:reward_id>', methods=['PUT'])
@jwt_required()
def update_reward(reward_id):
    if not is_school_or_teacher():
        return jsonify({'message': 'Unauthorized'}), 403
    
    reward = Reward.query.get(reward_id)
    if not reward:
        return jsonify({'message': 'Reward not found'}), 404
    
    data = request.get_json()
    
    if 'description' in data:
        reward.description = data['description']
    if 'points' in data:
        reward.points = data['points']
    if 'category' in data:
        reward.category = data['category']
    
    db.session.commit()
    
    return jsonify({
        'id': reward.id,
        'student_id': reward.student_id,
        'type': reward.type,
        'description': reward.description,
        'date': reward.date.isoformat(),
        'teacher_id': reward.teacher_id,
        'points': reward.points,
        'category': reward.category
    }), 200

@rewards_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_reward_statistics():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['school', 'teacher']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    class_id = request.args.get('class_id')
    reward_type = request.args.get('type')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = Reward.query
    
    # Apply filters
    if class_id:
        query = query.join(User, Reward.student_id == User.id).filter(User.class_id == class_id)
    if reward_type:
        query = query.filter_by(type=reward_type)
    if category:
        query = query.filter_by(category=category)
    if start_date:
        query = query.filter(Reward.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Reward.date <= datetime.fromisoformat(end_date))
    
    rewards = query.all()
    
    # Calculate statistics
    total_rewards = len(rewards)
    total_points = sum(reward.points or 0 for reward in rewards)
    by_type = {}
    by_category = {}
    
    for reward in rewards:
        by_type[reward.type] = by_type.get(reward.type, 0) + 1
        if reward.category:
            by_category[reward.category] = by_category.get(reward.category, 0) + 1
    
    return jsonify({
        'total_rewards': total_rewards,
        'total_points': total_points,
        'by_type': by_type,
        'by_category': by_category
    }), 200 