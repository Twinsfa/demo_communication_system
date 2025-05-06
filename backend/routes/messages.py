from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Message, User
from app import db

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/', methods=['GET'])
@jwt_required()
def get_messages():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Get query parameters
    conversation_with = request.args.get('with')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Base query for messages
    query = Message.query.filter(
        ((Message.sender_id == user_id) | (Message.receiver_id == user_id))
    )
    
    # Filter by conversation if specified
    if conversation_with:
        query = query.filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == conversation_with)) |
            ((Message.sender_id == conversation_with) & (Message.receiver_id == user_id))
        )
    
    # Order by creation date and paginate
    messages = query.order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
    
    return jsonify([{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'content': msg.content,
        'created_at': msg.created_at.isoformat(),
        'is_read': msg.is_read,
        'message_type': msg.message_type
    } for msg in messages]), 200

@messages_bp.route('/', methods=['POST'])
@jwt_required()
def send_message():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate receiver exists
    receiver = User.query.get(data['receiver_id'])
    if not receiver:
        return jsonify({'message': 'Receiver not found'}), 404
    
    message = Message(
        sender_id=user_id,
        receiver_id=data['receiver_id'],
        content=data['content'],
        message_type=data.get('message_type', 'text')
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'sender_id': message.sender_id,
        'receiver_id': message.receiver_id,
        'content': message.content,
        'created_at': message.created_at.isoformat(),
        'is_read': message.is_read,
        'message_type': message.message_type
    }), 201

@messages_bp.route('/<int:message_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(message_id):
    user_id = get_jwt_identity()
    message = Message.query.get(message_id)
    
    if not message:
        return jsonify({'message': 'Message not found'}), 404
    
    if message.receiver_id != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    message.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Message marked as read'}), 200

@messages_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    user_id = get_jwt_identity()
    
    # Get all unique users that the current user has conversations with
    conversations = db.session.query(
        User.id,
        User.username,
        User.full_name,
        User.role
    ).join(
        Message,
        ((Message.sender_id == User.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == User.id))
    ).distinct().all()
    
    return jsonify([{
        'user_id': conv.id,
        'username': conv.username,
        'full_name': conv.full_name,
        'role': conv.role
    } for conv in conversations]), 200 