import tkinter as tk

_after_ids = {}

def center_window(window):
    """Centers a Tkinter window on the screen."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def _perform_centering_on_restore(window, default_width, default_height):
    if not window.winfo_exists() or (hasattr(window, '_is_shutting_down') and window._is_shutting_down):
        return
    window.geometry(f"{default_width}x{default_height}")
    center_window(window)

def on_configure(window, event, default_width, default_height):
    current_state = window.wm_state()
    if current_state == 'normal':
        if window not in _after_ids:
            _after_ids[window] = []

        for after_id in _after_ids[window]:
            try:
                window.after_cancel(after_id)
            except tk.TclError:
                pass
        _after_ids[window].clear() # Clear the list after canceling old IDs

        after_id = window.after(10, lambda: _perform_centering_on_restore(window, default_width, default_height))
        _after_ids[window].append(after_id)

def restore_from_maximized_via_escape(window):
    if window.wm_state() == 'zoomed' or window.attributes('-fullscreen'):
        if window.attributes('-fullscreen'):
            window.attributes('-fullscreen', False)
        if window.wm_state() == 'zoomed':
            window.wm_state('normal')

def cleanup_window(win):
    if not hasattr(win, '_is_shutting_down'):
        win._is_shutting_down = False # Initialize if not present
    win._is_shutting_down = True
    
    if win in _after_ids:
        for after_id in _after_ids[win]:
            try:
                win.after_cancel(after_id)
            except tk.TclError:
                pass # Ignore if already cancelled or doesn't exist
        del _after_ids[win] # Remove the window's entry from the dictionary after cleanup
    
    if hasattr(win, 'bind_id') and win.bind_id:
        try:
            win.unbind('<Configure>', win.bind_id)
        except tk.TclError:
            pass # Ignore if already unbound or doesn't exist
        win.bind_id = None # Clear the stored bind ID