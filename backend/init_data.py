import datetime
from app import create_app, db
from models import User, Role, UserRole, Department, Teacher, Parent, Student
from werkzeug.security import generate_password_hash

def init_demo_data():
    app = create_app()
    with app.app_context():
        # Create roles
        roles = {}
        for name, perm in [
            ('school', 'all'),
            ('department', 'department'),
            ('teacher', 'teacher'),
            ('parent', 'parent'),
            ('student', 'student')
        ]:
            role = Role(name=name, permission=perm)
            db.session.add(role)
            roles[name] = role
        db.session.commit()

        # Create demo users and link them properly
        # 1. School Admin
        admin_user = User(username='admin', email='admin@school.com', status='active')
        admin_user.password_hash = generate_password_hash('admin123')
        db.session.add(admin_user)
        db.session.flush()
        db.session.add(UserRole(user_id=admin_user.id, role_id=roles['school'].id))

        # 2. Department
        dept_user = User(username='department', email='department@school.com', status='active')
        dept_user.password_hash = generate_password_hash('dept123')
        db.session.add(dept_user)
        db.session.flush()
        db.session.add(UserRole(user_id=dept_user.id, role_id=roles['department'].id))
        department = Department(name='Academic Department', email='department@school.com', phone='1234567890', user_id=dept_user.id)
        db.session.add(department)

        # 3. Teacher
        teacher_user = User(username='teacher', email='teacher@school.com', status='active')
        teacher_user.password_hash = generate_password_hash('teacher123')
        db.session.add(teacher_user)
        db.session.flush()
        db.session.add(UserRole(user_id=teacher_user.id, role_id=roles['teacher'].id))
        teacher = Teacher(full_name='Demo Teacher', email='teacher@school.com', type='subject_teacher', user_id=teacher_user.id)
        db.session.add(teacher)

        # 4. Parent
        parent_user = User(username='parent', email='parent@school.com', status='active')
        parent_user.password_hash = generate_password_hash('parent123')
        db.session.add(parent_user)
        db.session.flush()
        db.session.add(UserRole(user_id=parent_user.id, role_id=roles['parent'].id))
        parent = Parent(full_name='Demo Parent', email='parent@school.com', phone='1234567890', address='123 School St', user_id=parent_user.id)
        db.session.add(parent)
        db.session.flush()

        # 5. Student (linked to parent)
        student_user = User(username='student', email='student@school.com', status='active')
        student_user.password_hash = generate_password_hash('student123')
        db.session.add(student_user)
        db.session.flush()
        db.session.add(UserRole(user_id=student_user.id, role_id=roles['student'].id))
        student = Student(full_name='Demo Student', date_of_birth=datetime.date(2000, 1, 1), gender='male', parent_id=parent.id, user_id=student_user.id)
        db.session.add(student)

        try:
            db.session.commit()
            print("✅ Demo data has been initialized successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error initializing demo data: {str(e)}")

if __name__ == '__main__':
    init_demo_data() 