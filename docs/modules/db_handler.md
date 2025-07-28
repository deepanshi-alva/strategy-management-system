This module manages user registration, authentication, and workspace creation using an SQLite database (users.db). It defines a clean relational structure where:
Each user can have multiple workspaces.
Each workspace can contain multiple user-created tables.

Stores basic user information:
id (PK)
full_name
email (unique)
password (SHA-256 hashed)
created_at

Each workspace belongs to a user:
id (PK)
user_id (FK → users.id)
name
is_default (used to mark the primary workspace)
theme, icon
created_at

Tracks logical tables created by users within workspaces:
id (PK)
user_id (FK → users.id)
workspace_id (FK → workspaces.id)
table_name, schema, physical_table_name
is_default, created_at

🔐 Security:
Passwords are hashed using SHA-256 before storing.
Duplicate email registrations are blocked using a UNIQUE constraint.

Functionality
Function	                        |               Purpose
------------------------------------------------------------------------------------------------------------------------
init_db()	                        |               Initializes all tables and enables foreign keys.
add_user()	                        |               Adds a new user with hashed password.
verify_user()	                    |               Verifies login credentials.
get_user_id()	                    |               Retrieves user ID using email.
get_workspaces()	                |               Returns all workspaces for a user.
create_workspace()	                |               Creates a new workspace; can optionally set it as default.
set_default_workspace()	            |               Marks a selected workspace as the default and unsets others.
get_workspace_by_id()	            |               Fetches details like name, theme, and icon.
update_workspace()	                |               Updates workspace name, theme, and icon.
delete_workspace()	                |               Deletes a workspace and cascades related tables.
get_default_workspace_id()	        |               Returns the default workspace ID for a user.


How Everything Connects:
Users → Workspaces: One-to-many (a user can have many workspaces).
Workspaces → User Tables: One-to-many (a workspace can have many user-defined tables).
Deleting a user cascades deletes their workspaces and user tables.