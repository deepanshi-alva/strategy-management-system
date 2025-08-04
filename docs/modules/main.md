This is the starting point of the entire application. When you run the program, this file does the following:
    Initializes the core user database (if not already present).
    Preloads available trading instruments from an external .db3 file into a shared global list (config.cached_instruments).
    Launches the Login UI where users begin interacting with the system.

Functional Workflow: 
    1. init_db()
        From db_handler.py
        Creates users, workspaces, and user_tables tables inside users.db if they don't exist.
        Ensures the application can store user credentials, UI configurations, and table data.

    2. preload_instruments()
        Loads all instrument data from an external SQLite database: 20250606DB.db3.
        Extracts the Name, Symbol, and Token from the ResultSet table.
        Stores the list in config.cached_instruments for global access across the app (especially used by the instrument selector UI).

    📁 Why resource_path()?
        Makes the app compatible with PyInstaller, so it works both in development and when packaged as an executable.
        Ensures the .db3 file path resolves correctly in any environment.

    3. ui_login.login_window()
        Opens the Login Window using tkinter.
        Acts as the first screen users see to access their workspace and data.

How It All Connects: 
Module	                         |          Responsibility
------------------------------------------------------------------------------------------------------------------------------
db_handler	                     |          Sets up and manages the primary database (users.db).
config	                         |          Holds global state like cached instruments and timers.
20250606DB.db3	                 |          External database containing trading instruments (ResultSet table).
ui_login	                     |          Launches the login interface.
resource_path()	                 |          Ensures correct file paths (especially post-compilation).