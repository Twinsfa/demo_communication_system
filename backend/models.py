from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # school, teacher, parent, student
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    class_ = db.relationship('Class', backref='students')
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    children = db.relationship('User', backref=db.backref('parent', remote_side=[id]))
    
    # Messages
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver')
    
    # Forms
    sent_forms = db.relationship('Form', foreign_keys='Form.sender_id', backref='sender')
    received_forms = db.relationship('Form', foreign_keys='Form.receiver_id', backref='receiver')
    
    # Grades
    grades = db.relationship('Grade', backref='student')
    
    # Rewards
    rewards = db.relationship('Reward', backref='student')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    grade_level = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    teacher = db.relationship('User', backref='managed_classes')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    message_type = db.Column(db.String(20), default='text')  # text, file, image

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.relationship('User', backref='announcements')
    target_role = db.Column(db.String(20), nullable=False)  # all, teachers, parents, students
    target_class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    target_class = db.relationship('Class', backref='announcements')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    event_date = db.Column(db.DateTime)
    announcement_type = db.Column(db.String(50))  # schedule, exam, event, etc.
    is_important = db.Column(db.Boolean, default=False)

class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    form_type = db.Column(db.String(50))  # leave_request, suggestion, support_request, activity_registration
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    response = db.Column(db.Text)
    response_date = db.Column(db.DateTime)
    attachments = db.Column(db.String(500))  # Store file paths

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.Float, nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    school_year = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher = db.relationship('User', backref='given_grades')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comments = db.Column(db.Text)

class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # reward or discipline
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher = db.relationship('User', backref='given_rewards')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    points = db.Column(db.Integer)  # For numerical tracking of rewards/discipline
    category = db.Column(db.String(50))  # academic, behavior, sports, etc. 