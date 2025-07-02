import tkinter as tk
from tkinter import messagebox
from db_handler import add_user
import ui_login

def signup_window():
    win = tk.Tk()
    win.title("Signup")
    win.geometry("400x400")
    # win.resizable(False, False)

    frame = tk.Frame(win)
    frame.pack(expand=True)

    tk.Label(frame, text="Signup", font=("Arial", 16, "bold")).pack(pady=10)

    # Full Name
    tk.Label(frame, text="Full Name").pack()
    name_entry = tk.Entry(frame, width=30)
    name_entry.pack(pady=5)

    # Email
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

    def register():
        full_name = name_entry.get().strip()
        email = email_entry.get().strip()
        password = password_entry.get().strip()
        if not full_name or not email or not password:
            messagebox.showwarning("Empty Fields", "Please fill in all fields.")
            return
        if add_user(full_name, email, password):
            messagebox.showinfo("Success", "Signup Successful!")
            win.destroy()
            ui_login.login_window()
        else:
            messagebox.showerror("Error", "Email already exists")

    tk.Button(frame, text="Signup", width=20, command=register, bg="#4CAF50", fg="white").pack(pady=10)
    tk.Button(frame, text="Go to Login", command=lambda:[win.destroy(), ui_login.login_window()]).pack()
    win.mainloop()
