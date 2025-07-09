import tkinter as tk
from tkinter import messagebox
from db_handler import verify_user
import ui_signup
import ui_workspace
import db_handler
from window_utils import center_window, _perform_centering_on_restore, on_configure, cleanup_window

def reinitialize_session_ids(user_id):
    import sqlite3
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    all_rows = []
    current_id = 1  # Start fresh for this user

    # Step 1: Get all workspaces for the user ordered by creation time
    cur.execute("""
        SELECT id FROM workspaces
        WHERE user_id = ?
        ORDER BY datetime(created_at) ASC
    """, (user_id,))
    workspaces = [row[0] for row in cur.fetchall()]

    # Step 2: For each workspace, get associated tables
    for workspace_id in workspaces:
        cur.execute("""
            SELECT table_name, physical_table_name
            FROM user_tables
            WHERE user_id = ? AND workspace_id = ?
        """, (user_id, workspace_id))
        tables = cur.fetchall()

        # Step 3: For each table, fetch its rows
        for table_name, physical_table in tables:
            try:
                cur.execute(f"SELECT ID FROM {physical_table}")
                rows = cur.fetchall()

                # Step 4: Reassign new IDs using the running counter
                for row in rows:
                    old_id = row[0]
                    cur.execute(f"""
                        UPDATE {physical_table}
                        SET ID = ?
                        WHERE ID = ?
                    """, (current_id, old_id))
                    current_id += 1
            except sqlite3.Error as e:
                print(f"Error processing table {physical_table}: {e}")
                continue

    # Step 5: Update user's session counter
    cur.execute("""
        REPLACE INTO user_session_counters (user_id, current_id)
        VALUES (?, ?)
    """, (user_id, current_id - 1))  # last assigned ID

    conn.commit()
    conn.close()

def login_window():
    """Creates and displays the login window."""
    win = tk.Tk()
    win.title("LOGIN")
    win.geometry("400x300")

    center_window(win)
    win.state('zoomed')
    win.bind_id = win.bind('<Configure>', lambda event: on_configure(win, event, 400, 300))

    frame = tk.Frame(win)
    frame.pack(expand=True)

    tk.Label(frame, text="LOGIN", font=("Arial", 16, "bold")).pack(pady=10)

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
        # Gets user input from textboxes.
        email = email_entry.get().strip()
        password = password_entry.get().strip()

        # Shows a warning if either field is empty.
        if not email or not password:
            messagebox.showwarning("Empty Fields", "Please fill in all fields.")
            return
        
        # If login is successful:
        if verify_user(email, password):
            messagebox.showinfo("Success", "Login Successful!")
            cleanup_window(win)
            win.destroy()
            user_id = db_handler.get_user_id(email)
            reinitialize_session_ids(user_id)
            ui_workspace.workspace_window(email)
        else:
            messagebox.showerror("Failed", "Invalid credentials")

    tk.Button(frame, text="Login", width=20, command=login, bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(pady=10)
    tk.Button(frame, text="Go to Signup", width=20, bg="#07365C", fg="white", font=("Arial", 10, "bold","underline"), command=lambda:[cleanup_window(win), win.destroy(), ui_signup.signup_window()]).pack()
    win.mainloop()
 