## Project Structure

```
school-management/
├── backend/
│   ├── models.py          # Database models
│   ├── app.py            # Main application
│   └── routes/           # API routes
│       ├── auth.py       # Authentication routes
│       ├── users.py      # User management
│       ├── notifications.py
│       ├── messages.py
│       ├── forms.py
│       ├── evaluations.py
│       └── rewards.py
├── frontend/
│   ├── index.html        # Main HTML file
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       ├── api.js        # API service
│       └── app.js        # Main application logic
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## Setup Instructions

### 1. Backend Setup

1. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
# Windows
cd backend
$env:FLASK_APP = "app:create_app"
$env:FLASK_ENV = "development"
flask init-db


# Linux/Mac
export FLASK_APP=backend/app.py
flask init-db
```

4. Run the backend server:
```bash
# Windows
$env:FLASK_APP = "app:create_app"
$env:FLASK_ENV = "development"
flask run

# Linux/Mac
export FLASK_APP=backend/app.py
export FLASK_ENV=development
flask run
```

The backend server will run at `http://localhost:5000`

### 2. Frontend Setup

1. Open the frontend folder:
```bash
cd frontend
```

2. Serve the frontend files using a local server. You can use Python's built-in server:
```bash
# Python 3
python -m http.server 8000

3. Open your browser and navigate to:
```
http://localhost:8000
```

## Demo Accounts

The system comes with pre-configured demo accounts for testing:

1. School Admin:
   - Username: admin
   - Password: admin123
   - Role: school

2. Department:
   - Username: department
   - Password: dept123
   - Role: department

3. Teacher:
   - Username: teacher
   - Password: teacher123
   - Role: teacher

4. Parent:
   - Username: parent
   - Password: parent123
   - Role: parent

5. Student:
   - Username: student
   - Password: student123
   - Role: student