from db_handler import init_db
import ui_login
import sqlite3
import config  # import the module, not just the variable
import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource (for PyInstaller compatibility)"""
    try:
        base_path = sys._MEIPASS  # PyInstaller creates this
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def preload_instruments():
    db_path = resource_path("20250606DB.db3")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT Name, Symbol, Token FROM ResultSet")
    config.cached_instruments = cur.fetchall()
    print("Loaded instruments:", len(config.cached_instruments))
    conn.close()

if __name__ == "__main__":
    init_db()
    preload_instruments()  # Load instruments once
    ui_login.login_window()