from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Announcement, User, Class
from app import db
from datetime import datetime

announcements_bp = Blueprint('announcements', __name__)

def is_school_or_teacher():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.role in ['school', 'teacher']

@announcements_bp.route('/', methods=['GET'])
@jwt_required()
def get_announcements():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Get query parameters
    announcement_type = request.args.get('type')
    target_role = request.args.get('target_role')
    target_class = request.args.get('target_class')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Base query
    query = Announcement.query
    
    # Filter by type if specified
    if announcement_type:
        query = query.filter_by(announcement_type=announcement_type)
    
    # Filter by target role
    if target_role:
        query = query.filter_by(target_role=target_role)
    else:
        # Filter based on user's role
        if user.role == 'student':
            query = query.filter(
                (Announcement.target_role == 'all') |
                (Announcement.target_role == 'students') |
                ((Announcement.target_role == 'class') & (Announcement.target_class_id == user.class_id))
            )
        elif user.role == 'parent':
            query = query.filter(
                (Announcement.target_role == 'all') |
                (Announcement.target_role == 'parents')
            )
        elif user.role == 'teacher':
            query = query.filter(
                (Announcement.target_role == 'all') |
                (Announcement.target_role == 'teachers')
            )
    
    # Filter by target class
    if target_class:
        query = query.filter_by(target_class_id=target_class)
    
    # Order by creation date and paginate
    announcements = query.order_by(Announcement.created_at.desc()).offset(offset).limit(limit).all()
    
    return jsonify([{
        'id': ann.id,
        'title': ann.title,
        'content': ann.content,
        'sender_id': ann.sender_id,
        'sender_name': User.query.get(ann.sender_id).full_name,
        'target_role': ann.target_role,
        'target_class_id': ann.target_class_id,
        'created_at': ann.created_at.isoformat(),
        'event_date': ann.event_date.isoformat() if ann.event_date else None,
        'announcement_type': ann.announcement_type,
        'is_important': ann.is_important
    } for ann in announcements]), 200

@announcements_bp.route('/', methods=['POST'])
@jwt_required()
def create_announcement():
    if not is_school_or_teacher():
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    user_id = get_jwt_identity()
    
    announcement = Announcement(
        title=data['title'],
        content=data['content'],
        sender_id=user_id,
        target_role=data['target_role'],
        target_class_id=data.get('target_class_id'),
        event_date=datetime.fromisoformat(data['event_date']) if data.get('event_date') else None,
        announcement_type=data['announcement_type'],
        is_important=data.get('is_important', False)
    )
    
    db.session.add(announcement)
    db.session.commit()
    
    return jsonify({
        'id': announcement.id,
        'title': announcement.title,
        'content': announcement.content,
        'sender_id': announcement.sender_id,
        'target_role': announcement.target_role,
        'target_class_id': announcement.target_class_id,
        'created_at': announcement.created_at.isoformat(),
        'event_date': announcement.event_date.isoformat() if announcement.event_date else None,
        'announcement_type': announcement.announcement_type,
        'is_important': announcement.is_important
    }), 201

@announcements_bp.route('/<int:announcement_id>', methods=['PUT'])
@jwt_required()
def update_announcement(announcement_id):
    if not is_school_or_teacher():
        return jsonify({'message': 'Unauthorized'}), 403
    
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'message': 'Announcement not found'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        announcement.title = data['title']
    if 'content' in data:
        announcement.content = data['content']
    if 'target_role' in data:
        announcement.target_role = data['target_role']
    if 'target_class_id' in data:
        announcement.target_class_id = data['target_class_id']
    if 'event_date' in data:
        announcement.event_date = datetime.fromisoformat(data['event_date'])
    if 'announcement_type' in data:
        announcement.announcement_type = data['announcement_type']
    if 'is_important' in data:
        announcement.is_important = data['is_important']
    
    db.session.commit()
    
    return jsonify({
        'id': announcement.id,
        'title': announcement.title,
        'content': announcement.content,
        'sender_id': announcement.sender_id,
        'target_role': announcement.target_role,
        'target_class_id': announcement.target_class_id,
        'created_at': announcement.created_at.isoformat(),
        'event_date': announcement.event_date.isoformat() if announcement.event_date else None,
        'announcement_type': announcement.announcement_type,
        'is_important': announcement.is_important
    }), 200

@announcements_bp.route('/<int:announcement_id>', methods=['DELETE'])
@jwt_required()
def delete_announcement(announcement_id):
    if not is_school_or_teacher():
        return jsonify({'message': 'Unauthorized'}), 403
    
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'message': 'Announcement not found'}), 404
    
    db.session.delete(announcement)
    db.session.commit()
    
    return jsonify({'message': 'Announcement deleted successfully'}), 200 