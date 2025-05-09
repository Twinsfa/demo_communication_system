from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import RewardAndDiscipline, User, Student, Department, UserRole, Role, Class
from app import db
from datetime import datetime
from sqlalchemy import func
from collections import defaultdict

rewards_bp = Blueprint('rewards', __name__)

# Định nghĩa các loại nội dung cho khen thưởng và kỷ luật
CONTENT_TYPES = {
    'reward': ['achievement', 'excellence', 'improvement', 'other'],
    'discipline': ['violation', 'misconduct', 'attendance', 'other']
}

def init_rewards_table():
    """Khởi tạo bảng reward_and_discipline với trường content_type"""
    try:
        # Thêm cột content_type nếu chưa tồn tại
        with db.engine.connect() as conn:
            conn.execute("""
                ALTER TABLE reward_and_discipline 
                ADD COLUMN IF NOT EXISTS content_type VARCHAR(50)
            """)
            
            # Cập nhật dữ liệu hiện có
            conn.execute("""
                UPDATE reward_and_discipline 
                SET content_type = CASE 
                    WHEN type = 'reward' THEN 'achievement'
                    WHEN type = 'discipline' THEN 'violation'
                    ELSE 'other'
                END
                WHERE content_type IS NULL
            """)
            
            # Đặt cột không được null
            conn.execute("""
                ALTER TABLE reward_and_discipline 
                ALTER COLUMN content_type SET NOT NULL
            """)
            
        return True
    except Exception as e:
        print(f"Error initializing rewards table: {str(e)}")
        return False

# Gọi hàm khởi tạo khi module được import
init_rewards_table()

def get_user_roles(user_id):
    """Lấy danh sách vai trò của người dùng"""
    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    role_ids = [ur.role_id for ur in user_roles]
    return Role.query.filter(Role.id.in_(role_ids)).all()

