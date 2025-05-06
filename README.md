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