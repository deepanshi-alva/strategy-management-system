import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Enable foreign keys
    c.execute("PRAGMA foreign_keys = ON")

    #user table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Workspaces Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            theme TEXT DEFAULT 'light',
            icon TEXT DEFAULT '📁',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    #tables created by the user
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            workspace_id INTEGER,
            table_name TEXT,
            is_default INTEGER DEFAULT 0,
            schema TEXT,
            physical_table_name TEXT,  -- could be JSON stringified
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_session_counters (
            user_id INTEGER PRIMARY KEY,
            current_id INTEGER
        );
    """)

    conn.commit()
    conn.close()

def add_user(full_name, email, password):
    if not full_name or not email or not password:
        return False  # Avoid empty insert
    password_hash = hash_password(password)
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)", (full_name, email, password_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(email, password):
    password_hash = hash_password(password)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password_hash))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_user_id(email):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_workspaces(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, name, is_default FROM workspaces WHERE user_id=?", (user_id,))
    result = c.fetchall()
    conn.close()
    return result

def create_workspace(user_id, name, theme="light", icon="📁", set_as_default=False):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    if set_as_default:
        # Unset all other defaults
        c.execute("UPDATE workspaces SET is_default=0 WHERE user_id=?", (user_id,))
    c.execute("INSERT INTO workspaces (user_id, name, is_default, theme, icon) VALUES (?, ?, ?, ?, ?)",
              (user_id, name, 1 if set_as_default else 0, theme, icon))
    conn.commit()
    conn.close()

def set_default_workspace(workspace_id, user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE workspaces SET is_default=0 WHERE user_id=?", (user_id,))
    c.execute("UPDATE workspaces SET is_default=1 WHERE id=? AND user_id=?", (workspace_id, user_id))
    conn.commit()
    conn.close()

def get_workspace_by_id(workspace_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT name, theme, icon FROM workspaces WHERE id=?", (workspace_id,))
    result = c.fetchone()
    conn.close()
    return result

def get_default_workspace_id(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id FROM workspaces WHERE user_id=? AND is_default=1", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None