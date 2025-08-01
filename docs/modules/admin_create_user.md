This function creates the Signup UI window using tkinter. It allows new users to register by entering their full name, user ID , and password. It integrates input validation, password visibility toggling, database insertion, and redirects to the login window on successful signup.

Component	                 |       Purpose
-------------------------------------------------------------------------------------------------------------
tk.Tk()	                     |       Initializes a new standalone tkinter window for signup.
center_window()	             |       Custom utility function to center the window on screen.
on_configure()	             |       Maintains responsive window size on resize events.
Frame	                     |       Main container for arranging form widgets vertically.
Label	                     |       Displays static text for headings and input field labels.
Entry	                     |       Captures user input: Full Name, Email (User ID), Password.
StringVar + Checkbutton	     |       Enables toggle to show/hide password input.
Button: Signup	             |       Triggers the register() function to validate and create the user.
Button: Go to Login	         |       Cleans up and redirects to the login window.
messagebox	                 |       Displays warning, success, or error popups.
add_user()	                 |       Inserts user data into the SQLite DB with hashed password.

Functional Workflow : 
1) User inputs: Full Name, Email, Password.
2) Validation: Checks if fields are not empty.
3) Database Insertion: Calls add_user() from db_handler.py to store new user in users table.
4) Success Path: 
    Shows success message.
    Destroys the signup window.
    Redirects to login_window() from ui_login.py.
5) Failure Path:
    Shows error if email already exists.