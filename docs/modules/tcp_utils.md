This function is the client-side utility that sends a JSON command to the local TCP server (hosted at 127.0.0.1:9999 by default) and optionally receives a response via callback.
It’s typically triggered when a user performs an action in the UI like "Apply Strategy" or "Stop Strategy".

How It Works
    1) Opens a TCP socket connection to the server.
    2) Serializes the command dict (e.g., {"action": "apply_strategy", data: {...}}) into a JSON string.
    3) Prefixes the JSON string with a 4-digit length (e.g., 0035{"action":...}) to match server protocol.
    4) Sends the message to the server.
    5) Receives the server’s response using the same 4-byte-prefixed format.
    6) Parses the response JSON and, if a callback is given, passes the result to it.

Threaded for Non-Blocking UI :
    Runs on a background thread (daemon=True) to prevent the GUI from freezing.
    You can safely call it from button actions or other events.

A daemon thread is a background thread that runs alongside the main program, but it does not block the program from exiting.
    If all non-daemon threads finish execution, the program will terminate, even if daemon threads are still running.
    It's used for background tasks that don't need to complete before the program exits.

How It Connects: 
Component	           |       Relationship
--------------------------------------------------------------------------------------------
tcp_server.py	       |       Server that this function talks to
UI Buttons	           |       Call this function to trigger backend strategy actions
callback(response)	   |       Receives and handles success/error response asynchronously