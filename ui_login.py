import tkinter as tk
from tkinter import messagebox
from db_handler import verify_user
import ui_signup
import ui_workspace
import db_handler

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
