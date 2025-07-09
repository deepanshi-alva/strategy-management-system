import tkinter as tk
from tkinter import ttk, messagebox
import config  # access the shared list

instrument_popup = None

def select_instrument(callback):
    global instrument_popup

    instruments = config.cached_instruments

    # Group instruments by symbol
    symbol_to_instruments = {}
    for name, symbol, token in instruments:
        symbol_to_instruments.setdefault(symbol, []).append((name, symbol, token))
        
    distinct_symbols = sorted(symbol_to_instruments.keys())

    if instrument_popup is None or not instrument_popup.winfo_exists():
        print("1")
        instrument_popup = tk.Toplevel()
        instrument_popup.title("Select Instrument")
        instrument_popup.geometry("350x200")

        # --- IMPORTANT CHANGE 1: Create a handler for window close (X button) ---
        def on_popup_close():
            global instrument_popup
            instrument_popup.destroy() # Destroy the window
            instrument_popup = None    # Reset the reference to None
        instrument_popup.protocol("WM_DELETE_WINDOW", on_popup_close) # Use the new handler

        # SYMBOL Dropdown
        tk.Label(instrument_popup, text="Select Symbol:").pack(pady=(10, 0))
        instrument_popup.symbol_var = tk.StringVar(value="-- Select a Symbol --")
        instrument_popup.symbol_dropdown = ttk.Combobox(
            instrument_popup,
            textvariable=instrument_popup.symbol_var,
            width=35,
            state="normal",
            values=["-- Select a Symbol --"] + distinct_symbols
        )
        instrument_popup.symbol_dropdown.pack(pady=5)
        instrument_popup.all_symbols = distinct_symbols

        # Autocomplete filtering for symbols Track scheduled job to debounce
        instrument_popup.symbol_filter_job = None

        def on_symbol_keyrelease(event):
            if instrument_popup.symbol_filter_job:
                instrument_popup.after_cancel(instrument_popup.symbol_filter_job)

            instrument_popup.symbol_filter_job = instrument_popup.after(500, filter_symbol_dropdown)

        def filter_symbol_dropdown():
            typed = instrument_popup.symbol_dropdown.get()

            if typed.strip() == "":
                instrument_popup.symbol_dropdown['values'] = ["-- Select a Symbol --"] + instrument_popup.all_symbols
                return

            # Prioritize prefix matches
            typed_lower = typed.lower()
            starts_with = [s for s in instrument_popup.all_symbols if s.lower().startswith(typed_lower)]
            contains = [s for s in instrument_popup.all_symbols if typed_lower in s.lower() and not s.lower().startswith(typed_lower)]
            matches = starts_with + contains

            if matches:
                instrument_popup.symbol_dropdown['values'] = matches
                instrument_popup.symbol_dropdown.set(matches[0])  # Autocomplete to first match

                # Select the autocompleted portion
                instrument_popup.symbol_dropdown.icursor(len(typed))  # Move cursor to end of typed
                instrument_popup.symbol_dropdown.select_range(len(typed), tk.END)  # Highlight the remaining part
                instrument_popup.symbol_dropdown.event_generate('<Down>')
            else:
                instrument_popup.symbol_dropdown['values'] = []

        instrument_popup.symbol_dropdown.bind("<KeyRelease>", on_symbol_keyrelease)

        # NAME Dropdown
        tk.Label(instrument_popup, text="Select Instrument Name:").pack(pady=(10, 0))
        instrument_popup.name_var = tk.StringVar()
        instrument_popup.name_dropdown = ttk.Combobox(
            instrument_popup,
            textvariable=instrument_popup.name_var,
            width=35,
            state="readonly",
            values=[]
        )
        instrument_popup.name_dropdown.pack(pady=5)
        instrument_popup.name_dropdown.configure(state="disabled")  # <-- disable it initially

        # Autocomplete filtering for instrument names
        instrument_popup.name_filter_job = None
        instrument_popup.all_names = []  # To be filled when symbol is selected

        def on_name_keyrelease(event):
            if instrument_popup.name_filter_job:
                instrument_popup.after_cancel(instrument_popup.name_filter_job)

            instrument_popup.name_filter_job = instrument_popup.after(500, filter_name_dropdown)

        def filter_name_dropdown():
            typed = instrument_popup.name_dropdown.get()

            if typed.strip() == "":
                instrument_popup.name_dropdown['values'] = ["-- Select an Instrument --"] + instrument_popup.all_names
                return

            # Prioritize prefix matches
            typed_lower = typed.lower()
            starts_with = [n for n in instrument_popup.all_names if n.lower().startswith(typed_lower)]
            contains = [n for n in instrument_popup.all_names if typed_lower in n.lower() and not n.lower().startswith(typed_lower)]
            matches = starts_with + contains

            if matches:
                instrument_popup.name_dropdown['values'] = matches
                instrument_popup.name_dropdown.set(matches[0])  # Autocomplete to first match
                instrument_popup.name_dropdown.icursor(len(typed))  # Cursor after typed part
                instrument_popup.name_dropdown.select_range(len(typed), tk.END)  # Highlight completion
                instrument_popup.name_dropdown.event_generate('<Down>')
            else:
                instrument_popup.name_dropdown['values'] = []

        instrument_popup.name_dropdown.bind("<KeyRelease>", on_name_keyrelease)

        # Update instrument list when symbol is selected
        def on_symbol_change(event):
            selected_symbol = instrument_popup.symbol_var.get()
            if selected_symbol == "-- Select a Symbol --":
                instrument_popup.name_var.set('')
                instrument_popup.name_dropdown.set('')
                instrument_popup.name_dropdown['values'] = []
                instrument_popup.name_dropdown.configure(state="disabled")
                instrument_popup.all_names = []
                return

            related = symbol_to_instruments.get(selected_symbol, [])
            instrument_names = [name for name, _, _ in related]
            instrument_popup.all_names = instrument_names  # <-- Save for autocomplete
            instrument_popup.name_dropdown['values'] = ["-- Select an Instrument --"] + [name for name, _, _ in related]
            instrument_popup.name_var.set("-- Select an Instrument --")
            instrument_popup.name_dropdown.configure(state="normal") # Corrected 'norma;' to 'normal'

        instrument_popup.symbol_dropdown.bind("<<ComboboxSelected>>", on_symbol_change)

        # OK button logic
        def on_ok():
            global instrument_popup # Declare global to modify the reference
            selected_symbol = instrument_popup.symbol_var.get()
            selected_name = instrument_popup.name_var.get()

            if selected_symbol not in symbol_to_instruments or selected_name in ("", "-- Select an Instrument --"):
                messagebox.showwarning("Incomplete Selection", "Please select both symbol and instrument.")
                return

            related_instruments = symbol_to_instruments.get(selected_symbol, [])
            for name, symbol, token in related_instruments:
                if name == selected_name:
                    callback(name, symbol, token)
                    instrument_popup.destroy() # --- IMPORTANT CHANGE 2: Destroy instead of withdraw ---
                    instrument_popup = None    # Reset the reference to None
                    return
            messagebox.showerror("Error", "Selected instrument not found.")

        tk.Button(instrument_popup, text="OK", command=on_ok).pack(side="left", padx=20, pady=10)
        # --- IMPORTANT CHANGE 3: Create a separate handler for Cancel button ---
        def on_cancel():
            global instrument_popup
            instrument_popup.destroy() # Destroy the window
            instrument_popup = None    # Reset the reference to None
        tk.Button(instrument_popup, text="Cancel", command=on_cancel).pack(side="right", padx=20)

    else:
        # If popup already exists and is not destroyed, bring it to front and reset dropdowns
        print("2")
        instrument_popup.symbol_var.set("")
        instrument_popup.symbol_dropdown.set('')
        instrument_popup.symbol_dropdown['values'] = instrument_popup.all_symbols
        instrument_popup.name_var.set('')
        instrument_popup.name_dropdown.set('')
        instrument_popup.name_dropdown['values'] = []
        instrument_popup.name_dropdown.configure(state="disabled")
        instrument_popup.deiconify() # If it was withdrawn previously, bring it back
        instrument_popup.lift()