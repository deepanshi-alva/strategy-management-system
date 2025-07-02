import tkinter as tk
from tkinter import ttk, messagebox
import db_handler
import json
import ui_workspace
from instrument_pop import select_instrument
from functools import partial
from tcp_utils import send_tcp_command
import threading

# Constants
TABLE_ACTIONS = ["Set Default", "New Table", "Edit Table", "Add Row", "Start All", "Stop All"]

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
        edit_check = tk.Checkbutton(edit_frame, text="Editable", variable=editable)
        edit_check.pack()
        edit_frame.pack(side="left", padx=5)

        # --- Remove Button ---
        del_btn = tk.Button(row, text="Remove", command=lambda: remove_column(row))
        del_btn.pack(side="right")

        column_entries.append((name, dtype, default, editable))

    def remove_column(row):
        for i, (n, t, d, e) in enumerate(column_entries):
            if n.master == row:
                column_entries.pop(i)
                break
        row.destroy()

    add_column()

    tk.Button(popup, text="Add Column", command=add_column).pack(pady=5)

    def create_table():
        table_name = table_name_entry.get().strip().upper()
        if not table_name:
            messagebox.showerror("Error", "Table name is required")
            return

        schema = []
        for name, dtype, default, editable in column_entries:
            col_name = name.get().strip().upper()
            col_type = dtype.get()
            col_default = default.get().strip()
            is_editable = bool(editable.get())

            if not col_name:
                messagebox.showerror("Error", "Column name is required")
                return

            schema.append({
                "name": col_name,
                "type": col_type,
                "default": col_default,
                "editable": is_editable
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

    tk.Button(popup, text="Create Table", command=create_table, bg="green", fg="white").pack(pady=10)

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

    def add_column_with_values(col_name="", col_type="INTEGER", col_default="", col_editable=False):
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
        edit_check = tk.Checkbutton(edit_frame, text="Editable", variable=editable)
        edit_check.pack()
        edit_frame.pack(side="left", padx=5)

        del_btn = tk.Button(row, text="Remove", command=lambda: remove_column(row))
        del_btn.pack(side="right")

        column_entries.append((name, dtype, default, editable))

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
            col_editable=col["editable"]
        )

    tk.Button(popup, text="Add Column", command=lambda: add_column_with_values()).pack(pady=5)

    def save_changes():
        new_table_name = table_name_entry.get().strip().upper()
        if not new_table_name:
            messagebox.showerror("Error", "Table name cannot be empty.")
            return

        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()

        # Check for name conflict if changed
        if new_table_name != old_table_name:
            cur.execute("SELECT 1 FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                        (user_id, workspace_id, new_table_name))
            if cur.fetchone():
                conn.close()
                messagebox.showerror("Error", "A table with this name already exists.")
                return

        # Collect new schema
        new_schema = []
        for name, dtype, default, editable in column_entries:
            col_name = name.get().strip().upper()
            col_type = dtype.get()
            col_default = default.get().strip()
            is_editable = bool(editable.get())

            if not col_name:
                messagebox.showerror("Error", "Column name cannot be empty.")
                return

            new_schema.append({
                "name": col_name,
                "type": col_type,
                "default": col_default,
                "editable": is_editable
            })

        # Update table
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

        # --- THE CRITICAL CHANGE FOR ID GENERATION STARTS HERE ---
        # Find the maximum existing ID in the table and increment it.
        # CAST(ID AS INTEGER) is used to ensure numerical comparison, as IDs are stored as text.
        cur.execute(f"SELECT MAX(CAST(ID AS INTEGER)) FROM {physical_table}")
        max_id_result = cur.fetchone()[0]

        # If the table is empty (max_id_result is None), start ID from 1.
        # Otherwise, increment the highest existing ID by 1.
        next_id = (max_id_result if max_id_result is not None else 0) + 1

        print("The next unique ID for the new row is:", next_id) # For debugging/verification
        # --- END OF CRITICAL CHANGE FOR ID GENERATION ---

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

# Main layout for workspace
def open_workspace_layout(workspace_id, email):
    user_id = db_handler.get_user_id(email)
    workspace = db_handler.get_workspace_by_id(workspace_id)
    entry_widgets_by_row_id = {}
    name, theme, icon = workspace

    bg_color = "#ffffff" if theme == "light" else "#111111"
    fg_color = "black" if theme == "light" else "white"

    win = tk.Tk()
    win.title(name)
    # win.attributes("-fullscreen", True)
    win.configure(bg=bg_color)

    # === HEADER ===
    header = tk.Frame(win, bg=bg_color)
    header.pack(fill="x", padx=20, pady=10)
    tk.Label(header, text=f"{icon} {name}", font=("Arial", 24, "bold"), bg=bg_color, fg=fg_color).pack(side="left")

    table_frame = tk.Frame(win, bg=bg_color)
    table_frame.pack(fill="x", padx=20, pady=5)

    # Dropdown for tables
    tk.Label(table_frame, text="Table:", bg=bg_color, fg=fg_color).pack(side="left")
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
                if "apply_btn" in widgets:
                    widgets["apply_btn"].config(state="disabled")
                if "delete_btn" in widgets:
                    widgets["delete_btn"].config(state="disabled")
                if "stop_btn" in widgets:
                    widgets["stop_btn"].config(state="normal")


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
            if "apply_btn" in widgets:
                widgets["apply_btn"].config(state="normal")
            if "delete_btn" in widgets:
                widgets["delete_btn"].config(state="normal")
            if "stop_btn" in widgets:
                widgets["stop_btn"].config(state="disabled")


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

        # Loop through each row and update it to 'WAITING' immediately
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
        
        # Get physical table name
        conn = db_handler.sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT physical_table_name FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?",
                    (user_id, workspace_id, table_name))
        result = cur.fetchone()
        if not result:
            conn.close()
            tk.Label(content_frame, text="Error loading table.", font=("Arial", 12), bg=bg_color, fg="red").pack()
            return

        physical_table = result[0]

        try:
            cur.execute(f"SELECT * FROM {physical_table}")
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            conn.close()
        except Exception as e:
            conn.close()
            tk.Label(content_frame, text=f"Error reading data: {e}", font=("Arial", 12), bg=bg_color, fg="red").pack()
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

        # Draw header row with color-coded labels
        for col_idx, col_name in enumerate(col_names):
            is_editable = col_name in editable_cols
            header_color = "yellow" if is_editable else "blue"
            tk.Label(scroll_frame, text=col_name, font=("Arial", 10, "bold"),
                    fg=header_color, bg="#d9d9d9", borderwidth=1, relief="solid", width=15).grid(row=0, column=col_idx, sticky="nsew")

        # Add headers for action buttons
        tk.Label(scroll_frame, text="Apply", font=("Arial", 10, "bold"),
                bg="#d9d9d9", borderwidth=1, relief="solid", width=10).grid(row=0, column=len(col_names)+1, sticky="nsew")

        tk.Label(scroll_frame, text="Stop", font=("Arial", 10, "bold"),
                bg="#d9d9d9", borderwidth=1, relief="solid", width=10).grid(row=0, column=len(col_names)+2, sticky="nsew")

        tk.Label(scroll_frame, text="Delete", font=("Arial", 10, "bold"),
         bg="#d9d9d9", borderwidth=1, relief="solid", width=10).grid(row=0, column=len(col_names)+3, sticky="nsew")

        # Fetch schema to identify editable fields
        cur = db_handler.sqlite3.connect("users.db").cursor()
        cur.execute("SELECT schema FROM user_tables WHERE user_id=? AND workspace_id=? AND table_name=?", 
                    (user_id, workspace_id, table_name))
        schema_data = json.loads(cur.fetchone()[0])
        conn.close()

        editable_cols = set(col["name"] for col in schema_data if col["editable"])
        col_indices = {name: idx for idx, name in enumerate(col_names)}

        for row_idx, row_data in enumerate(rows, start=1):
            row_widgets = {}
            row_id = row_data[col_indices.get("ID")]
            
            # Add checkbox for selection
            status_value = str(row_data[col_indices.get("STATUS", -1)]).upper()
            selected_var = tk.IntVar(value=1 if status_value == "ACTIVE" else 0)
            cb = tk.Checkbutton(scroll_frame, variable=selected_var, bg=bg_color)
            cb.grid(row=row_idx, column=0, sticky="nsew")
            row_widgets["SELECTED"] = selected_var
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
                entry = tk.Entry(scroll_frame, width=15, disabledforeground="black", justify="center")

                val = row_data[col_idx]
                entry.insert(0, val)

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
                    entry.config(state="readonly", readonlybackground="#e5e7eb", fg="black")

                if is_static:
                    header_bg = "#1f4e78"  # Deep blue
                    header_fg = "white"
                elif is_editable:
                    header_bg = "#facc15"  # Amber/yellow
                    header_fg = "black"
                else:
                    header_bg = "#3b82f6"  # Blue for readonly user-defined
                    header_fg = "white"

                tk.Label(scroll_frame, text=col_name, font=("Arial", 10, "bold"),
                        fg=header_fg, bg=header_bg, borderwidth=1, relief="solid", width=15).grid(row=0, column=col_idx + 1, sticky="nsew")

                entry.grid(row=row_idx, column=col_idx+1, sticky="nsew")
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
                text="✅",
                bg="green",
                fg="white",
                width=6,
                font=("Arial", 10, "bold"),
                command=make_apply_callback(),
                state="disabled" if is_active else "normal"
            )
            apply_btn.grid(row=row_idx, column=action_col, sticky="nsew")

            stop_btn = tk.Button(
                scroll_frame,
                text="⛔",
                bg="red",
                fg="white",
                width=6,
                font=("Arial", 10, "bold"),
                command=make_stop_callback(),
                state="disabled" if is_inactive else "normal"
            )
            stop_btn.grid(row=row_idx, column=action_col + 1, sticky="nsew")

            delete_btn = tk.Button(
                scroll_frame,
                text="🗑️",
                bg="gray",
                fg="white",
                width=6,
                font=("Arial", 10, "bold"),
                command=make_delete_callback(),
                state="disabled" if is_active else "normal"
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
            status_label.config(text="No table selected", fg="gray")
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
            status_label.config(text="No strategies available", fg="gray")
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

    # Attach action buttons
    for act in TABLE_ACTIONS:
        if act == "New Table":
            btn = tk.Button(action_btns, text=act, command=lambda: open_create_table_popup(win, workspace_id, user_id, lambda: refresh_tables(table_var.get())))
        elif act == "Set Default":
            btn = tk.Button(action_btns, text=act, command=lambda: set_default_table(table_var.get()))
        elif act == "Edit Table":
            btn = tk.Button(action_btns, text=act, command=lambda: open_edit_table_popup(win, workspace_id, user_id, table_var.get(), refresh_tables))
        elif act == "Add Row":
            btn = tk.Button(action_btns, text=act, command=lambda: handle_add_row(user_id, workspace_id, table_var.get(), refresh_tables))
        elif act == "Start All":
            btn = tk.Button(action_btns, text=act, command=handle_start_all, bg="green", fg="white")
        elif act == "Stop All":
            btn = tk.Button(action_btns, text=act, command=handle_stop_all, bg="red", fg="white")
        else:
            btn = tk.Button(action_btns, text=act)
        btn.pack(side="left", padx=5)


    def back():
        win.destroy()
        ui_workspace.workspace_window(email)
    
    # Add "Back to Workspaces" after "Stop All"
    back_btn = tk.Button(action_btns, text="Back to Workspaces", command=lambda: back(),
                        bg="#f44336", fg="white", font=("Arial", 12, "bold"))
    back_btn.pack(side="left", padx=5)

         # === STATUS BAR ===
    status_frame = tk.Frame(win, bg=bg_color)
    status_frame.pack(fill="x", padx=20, pady=5)

    status_label = tk.Label(status_frame, text="No strategies applied yet", font=("Arial", 10, "bold"),
                        bg=bg_color, fg="green", anchor="w", justify="left")
    status_label.pack(side="left")


    refresh_tables()

    win.mainloop()