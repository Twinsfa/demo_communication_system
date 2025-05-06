from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Grade, User, Class
from app import db
from datetime import datetime

grades_bp = Blueprint('grades', __name__)

def is_school_or_teacher():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.role in ['school', 'teacher']

@grades_bp.route('/', methods=['GET'])
@jwt_required()
def get_grades():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Get query parameters
    student_id = request.args.get('student_id')
    subject = request.args.get('subject')
    semester = request.args.get('semester')
    school_year = request.args.get('school_year')
    class_id = request.args.get('class_id')
    
    # Base query
    query = Grade.query
    
    # Filter based on user role
    if user.role == 'student':
        query = query.filter_by(student_id=user_id)
    elif user.role == 'parent':
        # Parents can see grades of their children
        query = query.join(User, Grade.student_id == User.id).filter(User.parent_id == user_id)
    elif user.role == 'teacher':
        # Teachers can see grades of their students
        query = query.join(User, Grade.student_id == User.id).filter(User.class_id == user.class_id)
    elif user.role == 'school':
        # School can see all grades
        pass
    else:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Apply additional filters
    if student_id:
        query = query.filter_by(student_id=student_id)
    if subject:
        query = query.filter_by(subject=subject)
    if semester:
        query = query.filter_by(semester=semester)
    if school_year:
        query = query.filter_by(school_year=school_year)
    if class_id:
        query = query.join(User, Grade.student_id == User.id).filter(User.class_id == class_id)
    
    grades = query.all()
    
    return jsonify([{
        'id': grade.id,
        'student_id': grade.student_id,
        'student_name': User.query.get(grade.student_id).full_name,
        'subject': grade.subject,
        'grade': grade.grade,
        'semester': grade.semester,
        'school_year': grade.school_year,
        'teacher_id': grade.teacher_id,
        'teacher_name': User.query.get(grade.teacher_id).full_name,
        'created_at': grade.created_at.isoformat(),
        'updated_at': grade.updated_at.isoformat(),
        'comments': grade.comments
    } for grade in grades]), 200

@grades_bp.route('/', methods=['POST'])
@jwt_required()
def create_grade():
    if not is_school_or_teacher():
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    user_id = get_jwt_identity()
    
    # Validate student exists
    student = User.query.get(data['student_id'])
    if not student or student.role != 'student':
        return jsonify({'message': 'Invalid student'}), 400
    
    grade = Grade(
        student_id=data['student_id'],
        subject=data['subject'],
        grade=data['grade'],
        semester=data['semester'],
        school_year=data['school_year'],
        teacher_id=user_id,
        comments=data.get('comments')
    )
    
    db.session.add(grade)
    db.session.commit()
    
    return jsonify({
        'id': grade.id,
        'student_id': grade.student_id,
        'subject': grade.subject,
        'grade': grade.grade,
        'semester': grade.semester,
        'school_year': grade.school_year,
        'teacher_id': grade.teacher_id,
        'created_at': grade.created_at.isoformat(),
        'comments': grade.comments
    }), 201

@grades_bp.route('/<int:grade_id>', methods=['PUT'])
@jwt_required()
def update_grade(grade_id):
    if not is_school_or_teacher():
        return jsonify({'message': 'Unauthorized'}), 403
    
    grade = Grade.query.get(grade_id)
    if not grade:
        return jsonify({'message': 'Grade not found'}), 404
    
    data = request.get_json()
    
    if 'grade' in data:
        grade.grade = data['grade']
    if 'comments' in data:
        grade.comments = data['comments']
    
    grade.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': grade.id,
        'student_id': grade.student_id,
        'subject': grade.subject,
        'grade': grade.grade,
        'semester': grade.semester,
        'school_year': grade.school_year,
        'teacher_id': grade.teacher_id,
        'updated_at': grade.updated_at.isoformat(),
        'comments': grade.comments
    }), 200

@grades_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_grade_statistics():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role not in ['school', 'teacher']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    class_id = request.args.get('class_id')
    subject = request.args.get('subject')
    semester = request.args.get('semester')
    school_year = request.args.get('school_year')
    
    # Base query
    query = Grade.query
    
    # Apply filters
    if class_id:
        query = query.join(User, Grade.student_id == User.id).filter(User.class_id == class_id)
    if subject:
        query = query.filter_by(subject=subject)
    if semester:
        query = query.filter_by(semester=semester)
    if school_year:
        query = query.filter_by(school_year=school_year)
    
    grades = query.all()
    
    if not grades:
        return jsonify({
            'average': 0,
            'highest': 0,
            'lowest': 0,
            'count': 0
        }), 200
    
    grade_values = [grade.grade for grade in grades]
    
    return jsonify({
        'average': sum(grade_values) / len(grade_values),
        'highest': max(grade_values),
        'lowest': min(grade_values),
        'count': len(grade_values)
    }), 200 