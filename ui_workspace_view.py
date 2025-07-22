import tkinter as tk
from tkinter import ttk, messagebox
import db_handler
import json
from instrument_pop import select_instrument
# from functools import partial
from tcp_utils import send_tcp_command
import threading
from tkinter.filedialog import asksaveasfilename, askopenfilename
from window_utils import center_window, on_configure, cleanup_window 
import config

def get_next_session_id():
    session_id = config.GLOBAL_SESSION_COUNTER
    config.GLOBAL_SESSION_COUNTER += 1

    return session_id

# Constants
TABLE_ACTIONS = ["Export Schema", "Import Schema", "Export Table", "Import Table", "Set Default", "New Table", "Edit Table", "Add Row", "Start All", "Stop All"]

# Entry point
def create_validator(data_type):
    def validate(P):
        if data_type == "INTEGER":
            return P == "" or P.isdigit()
        elif data_type == "FLOAT":
            try:
                float(P)
                return True
            except ValueError:
                return P == ""  # Allow empty
        return True  # TEXT allows anything
    return validate

# Function to create a new table schema
def open_create_table_popup(parent, workspace_id, user_id, refresh_callback):
    popup = tk.Toplevel(parent)
    popup.title("Create New Table Schema")
    popup.geometry("600x500")

    tk.Label(popup, text="\u26A0 Column Name Guidelines:", font=("Arial", 10, "bold"), fg="darkred").pack(anchor="w", padx=10)
    tk.Label(popup, text="- Avoid spaces (use underscores)\n- Avoid special characters\n- Use uppercase\n- STATUS will be added automatically",
             justify="left", font=("Arial", 9)).pack(anchor="w", padx=20)

    tk.Label(popup, text="Table Name:").pack(anchor="w", padx=10, pady=(10, 0))
    table_name_entry = tk.Entry(popup)
    table_name_entry.pack(fill="x", padx=10)

    columns_frame = tk.Frame(popup, bd=2, relief="sunken")
    columns_frame.pack(padx=10, pady=10, fill="both", expand=True)

    column_entries = []

    header_frame = tk.Frame(columns_frame)
    header_frame.pack(fill="x", pady=2)

    # Adjusted widths and padding for better alignment with the image
    tk.Label(header_frame, text="Column Name", font=("Arial", 9, "bold"), width=15).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Type", font=("Arial", 9, "bold"), width=8).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Default Value", font=("Arial", 9, "bold"), width=15).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Editable", font=("Arial", 9, "bold"), width=7).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Subscription", font=("Arial", 9, "bold"), width=10).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Remove", font=("Arial", 9, "bold"), width=7, anchor="w").pack(side="left", padx=5)

    def add_column():
        row = tk.Frame(columns_frame)
        row.pack(fill="x", pady=2)

        # --- Column Name Entry with Placeholder ---
        name = tk.Entry(row, width=15, fg="gray")
        name.insert(0, "Column name")
        name.pack(side="left", padx=5)
        def on_focus_in_name(event):
            if name.get() == "Column name":
                name.delete(0, tk.END)
                name.config(fg="black")
        def on_focus_out_name(event):
            if name.get() == "":
                name.insert(0, "Column name")
                name.config(fg="gray")
        name.bind("<FocusIn>", on_focus_in_name)
        name.bind("<FocusOut>", on_focus_out_name)

        # --- Type Dropdown ---
        dtype = ttk.Combobox(row, values=["INTEGER", "FLOAT", "TEXT"], width=10)
        dtype.set("INTEGER")
        dtype.pack(side="left", padx=5)

        # --- Default Value Entry with Placeholder ---
        default = tk.Entry(row, width=15, fg="gray")
        default.insert(0, "Default value")
        default.pack(side="left", padx=5)
        def on_focus_in_def(event):
            if default.get() == "Default value":
                default.delete(0, tk.END)
                default.config(fg="black")
        def on_focus_out_def(event):
            if default.get() == "":
                default.insert(0, "Default value")
                default.config(fg="gray")
        default.bind("<FocusIn>", on_focus_in_def)
        default.bind("<FocusOut>", on_focus_out_def)

        # --- Editable Checkbox with Label ---
        editable = tk.IntVar()
        edit_frame = tk.Frame(row)
        edit_check = tk.Checkbutton(edit_frame, variable=editable) # Removed text="Editable"
        edit_check.pack(padx=25) # Add padx to center the checkbox within its frame
        edit_frame.pack(side="left", padx=5)

        subscription = tk.IntVar()
        sub_frame = tk.Frame(row)
        sub_check = tk.Checkbutton(sub_frame, variable=subscription)
        sub_check.pack(padx=25)  # Add padx to center the checkbox within its frame
        sub_frame.pack(side="left", padx=5)

        # --- Remove Button ---
        del_btn = tk.Button(row, text="🗑", command=lambda: remove_column(row), relief="flat",font=(10))
        del_btn.pack(side="left")

        column_entries.append((name, dtype, default, editable, subscription))

    def remove_column(row):
        for i, (n, t, d, e) in enumerate(column_entries):
            if n.master == row:
                column_entries.pop(i)
                break
        row.destroy()

    add_column()

    def create_table():
        table_name = table_name_entry.get().strip().upper()
        if not table_name:
            messagebox.showerror("Error", "Table name is required")
            return

        schema = []
        for name, dtype, default, editable, subscription in column_entries:
            col_name = name.get().strip().upper()
            col_type = dtype.get()
            col_default = default.get().strip()
            is_editable = bool(editable.get())
            is_subscription = bool(subscription.get())

            if not col_name:
                messagebox.showerror("Error", "Column name is required")
                return

            schema.append({
                "name": col_name,
                "type": col_type,
                "default": col_default,
                "editable": is_editable,
                "subscription": is_subscription
            })

        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        # Create physical table name
        physical_table_name = f"user_{user_id}_ws_{workspace_id}_{table_name}".replace(" ", "_")

        # Create physical table SQL
        column_defs = ['"ID" TEXT', '"STRATEGY" TEXT', '"TABLE" TEXT', '"STATUS" TEXT', '"InstrumentToken" TEXT', '"InstrumentID" TEXT', '"InstrumentName" TEXT']
        for col in schema:
            column_defs.append(f'"{col["name"]}" {col["type"]}')

        create_sql = f"CREATE TABLE IF NOT EXISTS {physical_table_name} ({', '.join(column_defs)})"
        cur.execute(create_sql)

        # Save the table schema and metadata
        cur.execute("""
            INSERT INTO user_tables (user_id, workspace_id, table_name, schema, physical_table_name, is_default)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (user_id, workspace_id, table_name, json.dumps(schema), physical_table_name))

        conn.commit()
        conn.close()

        popup.destroy()
        refresh_callback()

    tk.Button(popup, text="Add Column", command=add_column).pack(pady=5)
    tk.Button(popup, text="Create Table", command=create_table, bg="green", fg="white", font=("Arial", 12, "bold")).pack(pady=10)

# Function to edit table schema
def open_edit_table_popup(parent, workspace_id, user_id, old_table_name, refresh_callback):
    conn = db_handler.sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT schema FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                (user_id, workspace_id, old_table_name))
    result = cur.fetchone()

    if not result:
        conn.close()
        messagebox.showerror("Error", "Table not found.")
        return

    schema_data = json.loads(result[0])
    conn.close()

    popup = tk.Toplevel(parent)
    popup.title(f"Edit Table - {old_table_name}")
    popup.geometry("600x500")

    tk.Label(popup, text="\u26A0 Column Name Guidelines:", font=("Arial", 10, "bold"), fg="darkred").pack(anchor="w", padx=10)
    tk.Label(popup, text="- Avoid spaces (use underscores)\n- Avoid special characters\n- Use uppercase\n- STATUS will be added automatically",
             justify="left", font=("Arial", 9)).pack(anchor="w", padx=20)

    tk.Label(popup, text="Table Name:").pack(anchor="w", padx=10, pady=(10, 0))
    table_name_entry = tk.Entry(popup)
    table_name_entry.pack(fill="x", padx=10)
    table_name_entry.insert(0, old_table_name)

    columns_frame = tk.Frame(popup, bd=2, relief="sunken")
    columns_frame.pack(padx=10, pady=10, fill="both", expand=True)

    column_entries = []

    header_frame = tk.Frame(columns_frame)
    header_frame.pack(fill="x", pady=2)

    # Adjusted widths and padding for better alignment with the image
    tk.Label(header_frame, text="Column Name", font=("Arial", 9, "bold"), width=15).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Type", font=("Arial", 9, "bold"), width=8).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Default Value", font=("Arial", 9, "bold"), width=15).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Editable", font=("Arial", 9, "bold"), width=7).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Subscription", font=("Arial", 9, "bold"), width=10).pack(side="left", padx=5, anchor="w")
    tk.Label(header_frame, text="Remove", font=("Arial", 9, "bold"), width=7, anchor="w").pack(side="left", padx=5)

    def add_column_with_values(col_name="", col_type="INTEGER", col_default="", col_editable=False, col_subscription=False):
        row = tk.Frame(columns_frame)
        row.pack(fill="x", pady=2)

        name = tk.Entry(row, width=15)
        name.insert(0, col_name)
        name.pack(side="left", padx=5)

        dtype = ttk.Combobox(row, values=["INTEGER", "FLOAT", "TEXT"], width=10)
        dtype.set(col_type)
        dtype.pack(side="left", padx=5)

        default = tk.Entry(row, width=15)
        default.insert(0, col_default)
        default.pack(side="left", padx=5)

        editable = tk.IntVar(value=1 if col_editable else 0)
        edit_frame = tk.Frame(row)
        edit_check = tk.Checkbutton(edit_frame, variable=editable) # Removed text="Editable"
        edit_check.pack(padx=25) # Add padx to center the checkbox within its frame
        edit_frame.pack(side="left", padx=5)

        subscription = tk.IntVar(value=1 if col_subscription else 0)
        sub_frame = tk.Frame(row)
        sub_check = tk.Checkbutton(sub_frame, variable=subscription)
        sub_check.pack(padx=25)  # Add padx to center the checkbox within its frame
        sub_frame.pack(side="left", padx=5)

        del_btn = tk.Button(row, text="🗑", command=lambda: remove_column(row), relief="flat",font=(10))
        del_btn.pack(side="left")

        column_entries.append((name, dtype, default, editable, subscription))

    def remove_column(row):
        for i, (n, t, d, e) in enumerate(column_entries):
            if n.master == row:
                column_entries.pop(i)
                break
        row.destroy()

    for col in schema_data:
        add_column_with_values(
            col_name=col["name"],
            col_type=col["type"],
            col_default=col["default"],
            col_editable=col["editable"],
            col_subscription=col["subscription"]
        )

    tk.Button(popup, text="Add Column", command=lambda: add_column_with_values()).pack(pady=5)

    def save_changes():
        new_table_name = table_name_entry.get().strip().upper()
        if not new_table_name:
            messagebox.showerror("Error", "Table name cannot be empty.")
            return

        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()

        # Check for name conflict if name is changed
        if new_table_name != old_table_name:
            cur.execute("SELECT 1 FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                        (user_id, workspace_id, new_table_name))
            if cur.fetchone():
                conn.close()
                messagebox.showerror("Error", "A table with this name already exists.")
                return

        # Collect updated schema
        new_schema = []
        for name, dtype, default, editable, subscription in column_entries:
            col_name = name.get().strip().upper()
            col_type = dtype.get()
            col_default = default.get().strip()
            is_editable = bool(editable.get())
            is_subscription = bool(subscription.get())

            if not col_name:
                messagebox.showerror("Error", "Column name cannot be empty.")
                return

            new_schema.append({
                "name": col_name,
                "type": col_type,
                "default": col_default,
                "editable": is_editable,
                "subscription" : is_subscription
            })

        # Fetch current schema and physical table name
        cur.execute("SELECT schema, physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, old_table_name))
        old_schema_json, physical_table = cur.fetchone()
        old_schema = json.loads(old_schema_json)
        old_col_names = {col['name'] for col in old_schema}
        new_col_names = {col['name'] for col in new_schema}

        # Detect dropped columns
        dropped_cols = old_col_names - new_col_names
        added_cols = new_col_names - old_col_names

        # Recreate table if any column is dropped
        if dropped_cols:
            print(f"⚠️ Rebuilding table {physical_table} due to dropped columns: {dropped_cols}")

            # Build list of columns to keep (system + user)
            system_cols = ["ID", "STRATEGY", "TABLE", "STATUS", "InstrumentToken", "InstrumentID", "InstrumentName"]
            preserved_cols = system_cols + [col['name'] for col in new_schema]

            temp_table = f"{physical_table}_temp"

            # 1. Rename old table
            cur.execute(f'ALTER TABLE "{physical_table}" RENAME TO "{temp_table}"')

            # 2. Create new table with updated schema
            column_defs = [f'"{col}" TEXT' for col in system_cols] + \
                        [f'"{col["name"]}" {col["type"]}' for col in new_schema]
            cur.execute(f'CREATE TABLE "{physical_table}" ({", ".join(column_defs)})')

            # 3. Copy common columns from temp to new table
            common_cols = [col for col in preserved_cols if col not in dropped_cols]
            common_cols_sql = ", ".join(f'"{col}"' for col in common_cols)
            cur.execute(f'INSERT INTO "{physical_table}" ({common_cols_sql}) SELECT {common_cols_sql} FROM "{temp_table}"')

            # 4. Drop temp table
            cur.execute(f'DROP TABLE "{temp_table}"')

        # Add any newly added columns (for safety)
        for col in new_schema:
            if col["name"] in added_cols:
                try:
                    cur.execute(f'ALTER TABLE "{physical_table}" ADD COLUMN "{col["name"]}" {col["type"]}')
                except Exception as e:
                    print(f"⚠️ Column already exists: {col['name']}, skipping...")

                # Set default value for all existing rows
                if col["default"] != "":
                    cur.execute(f'UPDATE "{physical_table}" SET "{col["name"]}" = ? WHERE "{col["name"]}" IS NULL',
                                (col["default"],))

        # Update table metadata
        cur.execute("UPDATE user_tables SET table_name=?, schema=? WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (new_table_name, json.dumps(new_schema), user_id, workspace_id, old_table_name))

        conn.commit()
        conn.close()

        popup.destroy()
        refresh_callback()

    def delete_table():
        confirm = messagebox.askyesno("Delete Table", f"Are you sure you want to delete '{old_table_name}'?")
        if not confirm:
            return

        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        # Fetch physical table name
        cur.execute("SELECT physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, old_table_name))
        row = cur.fetchone()
        if row:
            physical_table = row[0]
            cur.execute(f'DROP TABLE IF EXISTS "{physical_table}"')
        cur.execute("DELETE FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, old_table_name))
        conn.commit()
        conn.close()
        popup.destroy()
        refresh_callback()

    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Save Changes", command=save_changes, bg="blue", fg="white").pack(side="left", padx=5)
    tk.Button(btn_frame, text="Delete Table", command=delete_table, bg="red", fg="white").pack(side="left", padx=5)

#Function to handle add row functionality in the table
def handle_add_row(user_id, workspace_id, table_name, refresh_callback):
    def after_instrument_selected(name, symbol, token):
        # Fetch existing table schema
        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT schema, physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, table_name))
        result = cur.fetchone()
        if not result:
            conn.close()
            messagebox.showerror("Error", "Table not found.")
            return

        schema = json.loads(result[0])
        physical_table = result[1]

        next_id = get_next_session_id()
        print("The next global user-based ID is:", next_id)

        # Create new row with the unique ID
        new_row = {
            "ID": str(next_id),  # Use the newly generated unique ID
            "Strategy": f"{table_name}_{next_id}", # Update Strategy to use the new unique ID
            "Table": table_name.upper(),
            "STATUS": "INACTIVE",
            "InstrumentToken": str(token),
            "InstrumentID": symbol,
            "InstrumentName": name,
        }

        # Add user-defined columns with defaults
        for col in schema:
            if col["name"] not in new_row:
                new_row[col["name"]] = col["default"]

        # Build insert SQL
        columns = list(new_row.keys())
        placeholders = ",".join("?" for _ in columns)
        # It's good practice to quote column names to avoid issues with reserved keywords
        quoted_columns = ', '.join(f'"{col}"' for col in columns)
        insert_sql = f"INSERT INTO {physical_table} ({quoted_columns}) VALUES ({placeholders})"
        
        try:
            cur.execute(insert_sql, [new_row[col] for col in columns])
            conn.commit()
            messagebox.showinfo("Success", "Row added successfully!")
            # This line ensures you stay on the correct table after adding a row
            refresh_callback(table_name)
        except db_handler.sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to add row: {e}")
        finally:
            conn.close()

    # Open instrument selection popup
    select_instrument(after_instrument_selected)

def open_workspace_layout(workspace_id, email, master_win=None, on_close_callback=None):

    user_id = db_handler.get_user_id(email)
    workspace = db_handler.get_workspace_by_id(workspace_id)
    entry_widgets_by_row_id = {}
    name, theme, icon = workspace

    bg_color = "#ffffff" if theme == "light" else "#111111"
    fg_color = "black" if theme == "light" else "white"

    win = tk.Toplevel(master=master_win)
    win.title(name)
    win.attributes("-fullscreen", True)

    center_window(win)

    win.configure(bg=bg_color)

    # MODIFIED: on_workspace_close now calls the provided callback
    def on_workspace_close():
        print("🔒 Attempting to close workspace...")
        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT table_name, physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=?", (user_id, workspace_id))
        tables = cur.fetchall()

        active_tables = []
        for logical_name, physical_name in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {physical_name} WHERE UPPER(STATUS)='ACTIVE'")
                count = cur.fetchone()[0]
                print(f"Table {logical_name} has {count} active strategies")
                if count > 0:
                    active_tables.append(logical_name)
            except Exception as e:
                print(f"❌ Failed to check {physical_name}: {e}")
                continue

        conn.close()

        if active_tables:
            table_list = ", ".join(active_tables)
            messagebox.showwarning("Active Strategies",
                f"❗ Please terminate your running strategies in the following table(s) before closing:\n\n{table_list}")
            return  # Don't close

        print("✅ No active strategies. Closing workspace.")
        if on_close_callback:
            on_close_callback(workspace_id)

        cleanup_window(win)
        win.destroy()
        if master_win:
            master_win.deiconify()
            master_win.lift()
            master_win.focus_force()

    win.protocol("WM_DELETE_WINDOW", on_workspace_close) # Handle window closing via 'X' button

    def exit_fullscreen():
        win.attributes("-fullscreen", False)
        win.wm_state('normal')
        win.geometry("800x600")
        center_window(win)

    # === HEADER ===
    header = tk.Frame(win, bg=bg_color)
    header.pack(fill="x", padx=20, pady=10)
    tk.Label(header, text=f"Workspace: {icon} {name}", font=("Arial", 24, "bold"), bg=bg_color, fg=fg_color).pack(side="left")

    table_frame = tk.Frame(win, bg=bg_color)
    table_frame.pack(fill="x", padx=20, pady=5)

    # Dropdown for tables
    tk.Label(table_frame, text="PF Group:", bg=bg_color, fg=fg_color).pack(side="left")
    table_var = tk.StringVar()
    table_dropdown = ttk.Combobox(table_frame, textvariable=table_var)
    table_dropdown.pack(side="left", padx=5)
    table_dropdown.bind("<<ComboboxSelected>>", lambda e: update_table_display(table_var.get()))

    action_btns = tk.Frame(table_frame, bg=bg_color)
    action_btns.pack(side="right")

    content_frame = tk.Frame(win, bg=bg_color)
    content_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def update_row_ui_waiting(row_id):
        widgets = entry_widgets_by_row_id.get(row_id)
        if widgets:
            if "STATUS" in widgets:
                widgets["STATUS"].config(state='normal')
                widgets["STATUS"].delete(0, tk.END)
                widgets["STATUS"].insert(0, "WAITING")
                widgets["STATUS"].config(state='readonly', background="#fcd34d")  # Yellow color for waiting
            if "ID" in widgets:
                widgets["ID"].config(state='normal', background="#fcd34d") 
                widgets["ID"].config(state='readonly')
            if "SELECTED" in widgets:
                widgets["SELECTED"].set(1)
            if "CHECKBOX_WIDGET" in widgets: # <--- ADD THIS BLOCK
                widgets["CHECKBOX_WIDGET"].config(bg=bg_color)

    def update_row_ui_active(row_id):
            widgets = entry_widgets_by_row_id.get(row_id)
            if widgets:
                if "STATUS" in widgets:
                    widgets["STATUS"].config(state='normal')
                    widgets["STATUS"].delete(0, tk.END)
                    widgets["STATUS"].insert(0, "ACTIVE")
                    widgets["STATUS"].config(state='readonly', background="#c7f9cc")
                if "ID" in widgets:
                    widgets["ID"].config(state='normal')
                    widgets["ID"].config(readonlybackground="#c7f9cc")
                    widgets["ID"].config(state='readonly')
                if "SELECTED" in widgets:
                    widgets["SELECTED"].set(1)
                if "CHECKBOX_WIDGET" in widgets:
                    widgets["CHECKBOX_WIDGET"].config(bg="#c7f9cc")
                if "apply_btn" in widgets:
                    widgets["apply_btn"].config(state="disabled", text="Applied", bg="black", fg="white")
                if "delete_btn" in widgets:
                    widgets["delete_btn"].config(state="disabled")
                if "stop_btn" in widgets:
                    widgets["stop_btn"].config(state="normal", text="Stop", bg="black", fg="white")

    def update_row_ui_inactive(row_id):
        widgets = entry_widgets_by_row_id.get(row_id)
        if widgets:
            if "STATUS" in widgets:
                widgets["STATUS"].config(state='normal')
                widgets["STATUS"].delete(0, tk.END)
                widgets["STATUS"].insert(0, "INACTIVE")
                widgets["STATUS"].config(state='readonly', background="white")  # Set background to white
            if "ID" in widgets:
                widgets["ID"].config(state='normal')
                widgets["ID"].config(readonlybackground="white")  # Set background to white
                widgets["ID"].config(state='readonly')
            if "SELECTED" in widgets:
                widgets["SELECTED"].set(0)  # Deselect if needed
            if "CHECKBOX_WIDGET" in widgets: 
                row_index = int(widgets["CHECKBOX_WIDGET"].grid_info()["row"])
                original_row_bg = "#f9fafb" if row_index % 2 == 0 else "#e5e7eb"
                widgets["CHECKBOX_WIDGET"].config(bg=original_row_bg, activebackground=original_row_bg)
            if "apply_btn" in widgets:
                widgets["apply_btn"].config(state="normal", text="Apply", bg="black", fg="white")
            if "delete_btn" in widgets:
                widgets["delete_btn"].config(state="normal")
            if "stop_btn" in widgets:
                widgets["stop_btn"].config(state="disabled", text="Stopped", bg="black", fg="white")

    def handle_start_all():
        table_name = table_var.get()
        if not table_name:
            messagebox.showerror("Error", "No table selected.")
            return

        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT schema, physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, table_name))
        result = cur.fetchone()
        if not result:
            messagebox.showerror("Error", "Table not found.")
            return

        schema = json.loads(result[0])
        physical_table = result[1]

        cur.execute(f"SELECT * FROM {physical_table}")
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        conn.close()

        total = len(rows)
        done = [0]  # mutable counter

        # Loop through each row and update it to 'WAITING'
        for row in rows:
            row_id = row[col_names.index("ID")]  # Assuming "ID" is the first column in schema
            status_value = row[col_names.index("STATUS")].upper()

            # Call the update_row_ui_waiting before sending the command
            if status_value != "ACTIVE":
                update_row_ui_waiting(row_id)

            data = dict(zip(col_names, row))
            data.update({
                "strategy_name": data.get("STRATEGY", ""),
                "table_type": data.get("TABLE", "").lower(),
                "instrument_id": data.get("InstrumentID", ""),
                "instrument_name": data.get("InstrumentName", ""),
                "status": data.get("STATUS", ""),
                "user_id": user_id,
                "workspace_id": workspace_id,
                "row_id": data.get("ID", "")
            })

            command = {
                "action": "apply_strategy",
                "data": data
            }

            def callback(resp, row_id=data["row_id"]):
                if resp.get("status") == "success":
                    conn2 = db_handler.sqlite3.connect("users.db")
                    cur2 = conn2.cursor()
                    cur2.execute(f"UPDATE {physical_table} SET STATUS = 'ACTIVE' WHERE ID = ?", (row_id,))
                    conn2.commit()
                    conn2.close()
                    update_row_ui_active(row_id)  # Update the row to ACTIVE
                else:
                    messagebox.showerror("TCP Error", f"❌ {resp.get('message')}")
                    conn2 = db_handler.sqlite3.connect("users.db")
                    cur2 = conn2.cursor()
                    cur2.execute(f"UPDATE {physical_table} SET STATUS = 'INACTIVE' WHERE ID = ?", (row_id,))
                    conn2.commit()
                    conn2.close()
                    update_row_ui_inactive(row_id)  # Update the row to INACTIVE

                update_strategy_status_display()

            send_tcp_command(command, callback=callback)

    def handle_stop_all():
        table_name = table_var.get()
        if not table_name:
            messagebox.showerror("Error", "No table selected.")
            return

        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT schema, physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, table_name))
        result = cur.fetchone()
        if not result:
            messagebox.showerror("Error", "Table not found.")
            return

        schema = json.loads(result[0])
        physical_table = result[1]

        cur.execute(f"SELECT * FROM {physical_table}")
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        conn.close()

        total = len(rows)
        done = [0]  # mutable counter

        # Loop through each row and update it to 'WAITING'
        for row in rows:
            row_id = row[col_names.index("ID")]  # Assuming "ID" is the first column in schema
            status_value = row[col_names.index("STATUS")].upper()

        # Only set 'WAITING' if transitioning from 'ACTIVE' to 'INACTIVE'
            if status_value != "INACTIVE":
                update_row_ui_waiting(row_id)

            data = dict(zip(col_names, row))
            data.update({
                "strategy_name": data.get("STRATEGY", ""),
                "table_type": data.get("TABLE", "").lower(),
                "instrument_id": data.get("InstrumentID", ""),
                "instrument_name": data.get("InstrumentName", ""),
                "status": data.get("STATUS", ""),
                "user_id": user_id,
                "workspace_id": workspace_id,
                "row_id": data.get("ID", "")
            })

            command = {
                "action": "stop_strategy",
                "data": data
            }

            # Callback function to execute after sending stop command
            def callback(resp, row_id=data["row_id"]):
                if resp.get("status") == "success":
                    # No need to show success popup as we are directly updating the status
                    conn2 = db_handler.sqlite3.connect("users.db")
                    cur2 = conn2.cursor()
                    cur2.execute(f"UPDATE {physical_table} SET STATUS = 'INACTIVE' WHERE ID = ?", (row_id,))
                    conn2.commit()
                    conn2.close()
                    update_row_ui_inactive(row_id)  # Update the row to INACTIVE
                else:
                    messagebox.showerror("TCP Error", f"❌ {resp.get('message')}")
                    update_row_ui_active(row_id) 

                done[0] += 1
                if done[0] == total:
                    update_strategy_status_display()

            threading.Thread(target=lambda: send_tcp_command(command, callback=callback)).start()

    def set_default_table(table_name):
        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("UPDATE user_tables SET is_default=0 WHERE user_id=? AND workspace_id=?", (user_id, workspace_id))
        cur.execute("UPDATE user_tables SET is_default=1 WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, table_name))
        conn.commit()
        conn.close()
        messagebox.showinfo("Default Table", f"'{table_name}' set as default.")

    def update_table_display(table_name):
        nonlocal entry_widgets_by_row_id
        entry_widgets_by_row_id.clear()
        for widget in content_frame.winfo_children():
            widget.destroy()

        if not table_name:
            tk.Label(content_frame, text="No tables found. Click 'New Table' to create one.",
                    font=("Arial", 14), bg=bg_color, fg=fg_color).pack(expand=True)
            return
        
        # Safely get the physical table name
        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, table_name))
        result = cur.fetchone()
        if not result:
            conn.close()
            tk.Label(content_frame, text="Error: Table not found.", font=("Arial", 14), bg=bg_color, fg="red").pack()
            return
        physical_table = result[0]
        # Now safely read the data from that table
        try:
            print("DEBUG: physical_table =", physical_table)
            cur.execute(f'SELECT * FROM "{physical_table}"')  # Correct identifier quoting
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            conn.close()
        except Exception as e:
            conn.close()
            tk.Label(content_frame, text=f"Error reading data: {e}", font=("Arial", 12), bg=bg_color, fg="red").pack()
            print("EXCEPTION:", e)
            return

        # Header
        header = tk.Label(content_frame, text=f"{table_name}", font=("Arial", 16, "bold"),
                        bg=bg_color, fg=fg_color)
        header.pack(anchor="center", pady=(0, 10))

        # Table area (scrollable)
        table_canvas = tk.Canvas(content_frame, bg=bg_color)
        table_scroll = ttk.Scrollbar(content_frame, orient="vertical", command=table_canvas.yview)
        table_scroll.pack(side="right", fill="y")

        table_scroll_hori = ttk.Scrollbar(content_frame, orient="horizontal", command=table_canvas.xview)
        table_scroll_hori.pack(side="bottom", fill="x")

        scroll_frame = tk.Frame(table_canvas, bg=bg_color)

        scroll_frame.bind("<Configure>", lambda e: table_canvas.configure(scrollregion=table_canvas.bbox("all")))
        table_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        table_canvas.configure(yscrollcommand=table_scroll.set)
        table_canvas.configure(xscrollcommand=table_scroll_hori.set)

        table_canvas.pack(side="left", fill="both", expand=True)

        # Fetch schema to identify editable fields
        cur = db_handler.sqlite3.connect("users.db").cursor()
        cur.execute("SELECT schema FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?", 
                    (user_id, workspace_id, table_name))
        schema_data = json.loads(cur.fetchone()[0])
        conn.close()

        editable_cols = set(col["name"] for col in schema_data if col["editable"])
        col_indices = {name: idx for idx, name in enumerate(col_names)}

        tk.Label(scroll_frame, text="Select", font=("Arial", 10, "bold"),
         bg="#1f2937", fg="white", borderwidth=1, relief="solid", width=10).grid(row=0, column=0, sticky="nsew")

        # Draw header row with color-coded labels
        static_columns = {"ID", "STRATEGY", "TABLE", "STATUS", "InstrumentToken", "InstrumentID", "InstrumentName"}

        for col_idx, col_name in enumerate(col_names):
            is_static = col_name in static_columns
            is_editable = col_name in editable_cols

            if is_static:
                header_bg = "#2e6291"  # Deep blue
                header_fg = "white"
            elif is_editable:
                header_bg = "#489ad1"  # Yellowish blue
                header_fg = "black"
            else:
                header_bg = "#3b82f6"  # Normal blue
                header_fg = "white"

            tk.Label(
                scroll_frame,
                text=col_name,
                font=("Arial", 10, "bold"),
                fg=header_fg,
                bg=header_bg,
                borderwidth=1,
                relief="solid",
                width=15
            ).grid(row=0, column=col_idx + 1, sticky="nsew")  # +1 to skip Select

        # Add headers for action buttons
        tk.Label(scroll_frame, text="Apply", font=("Arial", 10, "bold"),
                bg="#d9d9d9", borderwidth=1, relief="solid", width=10).grid(row=0, column=len(col_names)+1, sticky="nsew")

        tk.Label(scroll_frame, text="Stop", font=("Arial", 10, "bold"),
                bg="#d9d9d9", borderwidth=1, relief="solid", width=10).grid(row=0, column=len(col_names)+2, sticky="nsew")

        tk.Label(scroll_frame, text="Delete", font=("Arial", 10, "bold"),
         bg="#d9d9d9", borderwidth=1, relief="solid", width=10).grid(row=0, column=len(col_names)+3, sticky="nsew")
        
        if not rows:
            print("✅ No rows found. Showing message.")
            msg_label = tk.Label(
                scroll_frame,
                text="No rows found. Click 'Add Row' to insert one.",
                font=("Arial", 13, "italic"),
                bg=bg_color,
                fg="gray"
            )
            msg_label.grid(
                row=1,
                column=0,
                columnspan=len(col_names) + 4,  # Select + data + Apply/Stop/Delete
                pady=30,
                sticky="nsew"
            )

        for row_idx, row_data in enumerate(rows, start=1):
            row_bg = "#f9fafb" if row_idx % 2 == 0 else "#e5e7eb"
            row_widgets = {}
            row_id = row_data[col_indices.get("ID")]
            
            # Add checkbox for selection
            status_value = str(row_data[col_indices.get("STATUS", -1)]).upper()
            selected_var = tk.IntVar(value=1 if status_value == "ACTIVE" else 0)
            cb_color = "#bbf7d0" if status_value == "ACTIVE" else row_bg
            cb = tk.Checkbutton(scroll_frame, variable=selected_var, bg=cb_color, activebackground=cb_color, bd=0, highlightthickness=0, relief="flat")
            def on_checkbox_toggle(row_id=row_id, var=selected_var):
                if var.get():
                    # Simulate Apply
                    if "apply_btn" in entry_widgets_by_row_id[row_id]:
                        entry_widgets_by_row_id[row_id]["apply_btn"].invoke()
                else:
                    # Simulate Stop
                    if "stop_btn" in entry_widgets_by_row_id[row_id]:
                        entry_widgets_by_row_id[row_id]["stop_btn"].invoke()

            cb.config(command=on_checkbox_toggle)
            cb.grid(row=row_idx, column=0, sticky="nsew", padx=1, pady=1)
            row_widgets["SELECTED"] = selected_var
            row_widgets["CHECKBOX_WIDGET"] = cb
            entry_widgets_by_row_id[row_id] = row_widgets

            # Define static/system columns
            static_columns = {"ID", "STRATEGY", "TABLE", "STATUS", "InstrumentToken", "InstrumentID", "InstrumentName"}

            # Add "Select" column header
            tk.Label(scroll_frame, text="Select", font=("Arial", 10, "bold"),
                 bg="#1f2937", fg="white", borderwidth=1, relief="solid", width=10).grid(row=0, column=0, sticky="nsew")
            for col_idx, col_name in enumerate(col_names):
                val = row_data[col_idx]
                is_static = col_name in static_columns
                is_editable = col_name in editable_cols
                entry = tk.Entry(scroll_frame, width=15, disabledforeground="black", justify="center", bg=row_bg, relief="flat")
                val = row_data[col_idx]
                entry.insert(0, "" if val is None else str(val))

                # Apply validation if editable
                if col_name in editable_cols:
                    # Find column type from schema
                    col_type = next((col['type'] for col in schema_data if col['name'] == col_name), "TEXT")
                    vcmd = entry.register(create_validator(col_type))
                    entry.config(validate="key", validatecommand=(vcmd, '%P'))
                    def save_edit(event, col=col_name, row=row_id, e_widget=entry):
                        new_value = e_widget.get()
                        conn2 = db_handler.sqlite3.connect("users.db")
                        cur2 = conn2.cursor()
                        try:
                            cur2.execute(f'UPDATE {physical_table} SET "{col}" = ? WHERE ID = ?', (new_value, row))
                            conn2.commit()
                        except Exception as ex:
                            print(f"❌ DB Update Error for {col}, ID={row}: {ex}")
                        finally:
                            conn2.close()

                    entry.bind("<FocusOut>", save_edit)
                else:
                    # Make truly read-only (no cursor, no edits)
                    entry.config(state="readonly", readonlybackground=row_bg, fg="black")

                if is_static:
                    header_bg = "#2e6291"  # Deep blue
                    header_fg = "white"
                elif is_editable:
                    header_bg = "#489ad1"  # Amber/yellow
                    header_fg = "black"
                else:
                    header_bg = "#3b82f6"  # Blue for readonly user-defined
                    header_fg = "white"

                tk.Label(scroll_frame, text=col_name, font=("Arial", 10, "bold"),
                        fg=header_fg, bg=header_bg, borderwidth=1, relief="solid", width=15).grid(row=0, column=col_idx + 1, sticky="nsew")

                entry.grid(row=row_idx, column=col_idx+1, sticky="nsew", padx=1, pady=1)
                if col_name in ["ID", "STATUS"]:
                    row_widgets[col_name] = entry
                else:
                    row_widgets[col_name] = entry
            
            # Action Buttons: Apply, Stop, Delete
            def make_apply_callback(row_widgets=row_widgets, physical_table=physical_table, row_id=row_data[col_indices["ID"]]):
                def apply():
                    # Show "WAITING" immediately when Apply is clicked
                    update_row_ui_waiting(row_id)

                    data = {col: entry.get() for col, entry in row_widgets.items() if isinstance(entry, tk.Entry)}
                    data["strategy_name"] = data.get("STRATEGY", "")
                    data["table_type"] = data.get("TABLE", "").lower()
                    data["instrument_id"] = data.get("InstrumentID", "")
                    data["instrument_name"] = data.get("InstrumentName", "")
                    data["status"] = data.get("STATUS", "")

                    # Build the TCP request
                    command = {
                        "action": "apply_strategy",
                        "data": data
                    }

                    # Callback to update UI after TCP response
                    def on_response(response):
                        if response.get("status") == "success":
                            
                            update_row_ui_active(row_id)  # Update the row to ACTIVE
                            # Update database status to ACTIVE
                            conn = db_handler.sqlite3.connect("users.db")
                            cur = conn.cursor()
                            cur.execute(f"UPDATE {physical_table} SET STATUS = 'ACTIVE' WHERE ID = ?", (row_id,))
                            conn.commit()
                            conn.close()

                        else:
                            messagebox.showerror("TCP Error", f"❌ {response.get('message')}")
                            update_row_ui_inactive(row_id)  # Update the row to INACTIVE

                        update_strategy_status_display()
                    send_tcp_command(command, callback=on_response)

                return apply

            def make_stop_callback(row_widgets=row_widgets, physical_table=physical_table, row_id=row_data[col_indices["ID"]]):
                def stop():
                    # Show "WAITING" immediately when Stop is clicked
                    update_row_ui_waiting(row_id)

                    data = {col: entry.get() for col, entry in row_widgets.items() if isinstance(entry, tk.Entry)}
                    data["row_id"] = row_id
                    data["table_type"] = data.get("TABLE", "")
                    data["user_id"] = user_id
                    data["workspace_id"] = workspace_id

                    command = {
                        "action": "stop_strategy",
                        "data": data
                    }

                    def on_response(response):
                        if response.get("status") == "success":
                            update_row_ui_inactive(row_id)  # Update the row to INACTIVE
                            # Update database status to INACTIVE
                            conn = db_handler.sqlite3.connect("users.db")
                            cur = conn.cursor()
                            cur.execute(f"UPDATE {physical_table} SET STATUS = 'INACTIVE' WHERE ID = ?", (row_id,))
                            conn.commit()
                            conn.close()

                        else:
                            messagebox.showerror("TCP Error", f"❌ {response.get('message')}")
                            update_row_ui_active(row_id)  # Update the row to ACTIVE

                        update_strategy_status_display()

                    send_tcp_command(command, callback=on_response)

                return stop

            def make_delete_callback(row_id=row_data[col_indices["ID"]]):
                def delete():
                    confirm = messagebox.askyesno("Delete", f"Delete row ID {row_id}?")
                    if not confirm:
                        return
                    conn = db_handler.sqlite3.connect("users.db")
                    cur = conn.cursor()
                    cur.execute(f'DELETE FROM {physical_table} WHERE ID = ?', (row_id,))
                    conn.commit()
                    conn.close()
                    refresh_tables(table_name)
                return delete

            action_col = len(col_names)+1
            # Determine status to conditionally disable buttons
            is_active = status_value == "ACTIVE"
            is_inactive = status_value == "INACTIVE"

            apply_btn = tk.Button(
                scroll_frame,
                text="Apply" if is_inactive else "Applied",
                bg="#090a0a",  # soft green
                fg="white",
                disabledforeground="#383838",
                width=6,
                font=("Arial", 10, "bold"),
                command=make_apply_callback(),
                state="disabled" if is_active else "normal",
                relief="flat"
            )

            apply_btn.grid(row=row_idx, column=action_col, sticky="nsew")

            stop_btn = tk.Button(
                scroll_frame,
                text="Stop" if is_active else "Stopped",
                bg="#090a0a",  # soft red
                fg="white",
                disabledforeground="#383838",
                width=6,
                font=("Arial", 10, "bold"),
                command=make_stop_callback(),
                state="disabled" if is_inactive else "normal",
                relief="flat"
            )

            stop_btn.grid(row=row_idx, column=action_col + 1, sticky="nsew")

            delete_btn = tk.Button(
                scroll_frame,
                text="🗑️",
                bg="#848688",  # gray
                fg="white",
                disabledforeground="#383838",
                width=6,
                font=("Arial", 10, "bold"),
                command=make_delete_callback(),
                state="disabled" if is_active else "normal",
                relief="flat"
            )

            delete_btn.grid(row=row_idx, column=action_col + 2, sticky="nsew")

            # Store the button references
            row_widgets["apply_btn"] = apply_btn
            row_widgets["stop_btn"] = stop_btn
            row_widgets["delete_btn"] = delete_btn

            update_strategy_status_display()

    def update_strategy_status_display():
        total = 0
        active = 0

        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()

        selected_table = table_var.get()
        if not selected_table:
            status_label.config(text="No strategies available", fg="gray")
            return

        cur.execute("SELECT physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, selected_table))
        result = cur.fetchone()
        if not result:
            status_label.config(text="Invalid table", fg="gray")
            return

        physical_table = result[0]
        try:
            cur.execute(f"SELECT STATUS FROM {physical_table}")
            rows = cur.fetchall()
            total = len(rows)
            active = sum(1 for r in rows if r[0].upper() == "ACTIVE")
        except:
            total = 0
            active = 0

        conn.close()
    
        # Update the status label text
        if total == 0:
            status_label.config(text="No strategies available", fg="black")
        else:
            status_label.config(text=f"📈 {active} / {total} strategies active", fg="green" if active > 0 else "red")

        # print(f"🟢 Updating strategy status: {active} / {total}")

    def refresh_tables(select_table_name=None):
        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()

        # Fetch all tables for this user/workspace
        cur.execute("SELECT table_name, is_default FROM user_tables WHERE user_id=? AND workspace_id=?", (user_id, workspace_id))
        table_rows = cur.fetchall()
        conn.close()

        # Separate table names and detect default
        tables = []
        default_table_name = None
        for name, is_default in table_rows:
            tables.append(name)
            if is_default:
                default_table_name = name

        # Update dropdown
        table_dropdown["values"] = tables
        if tables:
            # Set default selected
            if select_table_name and select_table_name in tables:
                table_var.set(select_table_name)
            elif default_table_name:
                table_var.set(default_table_name)
            else:
                table_var.set(tables[0])
        else:
            table_var.set("")

        # Clear content area
        for widget in content_frame.winfo_children():
            widget.destroy()

        # No tables
        if not tables:
            tk.Label(content_frame, text="No tables found. Click 'New Table' to create one.",
                    font=("Arial", 14), bg=bg_color, fg=fg_color).pack(expand=True)
        else:
            # Show current selected table
            selected = table_var.get()
            label_text = f"{selected}"
            if selected == default_table_name:
                label_text += " ⭐ (Default)"
            tk.Label(content_frame, text=label_text,
                    font=("Arial", 16), bg=bg_color, fg=fg_color).pack(anchor="center")
            
        update_strategy_status_display()

        update_table_display(table_var.get())

    def export_table_as_json():
        table_name = table_var.get()
        if not table_name:
            messagebox.showerror("Error", "Please select a table to export.")
            return
        print("this is the table name", table_name)

        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT schema, physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, table_name))
        result = cur.fetchone()
        if not result:
            messagebox.showerror("Error", "Table not found.")
            return
        schema_json, physical_table = result
        schema = json.loads(schema_json)

        cur.execute(f"SELECT * FROM {physical_table}")
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]

        data_rows = []
        for row in rows:
            row_dict = dict(zip(col_names, row))
            row_dict["STATUS"] = "INACTIVE"  # Force status to INACTIVE
            data_rows.append(row_dict)

        export_data = {
            "table_name": table_name,
            "schema": schema,
            "rows": data_rows
        }

        save_path = asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if save_path:
            with open(save_path, "w") as f:
                json.dump(export_data, f, indent=4)
            messagebox.showinfo("Export Success", f"Table '{table_name}' exported successfully!")
        conn.close()

    def import_table_from_json():
        file_path = askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return

        with open(file_path, "r") as f:
            data = json.load(f)

        imported_table_name = data.get("table_name", "").upper()
        schema = data.get("schema", [])
        rows = data.get("rows", [])

        if not imported_table_name or not schema:
            messagebox.showerror("Import Error", "Invalid or corrupt JSON file.")
            return

        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()

        physical_table_name = f"user_{user_id}_ws_{workspace_id}_{imported_table_name}".replace(" ", "_")

        # Ensure table creation
        column_defs = ['"ID" TEXT', '"STRATEGY" TEXT', '"TABLE" TEXT', '"STATUS" TEXT',
                    '"InstrumentToken" TEXT', '"InstrumentID" TEXT', '"InstrumentName" TEXT']
        for col in schema:
            column_defs.append(f'"{col["name"]}" {col["type"]}')

        cur.execute(f"CREATE TABLE IF NOT EXISTS {physical_table_name} ({', '.join(column_defs)})")

        # Insert metadata
        cur.execute("INSERT OR IGNORE INTO user_tables (user_id, workspace_id, table_name, schema, physical_table_name, is_default) VALUES (?, ?, ?, ?, ?, 0)",
                    (user_id, workspace_id, imported_table_name, json.dumps(schema), physical_table_name))

        for row in rows:
            next_id = get_next_session_id()
            print("this is the next session id", next_id)
            row["ID"] = str(next_id)
            row["STRATEGY"] = f"{imported_table_name}_{next_id}"
            row["STATUS"] = "INACTIVE"
            row["TABLE"] = imported_table_name.upper()
            columns = list(row.keys())
            placeholders = ", ".join("?" for _ in columns)
            quoted_columns = ", ".join(f'"{col}"' for col in columns)
            cur.execute(f'INSERT INTO {physical_table_name} ({quoted_columns}) VALUES ({placeholders})',
                        [row[col] for col in columns])

        conn.commit()
        conn.close()
        messagebox.showinfo("Import Success", f"Table '{imported_table_name}' imported successfully!")
        refresh_tables(imported_table_name)

    # Attach action buttons
    for act in TABLE_ACTIONS:
        if act == "New Table":
            btn = tk.Button(
                action_btns, text=act,
                command=lambda: open_create_table_popup(win, workspace_id, user_id, lambda: refresh_tables(table_var.get())),
                bg="#2563eb", fg="white",
                activebackground="#1d4ed8", activeforeground="white",
                font=("Arial", 10, "bold"),
                relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
            )

        elif act == "Set Default":
            btn = tk.Button(
                action_btns, text=act,
                command=lambda: set_default_table(table_var.get()),
                bg="#6b7280", fg="white",
                activebackground="#4b5563", activeforeground="white",
                font=("Arial", 10, "bold"),
                relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
            )

        elif act == "Export Table":
            btn = tk.Button(
                action_btns, text=act,
                command=export_table_as_json,
                bg="#F2D2BD", fg="black",
                font=("Arial", 10, "bold"),
                relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
            )

        elif act == "Import Table":
            btn = tk.Button(
                action_btns, text=act,
                command=import_table_from_json,
                bg="#AFE1AF", fg="black",
                font=("Arial", 10, "bold"),
                relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
            )

        elif act == "Edit Table":
            btn = tk.Button(
                action_btns, text=act,
                command=lambda: open_edit_table_popup(win, workspace_id, user_id, table_var.get(), refresh_tables),
                bg="#0ea5e9", fg="white",
                activebackground="#0284c7", activeforeground="white",
                font=("Arial", 10, "bold"),
                relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
            )

        elif act == "Add Row":
            btn = tk.Button(
                action_btns, text=act,
                command=lambda: handle_add_row(user_id, workspace_id, table_var.get(), refresh_tables),
                bg="#22c55e", fg="white",
                activebackground="#16a34a", activeforeground="white",
                font=("Arial", 10, "bold"),
                relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
            )

        elif act == "Start All":
            btn = tk.Button(
                action_btns, text=act,
                command=handle_start_all,
                bg="#10b981", fg="white",
                activebackground="#059669", activeforeground="white",
                font=("Arial", 10, "bold"),
                relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
            )

        elif act == "Stop All":
            btn = tk.Button(
                action_btns, text=act,
                command=handle_stop_all,
                bg="#ef4444", fg="white",
                activebackground="#dc2626", activeforeground="white",
                font=("Arial", 10, "bold"),
                relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
            )

        else:
            btn = tk.Button(
                action_btns, text=act,
                bg="#6b7280", fg="white",
                font=("Arial", 10, "bold"),
                relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
            )

        btn.pack(side="left", padx=5, pady=2)

    def back():
        cleanup_window(win) 
        if master_win:
            master_win.deiconify()
            master_win.lift()
            master_win.focus_force()
 
    # Add "Back to Workspaces" after "Stop All"
    back_btn = tk.Button(action_btns, text="Back to Workspaces", command=back,
                        bg="#f44336", fg="white", font=("Arial", 10, "bold"),bd=0, padx=12, pady=6)
    back_btn.pack(side="left", padx=5)

    right_buttons = tk.Frame(header)
    right_buttons.pack(side="right")

    tk.Button(right_buttons,
                          text="Exit Fullscreen",
                          command=exit_fullscreen,
                          bg="#BBB5B5",
                          fg="white",
                          font=("Arial", 10, "bold"),
                          relief="flat",
                          borderwidth=0,
                          highlightthickness=2,
                          highlightbackground="#9C9898",
                          highlightcolor="#808080",
                          cursor="hand2",bd=0, padx=12, pady=6
                         ).pack(side="left")

         # === STATUS BAR ===
    status_frame = tk.Frame(win, bg=bg_color)
    status_frame.pack(fill="x", padx=20, pady=5)

    status_label = tk.Label(status_frame, text="No strategies applied yet", font=("Arial", 10, "bold"),
                        bg=bg_color, fg="green", anchor="w", justify="left")
    status_label.pack(side="left")

    refresh_tables()

    return win