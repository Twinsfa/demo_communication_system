from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Evaluation, TeacherEvaluation, User, Student, Teacher, Class, Subject, UserRole, Role
from app import db
from datetime import datetime

evaluations_bp = Blueprint('evaluations', __name__)

def get_user_roles(user_id):
    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    return Role.query.filter(Role.id.in_(role_ids)).all()

@evaluations_bp.route('/', methods=['POST'])
@jwt_required()
def create_evaluation():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user is teacher
    roles = get_user_roles(user_id)
    if not any(role.name == 'teacher' for role in roles):
        return jsonify({'message': 'Only teachers can create evaluations'}), 403
    
    # Validate required fields
    if not all(k in data for k in ['content', 'student_id']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Validate student exists
    student = Student.query.get(data['student_id'])
    if not student:
        return jsonify({'message': 'Student not found'}), 404
    
    # Get teacher
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return jsonify({'message': 'Teacher profile not found'}), 404
    
    # Create evaluation
    evaluation = Evaluation(
        content=data['content'],
        student_id=student.id
    )
    db.session.add(evaluation)
    db.session.flush()
    
    # Add teacher evaluation
    teacher_eval = TeacherEvaluation(
        evaluation_id=evaluation.id,
        teacher_id=teacher.id
    )
    db.session.add(teacher_eval)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Evaluation created successfully',
            'evaluation_id': evaluation.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error creating evaluation'}), 500

@evaluations_bp.route('/', methods=['GET'])
@jwt_required()
def get_evaluations():
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    # Base query
    query = Evaluation.query
    
    # Filter based on user role
    if any(role.name == 'student' for role in roles):
        # Students can only see their own evaluations
        student = Student.query.filter_by(user_id=user_id).first()
        if student:
            query = query.filter_by(student_id=student.id)
    elif any(role.name == 'parent' for role in roles):
        # Parents can see evaluations of their children
        parent = User.query.get(user_id).parent
        if parent:
            student_ids = [student.id for student in parent.students]
            query = query.filter(Evaluation.student_id.in_(student_ids))
    elif any(role.name == 'teacher' for role in roles):
        # Teachers can see evaluations of their students
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        if teacher:
            if teacher.type == 'homeroom_teacher':
                # Homeroom teachers can see evaluations of their class students
                class_students = Student.query.join(Student.classes).filter(
                    Class.teacher_id == teacher.id
                ).all()
                student_ids = [student.id for student in class_students]
                query = query.filter(Evaluation.student_id.in_(student_ids))
            else:
                # Subject teachers can see evaluations of students in their subjects
                subject_students = Student.query.join(Student.subjects).filter(
                    Subject.teacher_id == teacher.id
                ).all()
                student_ids = [student.id for student in subject_students]
                query = query.filter(Evaluation.student_id.in_(student_ids))
    
    # Apply filters
    student_id = request.args.get('student_id')
    teacher_id = request.args.get('teacher_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if student_id:
        query = query.filter_by(student_id=student_id)
    if teacher_id:
        query = query.join(TeacherEvaluation).filter(TeacherEvaluation.teacher_id == teacher_id)
    if start_date:
        query = query.filter(Evaluation.evaluation_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Evaluation.evaluation_date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    evaluations = query.order_by(Evaluation.evaluation_date.desc()).all()
    
    return jsonify([{
        'id': eval.id,
        'content': eval.content,
        'evaluation_date': eval.evaluation_date.isoformat(),
        'student': {
            'id': eval.student.id,
            'full_name': eval.student.full_name
        },
        'teachers': [{
            'id': te.teacher.id,
            'full_name': te.teacher.full_name,
            'type': te.teacher.type
        } for te in eval.teachers]
    } for eval in evaluations]), 200

@evaluations_bp.route('/<int:evaluation_id>', methods=['GET'])
@jwt_required()
def get_evaluation(evaluation_id):
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    evaluation = Evaluation.query.get(evaluation_id)
    if not evaluation:
        return jsonify({'message': 'Evaluation not found'}), 404
    
    # Check permissions
    if any(role.name == 'student' for role in roles):
        student = Student.query.filter_by(user_id=user_id).first()
        if not student or evaluation.student_id != student.id:
            return jsonify({'message': 'Unauthorized'}), 403
    elif any(role.name == 'parent' for role in roles):
        parent = User.query.get(user_id).parent
        if not parent or evaluation.student_id not in [student.id for student in parent.students]:
            return jsonify({'message': 'Unauthorized'}), 403
    elif any(role.name == 'teacher' for role in roles):
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        if teacher:
            if teacher.type == 'homeroom_teacher':
                class_students = Student.query.join(Student.classes).filter(
                    Class.teacher_id == teacher.id
                ).all()
                if evaluation.student_id not in [student.id for student in class_students]:
                    return jsonify({'message': 'Unauthorized'}), 403
            else:
                subject_students = Student.query.join(Student.subjects).filter(
                    Subject.teacher_id == teacher.id
                ).all()
                if evaluation.student_id not in [student.id for student in subject_students]:
                    return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify({
        'id': evaluation.id,
        'content': evaluation.content,
        'evaluation_date': evaluation.evaluation_date.isoformat(),
        'student': {
            'id': evaluation.student.id,
            'full_name': evaluation.student.full_name
        },
        'teachers': [{
            'id': te.teacher.id,
            'full_name': te.teacher.full_name,
            'type': te.teacher.type
        } for te in evaluation.teachers]
    }), 200

@evaluations_bp.route('/<int:evaluation_id>', methods=['PUT'])
@jwt_required()
def update_evaluation(evaluation_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user is teacher
    roles = get_user_roles(user_id)
    if not any(role.name == 'teacher' for role in roles):
        return jsonify({'message': 'Only teachers can update evaluations'}), 403
    
    evaluation = Evaluation.query.get(evaluation_id)
    if not evaluation:
        return jsonify({'message': 'Evaluation not found'}), 404
    
    # Check if teacher is one of the evaluators
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return jsonify({'message': 'Teacher profile not found'}), 404
    
    teacher_eval = TeacherEvaluation.query.filter_by(
        evaluation_id=evaluation_id,
        teacher_id=teacher.id
    ).first()
    
    if not teacher_eval:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Update content
    if 'content' in data:
        evaluation.content = data['content']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Evaluation updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating evaluation'}), 500

@evaluations_bp.route('/<int:evaluation_id>', methods=['DELETE'])
@jwt_required()
def delete_evaluation(evaluation_id):
    user_id = get_jwt_identity()
    
    # Check if user is teacher
    roles = get_user_roles(user_id)
    if not any(role.name == 'teacher' for role in roles):
        return jsonify({'message': 'Only teachers can delete evaluations'}), 403
    
    evaluation = Evaluation.query.get(evaluation_id)
    if not evaluation:
        return jsonify({'message': 'Evaluation not found'}), 404
    
    # Check if teacher is one of the evaluators
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return jsonify({'message': 'Teacher profile not found'}), 404
    
    teacher_eval = TeacherEvaluation.query.filter_by(
        evaluation_id=evaluation_id,
        teacher_id=teacher.id
    ).first()
    
    if not teacher_eval:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Delete teacher evaluation and the main evaluation
    db.session.delete(teacher_eval)
    db.session.delete(evaluation)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Evaluation deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error deleting evaluation'}), 500 