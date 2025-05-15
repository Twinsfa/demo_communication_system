# School Communication & Information System

## Overview
This project is a comprehensive School Communication and Information System designed to streamline communication and information management between school administrators, teachers, students, and parents. The system provides a unified platform for notifications, evaluations, messaging, request forms, and more, supporting both academic and administrative workflows.

## Main Features
- Notifications: Send and receive targeted notifications to/from departments, teachers, students, and parents. Flexible recipient selection by class, role, or individual.
- Evaluations & Reviews: Teachers can create and manage student evaluations and subject reviews. Students and parents can view detailed feedback, including subject-specific comments.
- Messaging: Secure, role-based direct messaging between teachers, departments, students, and parents. Department users can only message teachers and other departments.
- Request Forms: Parents can submit various requests (leave, grade appeal, etc.) linked to their children. Automatic routing to homeroom teachers and relevant departments.
- Reward & Discipline Management: Track and notify about student rewards and disciplinary actions.
- Role-based Access: Distinct interfaces and permissions for administrators, teachers, department staff, students, and parents.

## Technology Stack
- Backend: Django (Python)
- Frontend: Django Templates, Bootstrap (customizable)
- Database: MySQL (recommended), SQLite (for development)
- Other: Django ORM, Django Messages Framework

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/duy3twave/demo_communication_system.git
   cd demo_communication_system
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the database:
   - Edit `settings.py` for your database credentials (default is SQLite).
5. Apply migrations:
   ```bash
   python manage.py migrate
   ```
6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
7. Run the development server:
   ```bash
   python manage.py runserver
   ```
8. Access the system:
   - Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## Usage Guide
- Admin Panel: Manage users, roles, classes, subjects, and departments via `/admin/`.
- Teachers:
  - Send notifications to classes, students, or parents.
  - Add evaluations and subject reviews for students.
  - View and manage class scores, rewards, and discipline records.
- Departments:
  - Send notifications to other departments, teachers, parents, or students (with restrictions).
  - Respond to request forms submitted by parents.
- Parents:
  - Submit requests/forms for their children.
  - View notifications, evaluations, and rewards/discipline records for their children.
- Students:
  - View personal notifications, evaluations, and academic records.
- Messaging:
  - Start direct conversations according to role-based permissions.

## Contribution & Support
- Contributions: Pull requests are welcome! Please open an issue first to discuss major changes.
- Contact: For questions or support, please contact the project maintainer or open an issue on GitHub.
