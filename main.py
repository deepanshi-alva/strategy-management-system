from db_handler import init_db
import ui_login
import sqlite3
import instrument_cache  # import the module, not just the variable

def preload_instruments():
    conn = sqlite3.connect("20250606DB.db3")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT Name, Symbol, Token FROM ResultSet")
    instrument_cache.cached_instruments = cur.fetchall()
    print("Loaded instruments:", len(instrument_cache.cached_instruments))
    conn.close()

if __name__ == "__main__":
    init_db()
    preload_instruments()  # Load instruments once
    ui_login.login_window()
