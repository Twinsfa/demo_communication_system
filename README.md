# School Communication System

A comprehensive communication system for schools that facilitates interaction between school administrators, teachers, parents, and students.

## Features

- User Management with Role-based Access Control
- Real-time Messaging System
- Announcements and Event Notifications
- Parent Forms and Requests
- Grade Management
- Student Rewards and Discipline Records

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn

## Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the backend directory with:
```
JWT_SECRET_KEY=your-secret-key-here
FLASK_APP=app.py
FLASK_ENV=development
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the backend server:
```bash
flask run
```

The backend server will run on `http://localhost:5000`

## API Endpoints

### Authentication
- POST `/api/auth/register` - Register a new user
- POST `/api/auth/login` - Login user
- GET `/api/auth/users` - Get all users (school admin only)
- PUT `/api/auth/users/<id>` - Update user (school admin only)
- DELETE `/api/auth/users/<id>` - Delete user (school admin only)

### Messages
- POST `/api/messages` - Send a message
- GET `/api/messages/received` - Get received messages
- GET `/api/messages/sent` - Get sent messages
- PUT `/api/messages/<id>/read` - Mark message as read
- DELETE `/api/messages/<id>` - Delete message

### Announcements
- POST `/api/announcements` - Create announcement
- GET `/api/announcements` - Get announcements
- PUT `/api/announcements/<id>` - Update announcement
- DELETE `/api/announcements/<id>` - Delete announcement

### Forms
- POST `/api/forms` - Submit form
- GET `/api/forms/received` - Get received forms
- GET `/api/forms/sent` - Get sent forms
- PUT `/api/forms/<id>/respond` - Respond to form
- DELETE `/api/forms/<id>` - Delete form

### Grades
- POST `/api/grades` - Submit grade
- GET `/api/grades/student/<id>` - Get student grades
- GET `/api/grades/class/<class_name>` - Get class grades
- PUT `/api/grades/<id>` - Update grade
- DELETE `/api/grades/<id>` - Delete grade

### Rewards
- POST `/api/rewards` - Create reward record
- GET `/api/rewards/student/<id>` - Get student rewards
- GET `/api/rewards/class/<class_name>` - Get class rewards
- PUT `/api/rewards/<id>` - Update reward record
- DELETE `/api/rewards/<id>` - Delete reward record

## User Roles

1. School Administrator
   - Full access to all features
   - User management
   - System-wide announcements
   - View all data

2. Teacher
   - Manage class announcements
   - Submit and manage grades
   - Record rewards/discipline
   - Communicate with parents and students

3. Parent
   - View child's grades and records
   - Submit forms and requests
   - Receive announcements
   - Communicate with teachers

4. Student
   - View own grades and records
   - Receive announcements
   - Communicate with teachers

## Security

- JWT-based authentication
- Role-based access control
- Password hashing
- Input validation
- CORS protection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request