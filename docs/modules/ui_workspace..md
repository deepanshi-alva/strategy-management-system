This module shows a full-screen interface after login where the user can:
    View all their saved workspaces
    Create, edit, open, set default, or delete a workspace
    Log out or exit fullscreen easily

open_workspace_windows = {}
    This dictionary keeps track of all the workspace windows that are currently open.
    It ensures only one window opens per workspace and prevents duplicates.

Function: workspace_window(email)
    The main function that creates and runs the "Workspaces" dashboard window.
    What It Does:
        Starts a full-screen window titled “Your Workspaces”
        Gets the user’s ID from the email
        Loads and shows their saved workspaces from the database
        If a default workspace is set, it opens it automatically

Utility Functions Inside:

1) exit_fullscreen()
    Turns off fullscreen and resizes the window to a normal fixed size (800x800).

2) logout()
    Logs the user out:
    Closes all open workspace windows
    Destroys the main dashboard
    Returns to the login window

3) set_default(workspace_id)
    Sets the selected workspace as the default (opened automatically on next login).

4) edit_workspace(workspace_id)
    Opens a popup to edit the name, emoji, or theme (light/dark) of the selected workspace.

5) delete_workspace(workspace_id)
    Asks for confirmation.
    Deletes the selected workspace from the database.
    Also closes the workspace window if it was open.

6) open_workspace(workspace_id, master_win)
    Opens the selected workspace in a new window, unless it’s already open.
    Handles:
        Reusing already opened windows (brings it to front).
        Tracks opened windows using open_workspace_windows.
        Registers a callback so when a workspace window is closed, it removes it from memory.

7) refresh_workspaces()
    Clear`s and reloads the list of workspaces from the database.
    For each workspace, it displays:
        Name
        Emoji
        Theme (dark/light)
        Buttons: Set as Default, Open, Edit, Delete
    Each workspace is` shown as a card with its own background color and buttons.

8) open_create_workspace_popup()
    Used to create a new workspace. It includes:
    Name input box
    Emoji picker (click to select)
    Theme selector (light or dark)
    Create and Cancel buttons

9) open_edit_workspace_popup()
    Used to edit an existing workspace, pre-filled with the workspace’s current values:
    Name
    Emoji
    Theme

    Includes:
    Save Changes button
    Cancel button