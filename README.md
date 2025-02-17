
# RapidStack
A Docker-FastAPI-React Starter for Quick Prototyping

Have an idea but need a framework to start with? This repository provides a **minimal** working example of a **FastAPI** + **React** + **Postgres** setup with **JWT authentication**—all orchestrated via **Docker Compose**. 

---

## Overview

1. **`setup_project.py`**  
   A Python script that creates the entire project structure:
   - **`docker-auth-website/backend/app`** for the **FastAPI** backend
   - **`docker-auth-website/frontend`** for the **React** frontend
   - **`docker-compose.yml`** to spin up **Postgres**, **FastAPI**, and **React** simultaneously

2. **Backend (FastAPI)**
   - **Authentication**: Users can sign up and log in, receiving JWT tokens.
   - **Protected Routes**: A `/dashboard` endpoint requires a valid token.
   - **Database**: Uses **SQLAlchemy** with a Postgres DB.
   - **CORS Middleware**: Allows requests from the React frontend on `localhost:3000`.

3. **Frontend (React)**
   - **Login** & **Signup** pages that call the FastAPI endpoints.
   - **Dashboard** page that’s protected; the user must have a valid token to view it.
   - **Routing**: React Router (v6) sets up `/login`, `/signup`, `/dashboard`, etc.

4. **Database (Postgres)**
   - Hosted in a Docker container defined in `docker-compose.yml`.
   - Credentials (user, password) are set in environment variables, currently for demo purposes.

---

## Quick Start

1. **Clone or Download** this repository.

2. **Create & Run** the project structure by executing the `setup_project.py` script:
   ```bash
   python setup_project.py
   ```
   This will generate a folder named `docker-auth-website/` containing all necessary files.

3. **Navigate** into the new `docker-auth-website/` directory:
   ```bash
   cd docker-auth-website
   ```

4. **Build and Run** the Docker containers:
   ```bash
   docker-compose up --build
   ```
   - **frontend**: React app at [http://localhost:3000](http://localhost:3000)
   - **backend**: FastAPI at [http://localhost:8000](http://localhost:8000)
   - **database**: Postgres running internally on port 5432

5. **Visit** the app in your browser:
   - [http://localhost:3000](http://localhost:3000) – React homepage
   - **Signup** at `/signup`
   - **Login** at `/login`
   - **Dashboard** at `/dashboard` (requires JWT token)

---

## Directory Structure

After running `setup_project.py`, you’ll get:

```
docker-auth-website/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point; sets up routes & CORS
│   │   ├── auth.py              # JWT authentication logic
│   │   ├── models.py            # SQLAlchemy models (e.g., User)
│   │   ├── database.py          # Database engine & session
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── users.py         # Example route for listing users
│   ├── Dockerfile
│   ├── requirements.txt         # Python dependencies
│   └── .env
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── pages/
│   │   │   └── Home.js
│   │   ├── components/
│   │   │   ├── Login.js
│   │   │   ├── Signup.js
│   │   │   └── Dashboard.js
│   │   ├── App.js               # Main React routes
│   │   └── index.js             # React entry point
│   ├── Dockerfile
│   ├── package.json
│   └── .env
├── docker-compose.yml
└── ...
```

---

## How It Works

1. **`setup_project.py`**: A Python script that creates the entire file structure. It also automatically runs `npm install` in the `frontend` folder if `npm` is found on your machine.

2. **Docker Compose**:
   - **`docker-compose.yml`** starts three services:
     1. **`frontend`** – A Node-based container running your React app on port `3000`.
     2. **`backend`** – A Python container running FastAPI + Uvicorn on port `8000`.
     3. **`db`** – A Postgres container storing your user data.

3. **FastAPI** + **SQLAlchemy**:
   - **`auth.py`** handles password hashing, user creation, JWT generation, and authentication checks.
   - **`main.py`** defines endpoint routes (`/signup`, `/login`, `/dashboard`) and sets up **CORS**.
   - **`models.py`** + **`database.py`** define the `User` table and a function to get a DB session.

4. **React**:
   - Users can **signup** and **login**, storing the JWT in `localStorage`.
   - The **Dashboard** page checks for a token. If missing or invalid, it redirects to `/login`.
   - Simple forms in `Login.js` and `Signup.js` demonstrate how to call the backend.

---

## Customization & Next Steps

- **Secrets**: In production, store `DATABASE_URL` and `SECRET_KEY` in environment variables or a secret manager.
- **CORS**: Limit `allow_origins` to your actual production domain(s).
- **HTTPS**: Use a reverse proxy or hosting platform to enable SSL.
- **Password Rules**: Add validation for stronger password requirements.
- **Rate Limiting**: Protect login against brute-force attacks.

---

## License

This project is provided as an example. Feel free to adapt or extend it to suit your needs. 

