import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel
import db_handler
import ui_login
from ui_workspace_view import open_workspace_layout

open_workspace_windows = {}

# Common emoji options
EMOJIS = ["📁", "📊", "🧾", "📈", "🗂️", "💼", "📋", "🧮", "📜", "🧠"]

def workspace_window(email):
    win = tk.Tk()
    win.title("Workspaces")
    win.attributes("-fullscreen", True)

    user_id = db_handler.get_user_id(email)

    def exit_fullscreen():
        win.attributes("-fullscreen", False)

    def logout():
        win.destroy()
        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM user_session_counters WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        ui_login.login_window()

    def set_default(workspace_id):
        db_handler.set_default_workspace(workspace_id, user_id)
        refresh_workspaces()
    
    def edit_workspace(workspace_id):
        ws_data = db_handler.get_workspace_by_id(workspace_id)
        if not ws_data:
            messagebox.showerror("Error", "Workspace not found.")
            return

        current_name, current_theme, current_emoji = ws_data[0], ws_data[1], ws_data[2]

        new_name = simpledialog.askstring("Edit Workspace", "Enter new name:", initialvalue=current_name, parent=win)
        if not new_name:
            return

        def on_emoji_selected(new_emoji):
            new_theme = simpledialog.askstring("Theme", "Enter theme (light or dark):", initialvalue=current_theme, parent=win)
            if new_theme not in ["light", "dark"]:
                new_theme = "light"
            db_handler.update_workspace(workspace_id, new_name, new_theme, new_emoji)
            refresh_workspaces()

        show_emoji_picker(on_emoji_selected)

    def delete_workspace(workspace_id):
        confirm = messagebox.askyesno("Delete Workspace", "Are you sure you want to delete this workspace?")
        if confirm:
            db_handler.delete_workspace(workspace_id)
            if workspace_id in open_workspace_windows:
                try:
                    open_workspace_windows[workspace_id].destroy()
                except:
                    pass
                del open_workspace_windows[workspace_id]
            refresh_workspaces()

    def open_workspace(workspace_id):
        if workspace_id in open_workspace_windows:
            window = open_workspace_windows[workspace_id]
            try:
                # Try to bring the window to front
                window.lift()
                window.focus_force()
            except tk.TclError:
                # If window was closed without removing from dict, re-open
                del open_workspace_windows[workspace_id]
                new_win = open_workspace_layout(workspace_id, email, master_win=win)
                open_workspace_windows[workspace_id] = new_win
        else:
            new_win = open_workspace_layout(workspace_id, email, master_win=win)
            open_workspace_windows[workspace_id] = new_win

    def refresh_workspaces():
        for widget in workspace_frame.winfo_children():
            widget.destroy()

        workspaces = db_handler.get_workspaces(user_id)
        for wid, name, is_default in workspaces:
            ws_data = db_handler.get_workspace_by_id(wid)
            theme = ws_data[1]
            icon = ws_data[2]

            card = tk.Frame(workspace_frame, bd=2, relief="groove", bg="white" if theme == "light" else "#222222")
            card.pack(padx=10, pady=10, fill="x")

            tk.Label(card, text=f"{icon}  {name}", font=("Arial", 16, "bold"),
                     bg=card["bg"], fg="black" if theme == "light" else "white").pack(anchor="w", padx=10, pady=5)

            btn_frame = tk.Frame(card, bg=card["bg"])
            btn_frame.pack(anchor="e", padx=10, pady=5)

            if not is_default:
                tk.Button(btn_frame, text="Set as Default", command=lambda i=wid: set_default(i)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Open", command=lambda i=wid: open_workspace(i)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Edit", command=lambda i=wid: edit_workspace(i)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Delete", command=lambda i=wid: delete_workspace(i)).pack(side="left", padx=5)

    def show_emoji_picker(callback):
        emoji_win = Toplevel(win)
        emoji_win.title("Choose an Emoji")
        emoji_win.geometry("300x150")
        emoji_win.grab_set()  # Modal

        def choose(e):
            callback(e)
            emoji_win.destroy()

        for idx, emoji in enumerate(EMOJIS):
            b = tk.Button(emoji_win, text=emoji, font=("Arial", 18), width=4, command=lambda e=emoji: choose(e))
            b.grid(row=idx // 5, column=idx % 5, padx=5, pady=5)

    def create_new_workspace():
        name = simpledialog.askstring("New Workspace", "Enter workspace name:", parent=win)
        if not name:
            return

        def on_emoji_selected(emoji):
            theme = simpledialog.askstring("Theme", "Enter theme: light or dark", parent=win)
            if theme not in ["light", "dark"]:
                theme = "light"
            db_handler.create_workspace(user_id, name, theme, emoji)
            refresh_workspaces()

        show_emoji_picker(on_emoji_selected)

    # === HEADER ===
    header = tk.Frame(win)
    header.pack(fill="x", pady=10, padx=20)

    tk.Label(header, text="Your Workspaces", font=("Arial", 24, "bold")).pack(side="left")

    right_buttons = tk.Frame(header)
    right_buttons.pack(side="right")

    tk.Button(right_buttons, text="Create New Workspace", command=create_new_workspace,
              bg="#4CAF50", fg="white").pack(side="left", padx=10)
    tk.Button(right_buttons, text="Logout", command=logout,
              bg="#f44336", fg="white").pack(side="left", padx=10)
    tk.Button(right_buttons, text="Exit Fullscreen", command=exit_fullscreen).pack(side="left")

    # === WORKSPACE AREA ===
    canvas = tk.Canvas(win)
    scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    workspace_frame = scroll_frame
    refresh_workspaces()

    win.mainloop()
