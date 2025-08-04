This script renders the Login Window using tkinter. It handles:
    User credential input
    Authentication via the database
    Session ID re-initialization
    Launching the user’s workspace dashboard on successful login

Functional Workflow: 
    User enters email and password.
    Credentials are verified using verify_user() from db_handler.py.
    If valid:
        Shows success message
        Reinitializes session row IDs in all user tables using reinitialize_session_ids()
        Starts the global app timer (config.start_global_timer())
        Opens the workspace UI via ui_workspace.workspace_window(email)
    If invalid:
        Shows an error message


ID Reinitialization – reinitialize_session_ids(user_id): 
This function ensures that all user table rows across all their workspaces have clean, sequential IDs starting from 1 for the session.

    🔄 Why This Matters
        Prevents ID duplication or inconsistency between sessions.
        Ensures stable row tracking inside the UI and strategy logic.

    🔢 How It Works
    Fetches all workspaces for the user, ordered by creation time.
    For each workspace:
        Fetches all custom user-created physical table names.
        Reads all current IDs from each table.
    For each table:
        Creates a mapping of old_id → new_id starting from 1.
        First, temporarily shifts all IDs to new_id + 1,000,000 to prevent conflicts.
        Then, normalizes back to new_id cleanly. This ensures no duplicates during renumbering and preserves the original order.

    Updates the global session counter