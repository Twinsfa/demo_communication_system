from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Notification, NotificationUser, User, Department, Teacher, Class, Student, UserRole, Role
from app import db
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

def get_user_roles(user_id):
    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    return Role.query.filter(Role.id.in_(role_ids)).all()

@notifications_bp.route('/', methods=['POST'])
@jwt_required()
def create_notification():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user is department or teacher
    roles = get_user_roles(user_id)
    is_department = any(role.name == 'department' for role in roles)
    is_teacher = any(role.name == 'teacher' for role in roles)
    
    if not (is_department or is_teacher):
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Validate required fields
    if not all(k in data for k in ['title', 'content', 'type']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Create notification
    notification = Notification(
        title=data['title'],
        content=data['content'],
        type=data['type'],
        sender_id=user_id
    )
    db.session.add(notification)
    db.session.flush()
    
    # Handle recipients based on notification type
    if data['type'] == 'all':
        # Send to all users
        users = User.query.all()
        for user in users:
            notification_user = NotificationUser(
                user_id=user.id,
                notification_id=notification.id
            )
            db.session.add(notification_user)
    
    elif data['type'] == 'teachers':
        # Send to all teachers
        teachers = Teacher.query.all()
        for teacher in teachers:
            notification_user = NotificationUser(
                user_id=teacher.user_id,
                notification_id=notification.id
            )
            db.session.add(notification_user)
    
    elif data['type'] == 'parents':
        # Send to all parents
        parents = User.query.join(UserRole).join(Role).filter(Role.name == 'parent').all()
        for parent in parents:
            notification_user = NotificationUser(
                user_id=parent.id,
                notification_id=notification.id
            )
            db.session.add(notification_user)
    
    elif data['type'] == 'specific_class':
        # Send to specific class (students and their parents)
        if 'class_id' not in data:
            return jsonify({'message': 'Class ID required for specific class notification'}), 400
        
        class_obj = Class.query.get(data['class_id'])
        if not class_obj:
            return jsonify({'message': 'Class not found'}), 404
        
        # Get students in the class
        students = Student.query.join(Student.classes).filter(Class.id == data['class_id']).all()
        
        # Add notification for students and their parents
        for student in students:
            # Add for student
            notification_user = NotificationUser(
                user_id=student.user_id,
                notification_id=notification.id
            )
            db.session.add(notification_user)
            
            # Add for parent
            if student.parent:
                notification_user = NotificationUser(
                    user_id=student.parent.user_id,
                    notification_id=notification.id
                )
                db.session.add(notification_user)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Notification created successfully',
            'notification_id': notification.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error creating notification'}), 500

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    
    # Get all notifications for the user
    notifications = Notification.query.join(NotificationUser).filter(
        NotificationUser.user_id == user_id
    ).order_by(Notification.created_time.desc()).all()
    
    return jsonify([{
        'id': notification.id,
        'title': notification.title,
        'content': notification.content,
        'type': notification.type,
        'created_time': notification.created_time.isoformat(),
        'status': notification.status,
        'is_read': NotificationUser.query.filter_by(
            user_id=user_id,
            notification_id=notification.id
        ).first().is_read
    } for notification in notifications]), 200

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_as_read(notification_id):
    user_id = get_jwt_identity()
    
    notification_user = NotificationUser.query.filter_by(
        user_id=user_id,
        notification_id=notification_id
    ).first()
    
    if not notification_user:
        return jsonify({'message': 'Notification not found'}), 404
    
    notification_user.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Notification marked as read'}), 200

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    user_id = get_jwt_identity()
    
    # Check if user is department or teacher
    roles = get_user_roles(user_id)
    is_department = any(role.name == 'department' for role in roles)
    is_teacher = any(role.name == 'teacher' for role in roles)
    
    if not (is_department or is_teacher):
        return jsonify({'message': 'Unauthorized'}), 403
    
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'message': 'Notification not found'}), 404
    
    # Check if user is the sender
    if notification.sender_id != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Delete notification and its recipients
    NotificationUser.query.filter_by(notification_id=notification_id).delete()
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted successfully'}), 200 