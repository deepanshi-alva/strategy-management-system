This module acts as a central config and state management hub for the entire application. It defines global variables, caches, and a time-tracking utility used across different components.

start_global_timer(callback_every_second): 
    Starts a background timer thread that increments GLOBAL_ELAPSED_SECONDS every second and optionally triggers a callback with the updated time.
    Variable	Role
    TIMER_STARTED	Ensures the timer is only started once.
    GLOBAL_ELAPSED_SECONDS	Tracks elapsed time since timer started (in seconds).
    callback_every_second	A function to be called every second (if provided).
    time.sleep(1)	Keeps the loop interval to 1 second.
    threading.Thread(...)	Runs the timer loop in a separate daemon thread.

Global Variables: 
Variable	                           Type	                                  Description
--------------------------------------------------------------------------------------------------------------------------------------------------------------------
cached_instruments	           |        list	                   |          Stores a temporary list of selected instruments across sessions.
GLOBAL_SESSION_COUNTER	       |        int	                       |          Tracks unique session IDs incrementally.
GLOBAL_ELAPSED_SECONDS	       |        int	                       |          Time counter since timer started.
TIMER_STARTED	               |        bool	                   |          Flags whether the global timer has been initiated.
TEMP_ROW_STORAGE	           |        dict	                   |          Stores unsaved or in-memory rows per session or table.
AUTO_SAVE_JOB_ID	           |        any	                       |          Holds the scheduled job ID for auto-save (used for canceling or updating).
LAST_KNOWN_INTERVAL_MS	       |        int or None	               |          Stores the last used auto-save interval in milliseconds, if set.

