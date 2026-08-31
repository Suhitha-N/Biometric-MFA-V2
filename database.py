import sqlite3
import bcrypt
from datetime import datetime, timedelta

DB_PATH = "users.db"
MAX_FAILED_ATTEMPTS = 3
LOCK_MINUTES = 5
MIN_PASSWORD_LENGTH = 8


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password BLOB NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                account_status TEXT NOT NULL DEFAULT 'active',
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                created_at TEXT,
                last_login TEXT
            )
        """)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        migrations = {
            "account_status": "ALTER TABLE users ADD COLUMN account_status TEXT NOT NULL DEFAULT 'active'",
            "failed_attempts": "ALTER TABLE users ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0",
            "locked_until": "ALTER TABLE users ADD COLUMN locked_until TEXT",
            "created_at": "ALTER TABLE users ADD COLUMN created_at TEXT",
            "last_login": "ALTER TABLE users ADD COLUMN last_login TEXT",
        }
        for name, sql in migrations.items():
            if name not in columns:
                conn.execute(sql)
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute("UPDATE users SET created_at=? WHERE created_at IS NULL", (now,))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                factor TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()


def password_policy(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must contain at least {MIN_PASSWORD_LENGTH} characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain an uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain a lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain a number"
    if not any(not c.isalnum() for c in password):
        return False, "Password must contain a special character"
    return True, "OK"


def create_admin(username="admin", password="admin123"):
    """Create a demo admin only if no admin exists.

    Existing project databases are preserved. For a real deployment, replace the
    demo password immediately using the password reset/admin controls.
    """
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
        if row:
            return False
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO users(username,password,role,created_at) VALUES(?,?,?,?)",
            (username, hashed, "admin", now),
        )
        conn.commit()
        log_auth(username, "SYSTEM", "INFO", "Demo admin created; change password before deployment")
        return True


def register_user(username, password, role="user"):
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required"
    if len(username) > 50:
        return False, "Username is too long"
    if role not in {"user", "admin"}:
        return False, "Invalid role"
    ok, msg = password_policy(password)
    if not ok:
        return False, msg
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users(username,password,role,created_at) VALUES(?,?,?,?)",
                (username, hashed, role, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
        return True, "User created"
    except sqlite3.IntegrityError:
        return False, "Username already exists"


def is_locked(username):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT account_status, locked_until FROM users WHERE username=?", (username,)
        ).fetchone()
    if not row or row["account_status"] != "locked" or not row["locked_until"]:
        return False
    try:
        until = datetime.fromisoformat(row["locked_until"])
    except ValueError:
        return False
    if datetime.now() >= until:
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET account_status='active', failed_attempts=0, locked_until=NULL WHERE username=?",
                (username,),
            )
            conn.commit()
        return False
    return True


def verify_user(username, password):
    username = username.strip()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not row:
        return False, None, "Invalid username or password"
    if is_locked(username):
        return False, row["role"], f"Account temporarily locked for up to {LOCK_MINUTES} minutes"
    try:
        valid = bcrypt.checkpw(password.encode("utf-8"), row["password"])
    except (ValueError, TypeError):
        valid = False
    if not valid:
        attempts = int(row["failed_attempts"] or 0) + 1
        if attempts >= MAX_FAILED_ATTEMPTS:
            until = datetime.now() + timedelta(minutes=LOCK_MINUTES)
            with get_connection() as conn:
                conn.execute(
                    "UPDATE users SET failed_attempts=?, account_status='locked', locked_until=? WHERE username=?",
                    (attempts, until.isoformat(timespec="seconds"), username),
                )
                conn.commit()
            return False, row["role"], f"Account locked for {LOCK_MINUTES} minutes"
        with get_connection() as conn:
            conn.execute("UPDATE users SET failed_attempts=? WHERE username=?", (attempts, username))
            conn.commit()
        remaining = MAX_FAILED_ATTEMPTS - attempts
        return False, row["role"], f"Invalid username or password ({remaining} attempt(s) remaining)"
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET failed_attempts=0, account_status='active', locked_until=NULL, last_login=? WHERE username=?",
            (datetime.now().isoformat(timespec="seconds"), username),
        )
        conn.commit()
    return True, row["role"], "Password verified"


def reset_password(username, new_password):
    ok, _ = password_policy(new_password)
    if not ok:
        return False
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE users SET password=?, failed_attempts=0, account_status='active', locked_until=NULL WHERE username=?",
            (hashed, username.strip()),
        )
        conn.commit()
        return cur.rowcount > 0


def get_users(include_admin=False):
    query = "SELECT username, role, account_status, failed_attempts, created_at, last_login FROM users"
    if not include_admin:
        query += " WHERE role='user'"
    query += " ORDER BY username"
    with get_connection() as conn:
        return conn.execute(query).fetchall()


def get_user(username):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()


def delete_user(username):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM users WHERE username=? AND role='user'", (username.strip(),))
        conn.commit()
        return cur.rowcount > 0


def log_auth(username, factor, status, details=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO auth_logs(username,factor,status,details,timestamp) VALUES(?,?,?,?,?)",
            (username, factor, status, details, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()


def get_logs(limit=200):
    limit = max(1, min(int(limit), 1000))
    with get_connection() as conn:
        return conn.execute(
            "SELECT username, factor, status, details, timestamp FROM auth_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


init_db()
create_admin()
