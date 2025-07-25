# config.py
import threading
import time
LAST_KNOWN_INTERVAL_MS = None

def start_global_timer(callback_every_second=None):
    global TIMER_STARTED, GLOBAL_ELAPSED_SECONDS
    if TIMER_STARTED:
        return  # Only start once
    TIMER_STARTED = True

    def timer_loop():
        global GLOBAL_ELAPSED_SECONDS
        while True:
            time.sleep(1)
            GLOBAL_ELAPSED_SECONDS += 1
            if callback_every_second:
                callback_every_second(GLOBAL_ELAPSED_SECONDS)

    t = threading.Thread(target=timer_loop, daemon=True)
    t.start()


cached_instruments = []

GLOBAL_SESSION_COUNTER=1

GLOBAL_ELAPSED_SECONDS = 0
TIMER_STARTED = False

TEMP_ROW_STORAGE = {}