import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel
import db_handler
import ui_login
from ui_workspace_view import open_workspace_layout
from window_utils import center_window, _perform_centering_on_restore, on_configure, cleanup_window 

open_workspace_windows = {}

# Common emoji options
EMOJIS = ["📁", "📊", "🧾", "📈", "🗂️", "💼", "📋", "🧮", "📜", "🧠"]

def workspace_window(email):
    win = tk.Tk()
    win.title("Workspaces")
    win.attributes("-fullscreen", True)

    center_window(win)

    user_id = db_handler.get_user_id(email)

    default_workspace_id = db_handler.get_default_workspace_id(user_id)
    if default_workspace_id:
        # Hide the main workspace list window temporarily
        print(f"DEBUG: Default workspace ID found: {default_workspace_id}. Withdrawing main window.")
        win.withdraw()
        print("DEBUG: Scheduling default workspace to open.")
        win.after(100, lambda: open_workspace(default_workspace_id, master_win=win))
        print("DEBUG: Scheduled.")

    def exit_fullscreen():
        if win.winfo_exists(): # Check if main window still exists
            win.attributes("-fullscreen", False)
            win.wm_state('normal')
            win.geometry("800x800")
            center_window(win)

    def logout():
        if win.winfo_exists(): # Check if main window still exists before destroying
            cleanup_window(win)
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
        if not confirm:
            return

        db_handler.delete_workspace(workspace_id)
        
        # MODIFIED: Clean up the window if it's still open and remove from tracking
        if workspace_id in open_workspace_windows:
            try:
                # Only destroy if the window actually exists
                if open_workspace_windows[workspace_id].winfo_exists():
                    open_workspace_windows[workspace_id].destroy()
            except Exception as e:
                print(f"Error destroying workspace window {workspace_id}: {e}")
                pass # Window might have already been destroyed or other error
            del open_workspace_windows[workspace_id]
        
        refresh_workspaces()

    # MODIFIED FUNCTION: open_workspace to properly manage single instances
    def open_workspace(workspace_id, master_win):
        print(f"DEBUG: open_workspace called for ID: {workspace_id}")
        def workspace_close_callback(closed_workspace_id):
            print(f"DEBUG: Workspace close callback triggered for ID: {closed_workspace_id}")
            if closed_workspace_id in open_workspace_windows:
                print(f"DEBUG: Removing ID {closed_workspace_id} from tracking.")
                del open_workspace_windows[closed_workspace_id]
            # When a workspace window closes, ensure the master_win is brought back if it exists
            if master_win and master_win.winfo_exists():
                master_win.deiconify()
                master_win.lift()
                master_win.focus_force()

        # Check if a window for this workspace_id already exists and is still active
        if workspace_id in open_workspace_windows and open_workspace_windows[workspace_id].winfo_exists():
            print(f"DEBUG: Found existing window for ID {workspace_id}. Bringing to front.")
            window = open_workspace_windows[workspace_id]
            window.deiconify() # Ensure it's not minimized
            window.lift()
            window.focus_force()
            # If main window was withdrawn for default, bring it back
            if master_win and master_win.winfo_exists() and master_win.state() == 'withdrawn':
                 master_win.deiconify()
                 master_win.lift()
        else:
            print(f"DEBUG: Creating NEW window for ID {workspace_id}.")
            new_win = open_workspace_layout(workspace_id, email, master_win=master_win, on_close_callback=workspace_close_callback)
            open_workspace_windows[workspace_id] = new_win
            
            if master_win and master_win.winfo_exists() and master_win.state() == 'withdrawn':
                 master_win.deiconify()
                 master_win.lift()


    def refresh_workspaces():
        if not win.winfo_exists(): 
            return
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

            if is_default:
                default_label = tk.Label(btn_frame, text="Default", font=("Arial", 10, "italic","bold"),
                                        bg=btn_frame["bg"], fg="white")
                default_label.pack(side="left", padx=5) 
            if not is_default:
                tk.Button(btn_frame, text="Set as Default", command=lambda i=wid: set_default(i)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Open", command=lambda i=wid: open_workspace(i, master_win=win)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Edit", command=lambda i=wid: edit_workspace(i)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Delete", command=lambda i=wid: delete_workspace(i)).pack(side="left", padx=5)

    def show_emoji_picker(callback):
        if not win.winfo_exists(): # Don't show picker if main window is destroyed
            return
        emoji_win = Toplevel(win)
        emoji_win.title("Choose an Emoji")
        emoji_win.geometry("400x150")
        emoji_win.grab_set()  # Modal

        def choose(e):
            callback(e)
            emoji_win.destroy()

        for idx, emoji in enumerate(EMOJIS):
            b = tk.Button(emoji_win, text=emoji, font=("Arial", 18), width=4, command=lambda e=emoji: choose(e))
            b.grid(row=idx // 5, column=idx % 5, padx=5, pady=5)

    def create_new_workspace():
        if not win.winfo_exists(): # Don't create if main window is destroyed
            return
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
    scroll_frame.pack(fill="both", expand=True)

    workspace_frame = scroll_frame
    refresh_workspaces()

    win.mainloop()