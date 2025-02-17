import os
import subprocess
import shutil

# Define the base directory
base_path = os.getcwd()

project_structure = {
    "docker-auth-website": {
        "backend": {
            "app": {
                "__init__.py": "",  # Recognize 'app' as a Python package
                "main.py": """from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, database, auth
from .routes import users

app = FastAPI()

# ---- ALLOW ALL ORIGINS (LOCAL DEV ONLY) ----
# This will prevent any CORS domain issues on localhost, 127.0.0.1, etc.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# If you want to mount auth.router, uncomment:
# app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.users_router, prefix="/api", tags=["users"])

# Create tables
database.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def home():
    return {"message": "Welcome to the FastAPI app"}

@app.post("/signup")
def signup(user: auth.UserCreate, db: Session = Depends(database.get_db)):
    return auth.create_user(db, user)

@app.post("/login")
def login(user: auth.UserLogin, db: Session = Depends(database.get_db)):
    db_user = auth.authenticate_user(db, user)
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # Generate JWT token
    access_token = auth.create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/dashboard")
def get_dashboard(current_user: models.User = Depends(auth.get_current_user)):
    return {"message": f"Welcome to your dashboard, {current_user.username}!"}
""",
                "auth.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from . import models, database

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "supersecretkey"  # Replace with your own SECRET key in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2PasswordBearer expects a route where clients can obtain a token
# We point this to '/login' in main.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    '''Generate a JWT token with optional expiration.'''
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_user(db: Session, user: UserCreate):
    # Check for duplicate username
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken.")

    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": f"User {db_user.username} created successfully."}

def authenticate_user(db: Session, user: UserLogin):
    '''Return user object if password checks out, otherwise None.'''
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        return None
    return db_user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    '''Dependency that checks token validity and returns the current user.'''
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
""",
                "models.py": """from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
""",
                "database.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://user:password@db:5432/authdb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
                "routes": {
                    "__init__.py": "",
                    "users.py": """from fastapi import APIRouter

users_router = APIRouter()

@users_router.get("/users")
def get_users():
    return {"users": []}
"""
                }
            },
            "Dockerfile": """FROM python:3.9
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
            "requirements.txt": """fastapi
uvicorn
sqlalchemy
psycopg2
passlib[bcrypt]
python-jose[cryptography]
""",
            ".env": "DATABASE_URL=postgresql://user:password@db:5432/authdb\n"
        },
        "frontend": {
            "public": {
                "index.html": """<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>React App</title>
</head>
<body>
    <div id='root'></div>
</body>
</html>
"""
            },
            "src": {
                "pages": {
                    "Home.js": """import React from 'react';

function Home() {
    const containerStyle = {
        textAlign: 'center',
        marginTop: '50px'
    };

    return (
        <div style={containerStyle}>
            <h1>Welcome Home</h1>
            <p>Sign up or log in to get started!</p>
        </div>
    );
}

export default Home;
"""
                },
                "components": {
                    "Login.js": """import React, { useState } from 'react';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        const data = { username, password };
        try {
            const response = await fetch(process.env.REACT_APP_API_URL + '/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            if (response.ok) {
                localStorage.setItem('token', result.access_token);
                alert('Login successful');
                window.location.href = '/dashboard';
            } else {
                alert(result.detail || 'Login failed');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Something went wrong');
        }
    };

    const formStyle = {
        display: 'flex',
        flexDirection: 'column',
        maxWidth: '400px',
        margin: '40px auto',
        padding: '20px',
        border: '1px solid #ccc',
        borderRadius: '8px',
    };

    const inputStyle = {
        marginBottom: '12px',
        padding: '8px',
        fontSize: '1rem'
    };

    const buttonStyle = {
        padding: '10px',
        fontSize: '1rem',
        cursor: 'pointer',
        backgroundColor: '#2196f3',
        color: '#fff',
        border: 'none',
        borderRadius: '4px'
    };

    return (
        <form onSubmit={handleSubmit} style={formStyle}>
            <h1 style={{ textAlign: 'center' }}>Login</h1>
            <label>Username</label>
            <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={inputStyle}
                required
            />

            <label>Password</label>
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={inputStyle}
                required
            />

            <button type="submit" style={buttonStyle}>Login</button>
        </form>
    );
}

export default Login;
""",
                    "Signup.js": """import React, { useState } from 'react';

function Signup() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        const data = { username, password };
        try {
            const response = await fetch(process.env.REACT_APP_API_URL + '/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            if (response.ok) {
                alert('Signup successful');
                window.location.href = '/login';
            } else {
                alert(result.detail || 'Signup failed');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Something went wrong');
        }
    };

    const formStyle = {
        display: 'flex',
        flexDirection: 'column',
        maxWidth: '400px',
        margin: '40px auto',
        padding: '20px',
        border: '1px solid #ccc',
        borderRadius: '8px'
    };

    const inputStyle = {
        marginBottom: '12px',
        padding: '8px',
        fontSize: '1rem'
    };

    const buttonStyle = {
        padding: '10px',
        fontSize: '1rem',
        cursor: 'pointer',
        backgroundColor: '#4caf50',
        color: '#fff',
        border: 'none',
        borderRadius: '4px'
    };

    return (
        <form onSubmit={handleSubmit} style={formStyle}>
            <h1 style={{ textAlign: 'center' }}>Signup</h1>
            <label>Username</label>
            <input 
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={inputStyle}
                required
            />

            <label>Password</label>
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={inputStyle}
                required
            />

            <button type="submit" style={buttonStyle}>Sign Up</button>
        </form>
    );
}

export default Signup;
""",
                    "Dashboard.js": """import React, { useEffect, useState } from 'react';

function Dashboard() {
    const [message, setMessage] = useState('');
    const token = localStorage.getItem('token');

    useEffect(() => {
        if (!token) {
            window.location.href = '/login';
            return;
        }
        fetch(process.env.REACT_APP_API_URL + '/dashboard', {
            headers: {
                'Authorization': 'Bearer ' + token,
            }
        })
        .then(async (response) => {
            if (response.status === 401) {
                window.location.href = '/login';
            }
            const data = await response.json();
            if (data.message) {
                setMessage(data.message);
            } else {
                setMessage('No message from server');
            }
        })
        .catch(err => {
            console.error('Error', err);
            setMessage('Error fetching dashboard');
        });
    }, [token]);

    const containerStyle = {
        maxWidth: '600px',
        margin: '40px auto',
        textAlign: 'center',
        padding: '20px',
        border: '1px solid #ccc',
        borderRadius: '8px'
    };

    // Sign out function
    const handleSignOut = () => {
        // Clear token from localStorage
        localStorage.removeItem('token');
        // Redirect to login page
        window.location.href = '/login';
    };

    const buttonStyle = {
        marginTop: '20px',
        padding: '10px',
        fontSize: '1rem',
        cursor: 'pointer',
        backgroundColor: '#f44336',
        color: '#fff',
        border: 'none',
        borderRadius: '4px'
    };

    return (
        <div style={containerStyle}>
            <h1>Dashboard</h1>
            <p>{message}</p>
            <button onClick={handleSignOut} style={buttonStyle}>Sign Out</button>
        </div>
    );
}

export default Dashboard;
"""
                },
                "index.js": """import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

ReactDOM.render(<App />, document.getElementById('root'));
""",
                "App.js": """import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Home from './pages/Home';
import Login from './components/Login';
import Signup from './components/Signup';
import Dashboard from './components/Dashboard';

function App() {
    return (
        <Router>
            <Routes>
                <Route path='/' element={<Home />} />
                <Route path='/login' element={<Login />} />
                <Route path='/signup' element={<Signup />} />
                <Route path='/dashboard' element={<Dashboard />} />
            </Routes>
        </Router>
    );
}

export default App;
"""
            },
            "Dockerfile": """FROM node:14
WORKDIR /app
COPY package.json package.json
RUN npm install
COPY . .
RUN npm install react-scripts
CMD ["npm", "run", "start"]
""",
            "package.json": """{
  "name": "frontend",
  "version": "1.0.0",
  "scripts": {
    "start": "react-scripts start"
  },
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-router-dom": "^6.0.0",
    "react-scripts": "^5.0.1"
  }
}
""",
            ".env": "REACT_APP_API_URL=http://localhost:8000\n"
        },
        "docker-compose.yml": """version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - '3000:3000'
    depends_on:
      - backend
    networks:
      - app_network

  backend:
    build: ./backend
    ports:
      - '8000:8000'
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/authdb
    networks:
      - app_network

  db:
    image: postgres:latest
    restart: always
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: authdb
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - app_network

networks:
  app_network:
    driver: bridge

volumes:
  pgdata:
"""
    }
}

def create_structure(base_path, structure):
    """Recursively create folders and files based on the dictionary."""
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)

# Run the script
create_structure(base_path, project_structure)

# Check Dockerfiles
backend_dockerfile = os.path.join(base_path, "docker-auth-website", "backend", "Dockerfile")
frontend_dockerfile = os.path.join(base_path, "docker-auth-website", "frontend", "Dockerfile")

if not os.path.exists(backend_dockerfile) or not os.path.exists(frontend_dockerfile):
    print("❌ ERROR: One or both Dockerfiles are missing. Check project structure.")
    exit(1)

# Check package.json in frontend & run npm install
frontend_path = os.path.join(base_path, "docker-auth-website", "frontend")
package_json_path = os.path.join(frontend_path, "package.json")

if os.path.exists(package_json_path):
    npm_path = shutil.which("npm")
    if npm_path:
        subprocess.run([npm_path, "install"], cwd=frontend_path, check=True)
    else:
        print("❌ ERROR: npm not found. Ensure Node.js is installed and on your PATH.")
else:
    print("❌ ERROR: package.json was not created. Check script execution.")

print("✅ Project structure created successfully!")
