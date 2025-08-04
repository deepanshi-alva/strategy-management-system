This script runs a lightweight TCP server that listens for incoming JSON-based commands from the frontend/backend (like applying or stopping trading strategies). It handles real-time requests from the UI.

What It Does: 
1) Starts a TCP server at 127.0.0.1:9999 (default) or a custom host/port.
2) Listens for client requests via socket.
3) Parses JSON commands prefixed by a 4-digit length header.
4) Supports 2 main actions:
    apply_strategy: Activates a strategy and logs its metadata.
    stop_strategy: Stops a strategy by removing it from the active list.
5) Returns a structured JSON response for each request, including timestamp and strategy ID.

Key Components
Component	              |         Role
--------------------------------------------------------------------------------------------------------------------
TradingTCPServer	      |         Main server class managing socket lifecycle and strategy state.
start()	                  |         Sets up socket, accepts clients, spawns a thread for each.
_handle_client()	      |         Reads 4-digit-prefixed JSON messages, processes them, sends back responses.
_process_request()	      |         Routes actions (apply_strategy, stop_strategy) to handlers.
active_strategies	      |         Dictionary storing all currently active strategies with metadata.

Message Protocol: 
    Request Format: ####<json> (e.g., 0035{"action": "apply_strategy", ...})
    Response Format: Same 4-digit length-prefixed JSON.
        Example response:
        {
        "status": "success",
        "message": "Strategy applied successfully",
        "strategy_id": "mytable_3",
        "timestamp": "2025-08-04T10:31:55.123Z"
        }

How to Run: 
    python tcp_server.py --port 9999 --host 127.0.0.1 
    (You can change the port and host using command-line arguments.)

How It Connects: 
    Frontend or workspace UI sends TCP commands (like strategy apply/stop) to this server.
    This server handles the logic and maintains an in-memory map of currently running strategies.
    Works in sync with the UI buttons like "Start All", "Stop All", or individual row actions.