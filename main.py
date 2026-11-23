import os, re, secrets, hashlib, smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, EmailStr, Field

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "https://localhost:8443")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true") == "true"
pool = ConnectionPool(os.environ["DATABASE_URL"], min_size=1, max_size=10, open=True,
                      kwargs={"row_factory": dict_row})
ph = PasswordHasher()
DUMMY = ph.hash("timing-equaliser")          # keeps login timing equal for unknown emails
app = FastAPI(docs_url=None, redoc_url=None)

now = lambda: datetime.now(timezone.utc)
digest = lambda t: hashlib.sha256(t.encode()).hexdigest()
GENERIC = "If this email can be registered, a verification link is on its way."

@app.middleware("http")
async def security_headers(request: Request, call_next):
    r = await call_next(request)
    r.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["Referrer-Policy"] = "same-origin"
    r.headers["Content-Security-Policy"] = ("default-src 'self'; style-src 'self' 'unsafe-inline' "
        "https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; img-src 'self' data:")
    return r

class SignUp(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    practice_goal: str = Field(default="interview", pattern="^(interview|viva|presentation|public)$")

class Login(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)

MAILS = {
    "verify": ("Verify your ConfiCoach account",
               "Welcome to ConfiCoach.\n\nConfirm your email (valid 24 hours):\n{l}\n\nIf you did not sign up, ignore this message."),
    "reset": ("Reset your ConfiCoach password",
              "We received a request to reset your password.\n\nSet a new one here (valid 1 hour):\n{l}\n\n"
              "If this was not you, ignore this message. Your password stays unchanged."),
}

def send_mail(to: str, link: str, kind: str = "verify"):
    subject, body = MAILS[kind]
    host = os.getenv("SMTP_HOST")
    if not host:
        print(f"\n[DEV] {kind} link for {to}: {link}\n"); return
    m = EmailMessage()
    m["Subject"], m["From"], m["To"] = subject, os.getenv("MAIL_FROM"), to
    m.set_content(body.format(l=link))
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", 587))) as srv:
        srv.starttls(); srv.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS")); srv.send_message(m)

@app.post("/api/signup", status_code=201)
def signup(d: SignUp):
    if not (re.search(r"[A-Za-z]", d.password) and re.search(r"\d", d.password)):
        raise HTTPException(422, "Password must contain letters and numbers.")
    email = d.email.lower()
    with pool.connection() as c:
        u = c.execute("INSERT INTO users(full_name,email,password_hash,practice_goal) VALUES(%s,%s,%s,%s) "
                      "ON CONFLICT (email) DO NOTHING RETURNING id",
                      (d.full_name.strip(), email, ph.hash(d.password), d.practice_goal)).fetchone()
        if not u:
            return {"message": GENERIC}      # same reply: no account enumeration
        tok = secrets.token_urlsafe(32)
        c.execute("INSERT INTO email_tokens VALUES(%s,%s,%s)",
                  (digest(tok), u["id"], now() + timedelta(hours=24)))
    send_mail(email, f"{BASE_URL}/api/verify?token={tok}")
    return {"message": GENERIC}

@app.get("/api/verify")
def verify(token: str):
    with pool.connection() as c:
        r = c.execute("DELETE FROM email_tokens WHERE token_hash=%s AND expires_at>now() "
                      "RETURNING user_id", (digest(token),)).fetchone()
        if r:
            c.execute("UPDATE users SET email_verified=TRUE WHERE id=%s", (r["user_id"],))
    return RedirectResponse(f"/?verified={'1' if r else '0'}")

@app.post("/api/login")
def login(d: Login, resp: Response):
    email, err, tok = d.email.lower(), None, None
    with pool.connection() as c:
        u = c.execute("SELECT * FROM users WHERE email=%s", (email,)).fetchone()
        if u and u["locked_until"] and u["locked_until"] > now():
            err = (429, "Too many attempts. Try again in 15 minutes.")
        else:
            try:
                ph.verify(u["password_hash"] if u else DUMMY, d.password); ok = bool(u)
            except VerifyMismatchError:
                ok = False
            if not ok:
                if u:
                    c.execute("UPDATE users SET "
                      "failed_attempts = CASE WHEN failed_attempts+1>=5 THEN 0 ELSE failed_attempts+1 END, "
                      "locked_until = CASE WHEN failed_attempts+1>=5 THEN now()+interval '15 minutes' "
                      "ELSE locked_until END WHERE id=%s", (u["id"],))
                err = (401, "Incorrect email or password.")
            elif not u["email_verified"]:
                err = (403, "Please verify your email first. Check your inbox.")
            else:
                c.execute("UPDATE users SET failed_attempts=0, locked_until=NULL WHERE id=%s", (u["id"],))
                tok = secrets.token_urlsafe(32)
                c.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(%s,%s,%s)",
                          (digest(tok), u["id"], now() + timedelta(days=7)))
    if err: raise HTTPException(*err)
    resp.set_cookie("session", tok, httponly=True, secure=COOKIE_SECURE, samesite="lax",
                    max_age=7*86400, path="/")
    return {"full_name": u["full_name"], "email": u["email"]}

