import tkinter as tk
from tkinter import messagebox
from db_handler import add_user
import ui_login
from window_utils import center_window, _perform_centering_on_restore, on_configure, cleanup_window

def signup_window():
    win = tk.Tk()
    win.title("Signup")
    win.geometry("400x400")

    center_window(win)
    win.state('zoomed')

    # Store the on_configure binding ID
    win.bind_id = win.bind('<Configure>', lambda event: on_configure(win, event, 400, 400)) # Pass default dimensions for normal state

    frame = tk.Frame(win)
    frame.pack(expand=True)

    tk.Label(frame, text="SIGNUP", font=("Arial", 16, "bold")).pack(pady=10)

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
            cleanup_window(win) # Call cleanup before destroying
            win.destroy()
            ui_login.login_window()
        else:
            messagebox.showerror("Error", "Email already exists")

    tk.Button(frame, text="Signup", width=20, command=register, bg="#4CAF50", fg="white",font=("Arial", 10, "bold")).pack(pady=10)
    # Modify the command to include cleanup
    tk.Button(frame, text="Go to Login",bg="#07365C", fg="white", width=20, font=("Arial", 10, "bold","underline") ,command=lambda:[cleanup_window(win), win.destroy(), ui_login.login_window()]).pack()
    win.mainloop()