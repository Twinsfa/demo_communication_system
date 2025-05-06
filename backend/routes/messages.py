from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Conversation, Message, ConversationUser, User, Teacher, Parent, Student, Class, UserRole, Role
from app import db
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

def get_user_roles(user_id):
    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    return Role.query.filter(Role.id.in_(role_ids)).all()

@messages_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    user_id = get_jwt_identity()
    
    # Get all conversations where user is a participant
    conversations = Conversation.query.join(ConversationUser).filter(
        ConversationUser.user_id == user_id
    ).order_by(Conversation.created_at.desc()).all()
    
    return jsonify([{
        'id': conv.id,
        'title': conv.title,
        'type': conv.type,
        'created_at': conv.created_at.isoformat(),
        'participants': [{
            'user_id': cu.user_id,
            'username': User.query.get(cu.user_id).username
        } for cu in conv.participants],
        'last_message': Message.query.filter_by(conversation_id=conv.id)
            .order_by(Message.sent_at.desc()).first().content if conv.messages else None
    } for conv in conversations]), 200

@messages_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not all(k in data for k in ['type', 'participants']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Validate conversation type
    if data['type'] not in ['private', 'group']:
        return jsonify({'message': 'Invalid conversation type'}), 400
    
    # For private conversations, ensure exactly 2 participants
    if data['type'] == 'private' and len(data['participants']) != 2:
        return jsonify({'message': 'Private conversations must have exactly 2 participants'}), 400
    
    # Create conversation
    conversation = Conversation(
        title=data.get('title', 'New Conversation'),
        type=data['type']
    )
    db.session.add(conversation)
    db.session.flush()
    
    # Add participants
    for participant_id in data['participants']:
        # Verify participant exists
        participant = User.query.get(participant_id)
        if not participant:
            return jsonify({'message': f'User {participant_id} not found'}), 404
        
        # Add participant to conversation
        conv_user = ConversationUser(
            conversation_id=conversation.id,
            user_id=participant_id
        )
        db.session.add(conv_user)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Conversation created successfully',
            'conversation_id': conversation.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error creating conversation'}), 500

@messages_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conversation_id):
    user_id = get_jwt_identity()
    
    # Verify user is part of the conversation
    conv_user = ConversationUser.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first()
    
    if not conv_user:
        return jsonify({'message': 'Conversation not found'}), 404
    
    # Get messages
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.sent_at.asc()).all()
    
    return jsonify([{
        'id': msg.id,
        'sender_role': msg.sender_role,
        'content': msg.content,
        'sent_at': msg.sent_at.isoformat()
    } for msg in messages]), 200

@messages_bp.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conversation_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Verify user is part of the conversation
    conv_user = ConversationUser.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first()
    
    if not conv_user:
        return jsonify({'message': 'Conversation not found'}), 404
    
    if 'content' not in data:
        return jsonify({'message': 'Message content is required'}), 400
    
    # Determine sender role
    roles = get_user_roles(user_id)
    sender_role = None
    if any(role.name == 'teacher' for role in roles):
        sender_role = 'teacher'
    elif any(role.name == 'parent' for role in roles):
        sender_role = 'parent'
    
    if not sender_role:
        return jsonify({'message': 'User must be either teacher or parent'}), 403
    
    # Create message
    message = Message(
        sender_role=sender_role,
        content=data['content'],
        conversation_id=conversation_id
    )
    db.session.add(message)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Message sent successfully',
            'message_id': message.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error sending message'}), 500

@messages_bp.route('/conversations/<int:conversation_id>/participants', methods=['POST'])
@jwt_required()
def add_participant(conversation_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if 'participant_id' not in data:
        return jsonify({'message': 'Participant ID is required'}), 400
    
    # Verify user is part of the conversation
    conv_user = ConversationUser.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first()
    
    if not conv_user:
        return jsonify({'message': 'Conversation not found'}), 404
    
    # Get conversation
    conversation = Conversation.query.get(conversation_id)
    if conversation.type != 'group':
        return jsonify({'message': 'Can only add participants to group conversations'}), 400
    
    # Verify new participant exists
    new_participant = User.query.get(data['participant_id'])
    if not new_participant:
        return jsonify({'message': 'User not found'}), 404
    
    # Add participant
    new_conv_user = ConversationUser(
        conversation_id=conversation_id,
        user_id=data['participant_id']
    )
    db.session.add(new_conv_user)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Participant added successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error adding participant'}), 500

@messages_bp.route('/conversations/<int:conversation_id>/participants/<int:participant_id>', methods=['DELETE'])
@jwt_required()
def remove_participant(conversation_id, participant_id):
    user_id = get_jwt_identity()
    
    # Verify user is part of the conversation
    conv_user = ConversationUser.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first()
    
    if not conv_user:
        return jsonify({'message': 'Conversation not found'}), 404
    
    # Get conversation
    conversation = Conversation.query.get(conversation_id)
    if conversation.type != 'group':
        return jsonify({'message': 'Can only remove participants from group conversations'}), 400
    
    # Remove participant
    participant = ConversationUser.query.filter_by(
        conversation_id=conversation_id,
        user_id=participant_id
    ).first()
    
    if not participant:
        return jsonify({'message': 'Participant not found in conversation'}), 404
    
    db.session.delete(participant)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Participant removed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error removing participant'}), 500 