@rewards_bp.route('/', methods=['POST'])
@jwt_required()
def create_reward_discipline():
    """
    Tạo bản ghi khen thưởng/kỷ luật mới
    Chỉ phòng ban mới có quyền tạo
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Kiểm tra quyền phòng ban
    roles = get_user_roles(user_id)
    if not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Chỉ phòng ban mới có quyền tạo bản ghi'}), 403
    
    # Kiểm tra các trường bắt buộc
    if not all(k in data for k in ['type', 'content', 'date', 'student_id', 'content_type']):
        return jsonify({'message': 'Thiếu thông tin bắt buộc'}), 400
    
    # Kiểm tra loại bản ghi
    if data['type'] not in ['reward', 'discipline']:
        return jsonify({'message': 'Loại bản ghi không hợp lệ'}), 400
    
    # Kiểm tra loại nội dung
    if data['content_type'] not in CONTENT_TYPES[data['type']]:
        return jsonify({'message': 'Loại nội dung không hợp lệ'}), 400
    
    # Kiểm tra học sinh tồn tại
    student = Student.query.get(data['student_id'])
    if not student:
        return jsonify({'message': 'Không tìm thấy học sinh'}), 404
    
    # Lấy thông tin phòng ban
    department = Department.query.filter_by(user_id=user_id).first()
    if not department:
        return jsonify({'message': 'Không tìm thấy thông tin phòng ban'}), 404
    
    # Tạo bản ghi mới
    record = RewardAndDiscipline(
        type=data['type'],
        content_type=data['content_type'],
        content=data['content'],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        student_id=student.id,
        department_id=department.id
    )
    
    db.session.add(record)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Tạo bản ghi thành công',
            'record_id': record.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Lỗi khi tạo bản ghi'}), 500

@rewards_bp.route('/', methods=['GET'])
@jwt_required()
def get_rewards_discipline():
    """
    Lấy danh sách bản ghi khen thưởng/kỷ luật
    Phân quyền theo vai trò:
    - Học sinh: chỉ xem của mình
    - Phụ huynh: xem của con
    - Giáo viên: xem của học sinh trong lớp
    - Phòng ban: xem tất cả
    """
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    # Query cơ bản
    query = RewardAndDiscipline.query
    
    # Lọc theo vai trò
    if any(role.name == 'student' for role in roles):
        # Học sinh chỉ xem được của mình
        student = Student.query.filter_by(user_id=user_id).first()
        if student:
            query = query.filter_by(student_id=student.id)
    elif any(role.name == 'parent' for role in roles):
        # Phụ huynh xem được của con
        parent = User.query.get(user_id).parent
        if parent:
            student_ids = [student.id for student in parent.students]
            query = query.filter(RewardAndDiscipline.student_id.in_(student_ids))
    elif any(role.name == 'teacher' for role in roles):
        # Giáo viên xem được của học sinh trong lớp
        teacher = User.query.get(user_id).teacher
        if teacher and teacher.class_id:
            student_ids = [s.id for s in Student.query.filter_by(class_id=teacher.class_id).all()]
            query = query.filter(RewardAndDiscipline.student_id.in_(student_ids))
    elif not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Không có quyền truy cập'}), 403
    
    # Áp dụng bộ lọc
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

@rewards_bp.route('/statistics/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_statistics(student_id):
    """
    Lấy thống kê khen thưởng/kỷ luật của một học sinh
    Bao gồm:
    - Tổng số khen thưởng/kỷ luật
    - Phân loại theo loại
    - Thống kê theo thời gian
    """
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    # Kiểm tra quyền truy cập
    if any(role.name == 'student' for role in roles):
        student = Student.query.filter_by(user_id=user_id).first()
        if not student or student.id != student_id:
            return jsonify({'message': 'Không có quyền truy cập'}), 403
    elif any(role.name == 'parent' for role in roles):
        parent = User.query.get(user_id).parent
        if not parent or student_id not in [s.id for s in parent.students]:
            return jsonify({'message': 'Không có quyền truy cập'}), 403
    elif any(role.name == 'teacher' for role in roles):
        teacher = User.query.get(user_id).teacher
        if not teacher or student_id not in [s.id for s in Student.query.filter_by(class_id=teacher.class_id).all()]:
            return jsonify({'message': 'Không có quyền truy cập'}), 403
    elif not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Không có quyền truy cập'}), 403

    # Lấy thống kê
    rewards = RewardAndDiscipline.query.filter_by(student_id=student_id, type='reward').all()
    discipline = RewardAndDiscipline.query.filter_by(student_id=student_id, type='discipline').all()

    # Thống kê theo loại
    reward_types = defaultdict(int)
    discipline_types = defaultdict(int)
    for r in rewards:
        reward_types[r.content_type] += 1
    for d in discipline:
        discipline_types[d.content_type] += 1

    # Thống kê theo thời gian
    time_series = defaultdict(lambda: {'rewards': 0, 'discipline': 0})
    for r in rewards:
        time_series[r.date.isoformat()]['rewards'] += 1
    for d in discipline:
        time_series[d.date.isoformat()]['discipline'] += 1

    return jsonify({
        'rewards': {
            'total': len(rewards),
            'by_type': dict(reward_types)
        },
        'discipline': {
            'total': len(discipline),
            'by_type': dict(discipline_types)
        },
        'time_series': {
            'labels': sorted(time_series.keys()),
            'rewards': [time_series[date]['rewards'] for date in sorted(time_series.keys())],
            'discipline': [time_series[date]['discipline'] for date in sorted(time_series.keys())]
        }
    }), 200

@rewards_bp.route('/statistics/class/<int:class_id>', methods=['GET'])
@jwt_required()
def get_class_statistics(class_id):
    """
    Lấy thống kê khen thưởng/kỷ luật của một lớp
    Bao gồm:
    - Tổng số khen thưởng/kỷ luật
    - Top học sinh được khen thưởng/bị kỷ luật
    - Thống kê theo thời gian
    """
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    # Kiểm tra quyền truy cập
    if any(role.name == 'teacher' for role in roles):
        teacher = User.query.get(user_id).teacher
        if not teacher or teacher.class_id != class_id:
            return jsonify({'message': 'Không có quyền truy cập'}), 403
    elif not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Không có quyền truy cập'}), 403

    # Lấy danh sách học sinh trong lớp
    students = Student.query.filter_by(class_id=class_id).all()
    student_ids = [s.id for s in students]

    # Lấy thống kê
    rewards = RewardAndDiscipline.query.filter(
        RewardAndDiscipline.student_id.in_(student_ids),
        RewardAndDiscipline.type == 'reward'
    ).all()
    
    discipline = RewardAndDiscipline.query.filter(
        RewardAndDiscipline.student_id.in_(student_ids),
        RewardAndDiscipline.type == 'discipline'
    ).all()

    # Thống kê theo học sinh
    student_rewards = defaultdict(int)
    student_discipline = defaultdict(int)
    for r in rewards:
        student_rewards[r.student_id] += 1
    for d in discipline:
        student_discipline[d.student_id] += 1

    # Top học sinh
    top_rewards = sorted(
        [{'student_id': sid, 'count': count} for sid, count in student_rewards.items()],
        key=lambda x: x['count'],
        reverse=True
    )[:5]
    
    top_discipline = sorted(
        [{'student_id': sid, 'count': count} for sid, count in student_discipline.items()],
        key=lambda x: x['count'],
        reverse=True
    )[:5]

    # Thêm thông tin học sinh
    for item in top_rewards:
        student = Student.query.get(item['student_id'])
        item['full_name'] = student.full_name if student else 'Unknown'
    
    for item in top_discipline:
        student = Student.query.get(item['student_id'])
        item['full_name'] = student.full_name if student else 'Unknown'

    return jsonify({
        'rewards': {
            'total': len(rewards),
            'top_students': top_rewards
        },
        'discipline': {
            'total': len(discipline),
            'top_students': top_discipline
        }
    }), 200

@rewards_bp.route('/statistics/school', methods=['GET'])
@jwt_required()
def get_school_statistics():
    """
    Lấy thống kê khen thưởng/kỷ luật toàn trường
    Chỉ phòng ban mới có quyền xem
    Bao gồm:
    - Tổng số khen thưởng/kỷ luật
    - Phân loại theo loại
    - Thống kê theo thời gian
    """
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    # Kiểm tra quyền phòng ban
    if not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Chỉ phòng ban mới có quyền xem thống kê toàn trường'}), 403

    # Lấy thống kê
    rewards = RewardAndDiscipline.query.filter_by(type='reward').all()
    discipline = RewardAndDiscipline.query.filter_by(type='discipline').all()

    # Thống kê theo loại
    reward_types = defaultdict(int)
    discipline_types = defaultdict(int)
    for r in rewards:
        reward_types[r.content_type] += 1
    for d in discipline:
        discipline_types[d.content_type] += 1

    # Thống kê theo thời gian
    time_series = defaultdict(lambda: {'rewards': 0, 'discipline': 0})
    for r in rewards:
        time_series[r.date.isoformat()]['rewards'] += 1
    for d in discipline:
        time_series[d.date.isoformat()]['discipline'] += 1

    return jsonify({
        'rewards': {
            'total': len(rewards),
            'by_type': dict(reward_types)
        },
        'discipline': {
            'total': len(discipline),
            'by_type': dict(discipline_types)
        },
        'time_series': {
            'labels': sorted(time_series.keys()),
            'rewards': [time_series[date]['rewards'] for date in sorted(time_series.keys())],
            'discipline': [time_series[date]['discipline'] for date in sorted(time_series.keys())]
        }
    }), 200

@rewards_bp.route('/<int:record_id>', methods=['GET'])
@jwt_required()
def get_record(record_id):
    """
    Lấy chi tiết một bản ghi khen thưởng/kỷ luật
    Phân quyền theo vai trò:
    - Học sinh: chỉ xem của mình
    - Phụ huynh: xem của con
    - Giáo viên: xem của học sinh trong lớp
    - Phòng ban: xem tất cả
    """
    user_id = get_jwt_identity()
    roles = get_user_roles(user_id)
    
    record = RewardAndDiscipline.query.get(record_id)
    if not record:
        return jsonify({'message': 'Không tìm thấy bản ghi'}), 404
    
    # Kiểm tra quyền truy cập
    if any(role.name == 'student' for role in roles):
        student = Student.query.filter_by(user_id=user_id).first()
        if not student or record.student_id != student.id:
            return jsonify({'message': 'Không có quyền truy cập'}), 403
    elif any(role.name == 'parent' for role in roles):
        parent = User.query.get(user_id).parent
        if not parent or record.student_id not in [s.id for s in parent.students]:
            return jsonify({'message': 'Không có quyền truy cập'}), 403
    elif any(role.name == 'teacher' for role in roles):
        teacher = User.query.get(user_id).teacher
        if not teacher or record.student_id not in [s.id for s in Student.query.filter_by(class_id=teacher.class_id).all()]:
            return jsonify({'message': 'Không có quyền truy cập'}), 403
    elif not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Không có quyền truy cập'}), 403
    
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
    """
    Cập nhật bản ghi khen thưởng/kỷ luật
    Chỉ phòng ban mới có quyền cập nhật
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Kiểm tra quyền phòng ban
    roles = get_user_roles(user_id)
    if not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Chỉ phòng ban mới có quyền cập nhật bản ghi'}), 403
    
    record = RewardAndDiscipline.query.get(record_id)
    if not record:
        return jsonify({'message': 'Không tìm thấy bản ghi'}), 404
    
    # Cập nhật các trường
    if 'content' in data:
        record.content = data['content']
    if 'date' in data:
        record.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    try:
        db.session.commit()
        return jsonify({'message': 'Cập nhật bản ghi thành công'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Lỗi khi cập nhật bản ghi'}), 500

@rewards_bp.route('/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_record(record_id):
    """
    Xóa bản ghi khen thưởng/kỷ luật
    Chỉ phòng ban mới có quyền xóa
    """
    user_id = get_jwt_identity()
    
    # Kiểm tra quyền phòng ban
    roles = get_user_roles(user_id)
    if not any(role.name == 'department' for role in roles):
        return jsonify({'message': 'Chỉ phòng ban mới có quyền xóa bản ghi'}), 403
    
    record = RewardAndDiscipline.query.get(record_id)
    if not record:
        return jsonify({'message': 'Không tìm thấy bản ghi'}), 404
    
    db.session.delete(record)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Xóa bản ghi thành công'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Lỗi khi xóa bản ghi'}), 500 