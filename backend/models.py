from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # school, department, teacher, parent, student
    permission = db.Column(db.String(200))
    users = db.relationship('UserRole', backref='role', lazy=True)

class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True)
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    roles = db.relationship('UserRole', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='department')
    notifications = db.relationship('Notification', backref='department', lazy=True)
    request_forms = db.relationship('RequestForm', backref='department', lazy=True)
    rewards_disciplines = db.relationship('RewardAndDiscipline', backref='department', lazy=True)

class Parent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='parent')
    students = db.relationship('Student', backref='parent', lazy=True)
    request_forms = db.relationship('RequestForm', backref='parent', lazy=True)
    conversations = db.relationship('ConversationUser', backref='parent', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.String(200))
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='student')
    scores = db.relationship('Score', backref='student', lazy=True)
    rewards_disciplines = db.relationship('RewardAndDiscipline', backref='student', lazy=True)
    evaluations = db.relationship('Evaluation', backref='student', lazy=True)
    classes = db.relationship('StudentClass', backref='student', lazy=True)
    subjects = db.relationship('StudentSubject', backref='student', lazy=True)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    number_no = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    type = db.Column(db.String(50))  # homeroom_teacher, subject_teacher
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='teacher')
    subjects = db.relationship('Subject', backref='teacher', lazy=True)
    classes = db.relationship('Class', backref='teacher', lazy=True)
    scores = db.relationship('Score', backref='teacher', lazy=True)
    evaluations = db.relationship('TeacherEvaluation', backref='teacher', lazy=True)
    conversations = db.relationship('ConversationUser', backref='teacher', lazy=True)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20))
    academic_year = db.Column(db.String(20))
    student_count = db.Column(db.Integer, default=0)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    students = db.relationship('StudentClass', backref='class', lazy=True)
    notifications = db.relationship('Notification', backref='class', lazy=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    students = db.relationship('StudentSubject', backref='subject', lazy=True)
    scores = db.relationship('Score', backref='subject', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float, nullable=False)
    exam_type = db.Column(db.String(50))  # midterm, final, quiz, etc.
    exam_date = db.Column(db.Date)
    comments = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RequestForm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # leave_request, extra_class_request, etc.
    content = db.Column(db.Text, nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed
    response = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RewardAndDiscipline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # reward, discipline
    date = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer)  # For rewards: positive points, for discipline: negative points
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, archived
    type = db.Column(db.String(50))  # all, teachers, parents, students, specific_class
    sender_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    recipients = db.relationship('NotificationUser', backref='notification', lazy=True)

class NotificationUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)

class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evaluation_date = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teachers = db.relationship('TeacherEvaluation', backref='evaluation', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TeacherEvaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    type = db.Column(db.String(20), nullable=False)  # private, group
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True)
    participants = db.relationship('ConversationUser', backref='conversation', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_role = db.Column(db.String(20), nullable=False)  # teacher, parent
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)

class ConversationUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_read_at = db.Column(db.DateTime)

class StudentClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow) 