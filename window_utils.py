import tkinter as tk

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def _perform_centering_on_restore(window, default_width, default_height):
    if not window.winfo_exists() or (hasattr(window, '_is_shutting_down') and window._is_shutting_down):
        return

    if window.wm_state() == 'normal':
        window.geometry(f"{default_width}x{default_height}")
        center_window(window)

def on_configure(window, event, default_width, default_height):
    current_state = window.wm_state()
    if current_state == 'normal':
        if not hasattr(window, '_after_ids'):
            window._after_ids = []
        for after_id in window._after_ids:
            try:
                window.after_cancel(after_id)
            except tk.TclError:
                pass # Ignore if already cancelled or doesn't exist
        
        # Schedule centering after a short delay
        after_id = window.after(10, lambda: _perform_centering_on_restore(window, default_width, default_height))
        window._after_ids.append(after_id)

def restore_from_maximized_via_escape(window):
    if window.wm_state() == 'zoomed' or window.attributes('-fullscreen'):
        # If the window is fullscreen, turn off fullscreen
        if window.attributes('-fullscreen'):
            window.attributes('-fullscreen', False)
        # If it was zoomed (maximized), restore it to normal
        if window.wm_state() == 'zoomed':
            window.wm_state('normal')

def cleanup_window(current_window, next_window_function, *args, **kwargs):
    if hasattr(current_window, '_after_ids'):
        for after_id in current_window._after_ids:
            try:
                current_window.after_cancel(after_id)
            except tk.TclError:
                pass
    current_window._is_shutting_down = True
    current_window.destroy()
    next_window_function('normal', *args, **kwargs)  # ← pass 'normal' as default state
