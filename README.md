# ConfiCoach - Login and Sign Up (FastAPI + PostgreSQL + React)

## What you need installed
- Python 3.11 or newer  (python.org)
- Node.js 18 or newer   (nodejs.org, LTS)
- PostgreSQL 15 or newer (postgresql.org, EDB installer; remember the password you set for user "postgres")

## Project layout
    conficoach/
      main.py            backend API (signup, verify, login, logout, forgot, reset)
      schema.sql         database tables
      requirements.txt   Python packages
      .env.example       settings template
      frontend/          React app (Vite)

## First-time setup (Windows PowerShell; Mac/Linux steps are the same except venv activation)

### 1. Create the database
Open "SQL Shell (psql)" from the Start menu, or run `psql -U postgres -h localhost`. Then type:

    CREATE USER conficoach WITH PASSWORD 'ChooseAStrongPassword1';
    CREATE DATABASE conficoach OWNER conficoach;
    \q

Create the tables (run inside the conficoach folder):

    psql -U conficoach -h localhost -d conficoach -f schema.sql

If "psql" is not recognised, add C:\Program Files\PostgreSQL\16\bin to your PATH (change 16 to your version) and reopen PowerShell.

### 2. Backend setup
    cd conficoach
    python -m venv venv
    venv\Scripts\activate            (Mac/Linux: source venv/bin/activate)
    pip install -r requirements.txt
    copy .env.example .env           (Mac/Linux: cp .env.example .env)

If activation is blocked: `Set-ExecutionPolicy -Scope Process Bypass`, then activate again.

Open `.env` and set DATABASE_URL with your password:

    DATABASE_URL=postgresql://conficoach:ChooseAStrongPassword1@localhost:5432/conficoach

If the password contains special characters, URL-encode them (@ becomes %40, # becomes %23).
Keep BASE_URL=http://localhost:8000, COOKIE_SECURE=false and SMTP_HOST empty for the first run.

### 3. Build the frontend
    cd frontend
    npm install
    npm run build
    cd ..

### 4. Run
    uvicorn main:app --port 8000 --reload

Open http://localhost:8000

### 5. Test it
1. Click "Create an account", fill the form, choose a goal, press "Create account".
2. Look at the terminal running uvicorn. It prints a line like `[DEV] verify link for you@example.com: http://localhost:8000/api/verify?token=...`. Open that link.
3. You land on Log In with "Email verified". Log in.
4. Test "Forgot Password?": the reset link also prints in the terminal.

Check the data in PostgreSQL:

    psql -U conficoach -h localhost -d conficoach -c "SELECT id, email, email_verified, practice_goal FROM users;"

### Optional: live editing the UI
Keep uvicorn running, open a second terminal:

    cd frontend
    npm run dev

Open http://localhost:5173 (it forwards /api calls to port 8000).

## Real emails (Gmail)
1. Turn on 2-Step Verification on the Google account.
2. Create an App Password (Google Account > Security > App passwords).
3. In .env set: SMTP_HOST=smtp.gmail.com, SMTP_USER=your@gmail.com, SMTP_PASS=the app password, MAIL_FROM=ConfiCoach <your@gmail.com>.
Restart uvicorn.

## HTTPS
Local https: install mkcert, then
    mkcert -install
    mkcert localhost
    uvicorn main:app --port 8443 --ssl-keyfile localhost-key.pem --ssl-certfile localhost.pem
and set BASE_URL=https://localhost:8443, COOKIE_SECURE=true.

Production: put the app behind Caddy (automatic certificates). Caddyfile:

    yourdomain.com {
        reverse_proxy localhost:8000
    }

Run uvicorn without --reload, set BASE_URL=https://yourdomain.com and COOKIE_SECURE=true.

## Troubleshooting
- password authentication failed: wrong password in DATABASE_URL.
- connection refused: PostgreSQL service is not running (Services > postgresql).
- relation "users" does not exist: step 1 schema.sql was not run on the conficoach database.
- Directory 'frontend/dist' does not exist: run step 3 (npm run build).
- Login works but page logs you out: COOKIE_SECURE=true while using plain http. Set it to false for http.
- No email arrives: with SMTP_HOST empty, links appear in the uvicorn terminal, not in your inbox.

## Character image
The login hero uses frontend/public/coach.png (transparent PNG). Replace that file with your own licensed illustration to change the character; no code change is needed. If the file is missing, a built-in SVG character is shown instead. Confirm the licence of any image before production use.
