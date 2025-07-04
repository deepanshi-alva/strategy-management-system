import tkinter as tk
from tkinter import messagebox
from db_handler import verify_user
import ui_signup
import ui_workspace
import db_handler
import sqlite3

def reinitialize_session_ids(user_id):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # Step 1: Get all user tables and their physical names
    cur.execute("SELECT table_name, physical_table_name FROM user_tables WHERE user_id = ?", (user_id,))
    tables = cur.fetchall()

    all_rows = []
    table_map = {}

    # Step 2: Collect all rows with current IDs
    for table_name, physical_table in tables:
        cur.execute(f"SELECT ID FROM {physical_table}")
        rows = cur.fetchall()
        for row in rows:
            all_rows.append((int(row[0]), table_name, physical_table))
        table_map[table_name] = physical_table

    # Step 3: Sort and reassign new IDs
    all_rows.sort(key=lambda x: x[0])  # Sort by existing ID
    id_mapping = {}
    for new_id, (old_id, table_name, physical_table) in enumerate(all_rows, start=1):
        id_mapping[(physical_table, old_id)] = new_id

    # Step 4: Update tables with new IDs
    for (physical_table, old_id), new_id in id_mapping.items():
        cur.execute(f"UPDATE {physical_table} SET ID = ? WHERE ID = ?", (new_id, old_id))

    # Step 5: Update counter
    if all_rows:
        last_id = len(all_rows)
    else:
        last_id = 0
    cur.execute("REPLACE INTO user_session_counters (user_id, current_id) VALUES (?, ?)", (user_id, last_id))

    conn.commit()
    conn.close()

def login_window():
    win = tk.Tk()
    win.title("Login")
    win.geometry("400x300")
    # win.resizable(False, False)

    frame = tk.Frame(win)
    frame.pack(expand=True)

    tk.Label(frame, text="Login", font=("Arial", 16, "bold")).pack(pady=10)

    tk.Label(frame, text="Email").pack()
    email_entry = tk.Entry(frame, width=30)
    email_entry.pack(pady=5)

    tk.Label(frame, text="Password").pack()
    password_frame = tk.Frame(frame)
    password_frame.pack()

    password_var = tk.StringVar()
    password_entry = tk.Entry(password_frame, textvariable=password_var, width=23, show="*")
    password_entry.pack(side="left", pady=5)

    show_password = tk.BooleanVar()

    def toggle_password():
        password_entry.config(show="" if show_password.get() else "*")

    toggle_btn = tk.Checkbutton(password_frame, text="Show", variable=show_password, command=toggle_password)
    toggle_btn.pack(side="left", padx=5)

    def login():
        email = email_entry.get().strip()
        password = password_entry.get().strip()
        if not email or not password:
            messagebox.showwarning("Empty Fields", "Please fill in all fields.")
            return
        if verify_user(email, password):
            messagebox.showinfo("Success", "Login Successful!")
            win.destroy()
            user_id = db_handler.get_user_id(email)
            reinitialize_session_ids(user_id)
            default_workspace_id = db_handler.get_default_workspace_id(user_id)
            if default_workspace_id:
                from ui_workspace_view import open_workspace_layout
                open_workspace_layout(default_workspace_id, email)
            else:
                ui_workspace.workspace_window(email)
        else:
            messagebox.showerror("Failed", "Invalid credentials")

    tk.Button(frame, text="Login", width=20, command=login, bg="#2196F3", fg="white").pack(pady=10)
    tk.Button(frame, text="Go to Signup", command=lambda:[win.destroy(), ui_signup.signup_window()]).pack()
    win.mainloop()
