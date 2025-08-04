This module provides UI utility functions for handling tkinter windows more gracefully. It includes:
    Centering windows on screen
    Handling screen restore from maximized/fullscreen state
    Preventing UI glitches during resizing
    Cleaning up after() tasks and event bindings on window close

_after_ids = {}
    Stores after() task IDs for each window.
    Helps cancel delayed tasks tied to a specific window (used during resizing).

def center_window(window):
    Purpose: Centers the given window on the screen.
    How it works:
        update_idletasks() ensures size is up-to-date.
        Calculates screen center position.
        Sets new geometry: "{width}x{height}+{x}+{y}"
    Used after creating or resizing a window to place it at the center.

def _perform_centering_on_restore(window, default_width, default_height):
    Purpose: Resets the window to its default size and re-centers it after restore.
    How it works:
        Checks if the window exists and isn’t shutting down.
        Sets size to default_width x default_height.
        Calls center_window() to position it.
    Internally used by on_configure() after un-maximizing.

def on_configure(window, event, default_width, default_height):
    Purpose: Triggered on window resize events. If window is restored from maximized, it resets to default size and re-centers.
    How it works:
        If state is normal (i.e., not maximized or fullscreen):
            Cancels any pending after() tasks for that window.
            Schedules a new one with a 10ms delay.
            Stores that task ID in _after_ids.
    Should be bound to <Configure> event. Prevents UI glitches on window resize or unmaximize.

def restore_from_maximized_via_escape(window):
    Purpose: Allows a window to be restored from fullscreen or maximized mode back to normal.
    How it works:
        If fullscreen → disable fullscreen.
        If maximized (zoomed) → set to normal.
    Useful when binding Escape key or a custom shortcut to exit full window mode.

def cleanup_window(win):
    Purpose: Cleans up background tasks (after()) and event bindings before destroying a window.
    How it works:
        Flags the window as _is_shutting_down = True
        Cancels all after() tasks scheduled for that window.
        Unbinds <Configure> event (if bind_id exists).
        Removes the window entry from _after_ids.
    Must be called before win.destroy() to prevent memory leaks, orphaned timers, or crashes.