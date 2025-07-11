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

    # MODIFIED: edit_workspace function
    def edit_workspace(workspace_id):
        ws_data = db_handler.get_workspace_by_id(workspace_id)
        if not ws_data:
            messagebox.showerror("Error", "Workspace not found.")
            return

        current_name, current_theme, current_emoji = ws_data[0], ws_data[1], ws_data[2]

        # Call the new consolidated popup for editing
        open_edit_workspace_popup(win, workspace_id, current_name, current_theme, current_emoji, refresh_workspaces)

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

        if workspace_id in open_workspace_windows:
            existing_win = open_workspace_windows[workspace_id]
            if existing_win.winfo_exists():
                print(f"DEBUG: Reusing window for workspace ID {workspace_id}")
                existing_win.deiconify()
                existing_win.lift()
                existing_win.focus_force()
                return
            else:
                print(f"DEBUG: Window reference existed but was invalid. Removing it.")
                del open_workspace_windows[workspace_id]

        def workspace_close_callback(closed_workspace_id):
            print(f"DEBUG: Workspace close callback triggered for ID: {closed_workspace_id}")
            if closed_workspace_id in open_workspace_windows:
                try:
                    win = open_workspace_windows.pop(closed_workspace_id, None)
                    if win and win.winfo_exists():
                        print(f"DEBUG: Destroying window for ID: {closed_workspace_id}")
                        win.destroy()
                except Exception as e:
                    print(f"DEBUG: Exception during destroy: {e}")

        new_win = open_workspace_layout(
            workspace_id=workspace_id,
            email=email,
            master_win=master_win,
            on_close_callback=workspace_close_callback
        )
        open_workspace_windows[workspace_id] = new_win
        # new_win.protocol("WM_DELETE_WINDOW", lambda: workspace_close_callback(workspace_id))
        new_win.deiconify()
        new_win.lift()
        new_win.focus_force()

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

            display_text = f"{icon}  {name}"
            tk.Label(card, text=display_text, font=("Arial", 16, "bold"),
                     bg=card["bg"], fg="black" if theme == "light" else "white").pack(anchor="w", padx=10, pady=5)

            btn_frame = tk.Frame(card, bg=card["bg"])
            btn_frame.pack(anchor="e", padx=10, pady=5)

            if is_default:
                default_label = tk.Label(btn_frame, text="Default", font=("Arial", 10, "italic","bold"),
                                         bg=btn_frame["bg"], fg="grey")
                default_label.pack(side="left", padx=5) 
            if not is_default:
                tk.Button(btn_frame, text="Set as Default", command=lambda i=wid: set_default(i)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Open", command=lambda i=wid: open_workspace(i, master_win=win)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Edit", command=lambda i=wid: edit_workspace(i)).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Delete", command=lambda i=wid: delete_workspace(i)).pack(side="left", padx=5)
            
    # NEW FUNCTION: Consolidated popup for creating a new workspace
    def open_create_workspace_popup(parent_win, user_id, refresh_callback):
        popup = tk.Toplevel(parent_win)
        popup.title("Create New Workspace")
        popup.transient(parent_win) # Makes popup appear on top of parent
        popup.grab_set()  
        popup.geometry("500x350")      # Makes it modal
        center_window(popup)        # Center the popup

        # Variables to hold user input
        name_var = tk.StringVar(value="")
        emoji_var = tk.StringVar(value=EMOJIS[0]) # Default to first emoji
        theme_var = tk.StringVar(value="light") # Default to light theme

        # --- Workspace Name ---
        tk.Label(popup, text="Workspace Name:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        name_entry = tk.Entry(popup, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus_set() # Set focus

        # --- Emoji Picker ---
        tk.Label(popup, text="Choose Emoji:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        emoji_frame = tk.Frame(popup)
        emoji_frame.pack(pady=5)

        emoji_buttons = {} # To keep track of emoji buttons for highlighting
        def select_emoji_button(selected_emoji):
            for emoji, btn in emoji_buttons.items():
                if emoji == selected_emoji:
                    btn.config(relief="sunken", bd=2) # Highlight selected
                else:
                    btn.config(relief="raised", bd=1) # Unhighlight others
            emoji_var.set(selected_emoji)

        for idx, emoji in enumerate(EMOJIS):
            b = tk.Button(emoji_frame, text=emoji, font=("Arial", 14), width=3,
                          command=lambda e=emoji: select_emoji_button(e))
            b.grid(row=idx // 5, column=idx % 5, padx=2, pady=2)
            emoji_buttons[emoji] = b # Store button reference

        # --- Theme Selector ---
        tk.Label(popup, text="Choose Theme:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        theme_frame = tk.Frame(popup)
        theme_frame.pack(pady=5)

        tk.Radiobutton(theme_frame, text="Light", variable=theme_var, value="light",
                       font=("Arial", 10)).pack(side="left", padx=5)
        tk.Radiobutton(theme_frame, text="Dark", variable=theme_var, value="dark",
                       font=("Arial", 10)).pack(side="left", padx=5)

        # --- Action Buttons ---
        def create_action():
            name = name_var.get().strip()
            emoji = emoji_var.get()
            theme = theme_var.get()

            if not name:
                messagebox.showerror("Error", "Workspace name cannot be empty.", parent=popup)
                return
            if not emoji:
                messagebox.showerror("Error", "Please select an emoji.", parent=popup)
                return

            try:
                db_handler.create_workspace(user_id, name, theme, emoji)
                messagebox.showinfo("Success", f"Workspace '{name}' created!", parent=popup)
                popup.destroy()
                refresh_callback() # Refresh the main workspace list
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create workspace: {e}", parent=popup)

        def cancel_action():
            popup.destroy()

        button_frame = tk.Frame(popup)
        button_frame.pack(pady=15)

        tk.Button(button_frame, text="Create", command=create_action,
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=cancel_action,
                  bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)

        popup.wait_window(popup) # Wait for the popup to close before returning control

    # NEW FUNCTION: Consolidated popup for editing an existing workspace
    def open_edit_workspace_popup(parent_win, workspace_id, initial_name, initial_theme, initial_emoji, refresh_callback):
        popup = tk.Toplevel(parent_win)
        popup.title(f"Edit Workspace: {initial_name}")
        popup.transient(parent_win) # Makes popup appear on top of parent
        popup.grab_set()            # Makes it modal
        popup.geometry("500x350")   # Set a consistent size
        center_window(popup)        # Center the popup

        # Variables to hold user input, pre-filled with current data
        name_var = tk.StringVar(value=initial_name)
        emoji_var = tk.StringVar(value=initial_emoji)
        theme_var = tk.StringVar(value=initial_theme)

        # --- Workspace Name ---
        tk.Label(popup, text="Workspace Name:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        name_entry = tk.Entry(popup, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus_set() # Set focus to the name entry

        # --- Emoji Picker ---
        tk.Label(popup, text="Choose Emoji:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        emoji_frame = tk.Frame(popup)
        emoji_frame.pack(pady=5)

        emoji_buttons = {} # To keep track of emoji buttons for highlighting
        def select_emoji_button(selected_emoji):
            for emoji, btn in emoji_buttons.items():
                if emoji == selected_emoji:
                    btn.config(relief="sunken", bd=2) # Highlight selected
                else:
                    btn.config(relief="raised", bd=1) # Unhighlight others
            emoji_var.set(selected_emoji)

        for idx, emoji in enumerate(EMOJIS):
            b = tk.Button(emoji_frame, text=emoji, font=("Arial", 14), width=3,
                          command=lambda e=emoji: select_emoji_button(e))
            b.grid(row=idx // 5, column=idx % 5, padx=2, pady=2)
            emoji_buttons[emoji] = b # Store button reference

        # Select the initial emoji visually
        select_emoji_button(initial_emoji)

        # --- Theme Selector ---
        tk.Label(popup, text="Choose Theme:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        theme_frame = tk.Frame(popup)
        theme_frame.pack(pady=5)

        tk.Radiobutton(theme_frame, text="Light", variable=theme_var, value="light",
                       font=("Arial", 10)).pack(side="left", padx=5)
        tk.Radiobutton(theme_frame, text="Dark", variable=theme_var, value="dark",
                       font=("Arial", 10)).pack(side="left", padx=5)

        # --- Action Buttons ---
        def save_action():
            new_name = name_var.get().strip()
            new_emoji = emoji_var.get()
            new_theme = theme_var.get()

            if not new_name:
                messagebox.showerror("Error", "Workspace name cannot be empty.", parent=popup)
                return
            if not new_emoji:
                messagebox.showerror("Error", "Please select an emoji.", parent=popup)
                return

            try:
                db_handler.update_workspace(workspace_id, new_name, new_theme, new_emoji)
                messagebox.showinfo("Success", f"Workspace '{new_name}' updated!", parent=popup)
                popup.destroy()
                refresh_callback() # Refresh the main workspace list
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update workspace: {e}", parent=popup)

        def cancel_action():
            popup.destroy()

        button_frame = tk.Frame(popup)
        button_frame.pack(pady=15)

        tk.Button(button_frame, text="Save Changes", command=save_action,
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=cancel_action,
                  bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)

        popup.wait_window(popup) # Wait for the popup to close before returning control

    def create_new_workspace():
        if not win.winfo_exists(): # Don't create if main window is destroyed
            return
        # Call the new consolidated popup
        open_create_workspace_popup(win, user_id, refresh_workspaces) # Pass win, user_id, and refresh_workspaces

    # === HEADER ===
    header = tk.Frame(win)
    header.pack(fill="x", pady=10, padx=20)

    tk.Label(header, text="Your Workspaces", font=("Arial", 24, "bold")).pack(side="left")

    right_buttons = tk.Frame(header)
    right_buttons.pack(side="right")
    
    # --- Button Colors ---
    CREATE_NORMAL_BG = "#4CAF50"
    CREATE_HOVER_BG = "#45a049"
    CREATE_OUTLINE_COLOR = "#3d8b40" # A darker green for the outline

    LOGOUT_NORMAL_BG = "#f44336"
    LOGOUT_HOVER_BG = "#da190b"
    LOGOUT_OUTLINE_COLOR = "#c2322a" # A darker red for the outline

    EXIT_NORMAL_BG = "#BBB5B5"
    EXIT_HOVER_BG = "#9C9898"
    EXIT_OUTLINE_COLOR = "#808080"  # A medium grey for the outline of the neutral button

    # Enhanced 'Create New Workspace' Button
    create_btn = tk.Button(right_buttons,
                           text="Create New Workspace",
                           command=create_new_workspace,
                           bg=CREATE_NORMAL_BG,
                           fg="white",
                           font=("Arial", 12, "bold"),
                           relief="flat",            # Set back to flat to allow highlight to show as outline
                           borderwidth=0,            # No default border
                           highlightthickness=2,     # Thickness of the outline
                           highlightbackground=CREATE_OUTLINE_COLOR, # Color of outline when not focused
                           highlightcolor=CREATE_OUTLINE_COLOR,      # Color of outline when focused
                           cursor="hand2"
                          )
    create_btn.pack(side="left", padx=10)
    create_btn.bind("<Enter>", lambda e: create_btn.config(bg=CREATE_HOVER_BG))
    create_btn.bind("<Leave>", lambda e: create_btn.config(bg=CREATE_NORMAL_BG))

    # Enhanced 'Logout' Button
    logout_btn = tk.Button(right_buttons,
                          text="Logout",
                          command=logout,
                          bg=LOGOUT_NORMAL_BG,
                          fg="white",
                          font=("Arial", 12, "bold"),
                          relief="flat",
                          borderwidth=0,
                          highlightthickness=2,
                          highlightbackground=LOGOUT_OUTLINE_COLOR,
                          highlightcolor=LOGOUT_OUTLINE_COLOR,
                          cursor="hand2"
                         )
    logout_btn.pack(side="left", padx=10)
    logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg=LOGOUT_HOVER_BG))
    logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg=LOGOUT_NORMAL_BG))

    # Enhanced 'Exit Fullscreen' Button
    exit_btn = tk.Button(right_buttons,
                          text="Exit Fullscreen",
                          command=exit_fullscreen,
                          bg=EXIT_NORMAL_BG,
                          fg="white",
                          font=("Arial", 12, "bold"),
                          relief="flat",
                          borderwidth=0,
                          highlightthickness=2,
                          highlightbackground=EXIT_OUTLINE_COLOR,
                          highlightcolor=EXIT_OUTLINE_COLOR,
                          cursor="hand2"
                         )
    exit_btn.pack(side="left", padx=10)
    exit_btn.bind("<Enter>", lambda e: exit_btn.config(bg=EXIT_HOVER_BG))
    exit_btn.bind("<Leave>", lambda e: exit_btn.config(bg=EXIT_NORMAL_BG))

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