@app.get("/api/me")
def me(request: Request):
    tok = request.cookies.get("session")
    if not tok: raise HTTPException(401, "Not signed in.")
    with pool.connection() as c:
        u = c.execute("SELECT u.full_name,u.email,u.practice_goal FROM sessions s JOIN users u ON u.id=s.user_id "
                      "WHERE s.token_hash=%s AND s.expires_at>now()", (digest(tok),)).fetchone()
    if not u: raise HTTPException(401, "Session expired.")
    return u

@app.post("/api/logout")
def logout(request: Request, resp: Response):
    tok = request.cookies.get("session")
    if tok:
        with pool.connection() as c:
            c.execute("DELETE FROM sessions WHERE token_hash=%s", (digest(tok),))
    resp.delete_cookie("session", path="/")
    return {"ok": True}

class Forgot(BaseModel):
    email: EmailStr

class Reset(BaseModel):
    token: str = Field(max_length=200)
    password: str = Field(min_length=10, max_length=128)

@app.post("/api/forgot")
def forgot(d: Forgot):
    email, tok = d.email.lower(), None
    with pool.connection() as c:
        u = c.execute("SELECT id FROM users WHERE email=%s", (email,)).fetchone()
        recent = u and c.execute("SELECT 1 FROM password_resets WHERE user_id=%s "
                                 "AND created_at>now()-interval '60 seconds'", (u["id"],)).fetchone()
        if u and not recent:                      # one mail per minute per account
            tok = secrets.token_urlsafe(32)
            c.execute("DELETE FROM password_resets WHERE user_id=%s", (u["id"],))
            c.execute("INSERT INTO password_resets(token_hash,user_id,expires_at) VALUES(%s,%s,%s)",
                      (digest(tok), u["id"], now() + timedelta(hours=1)))
    if tok:
        send_mail(email, f"{BASE_URL}/?reset={tok}", "reset")
    return {"message": "If an account exists, a reset link is on its way."}   # same reply always

@app.post("/api/reset")
def reset(d: Reset):
    if not (re.search(r"[A-Za-z]", d.password) and re.search(r"\d", d.password)):
        raise HTTPException(422, "Password must contain letters and numbers.")
    with pool.connection() as c:
        r = c.execute("DELETE FROM password_resets WHERE token_hash=%s AND expires_at>now() "
                      "RETURNING user_id", (digest(d.token),)).fetchone()
        if r:
            c.execute("UPDATE users SET password_hash=%s, email_verified=TRUE, failed_attempts=0, "
                      "locked_until=NULL WHERE id=%s", (ph.hash(d.password), r["user_id"]))
            c.execute("DELETE FROM sessions WHERE user_id=%s", (r["user_id"],))   # sign out everywhere
    if not r:
        raise HTTPException(400, "This reset link is invalid or has expired.")
    return {"message": "Password updated."}

app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
