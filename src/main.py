"""main.py — runs after boot.py on every device boot.

Starts the HTTP command server and the fall watchdog (auto-recovery when
flipped over), each in a background thread, then returns so the main thread
stays free for WebREPL / interactive REPL access.
If a module is unavailable, continues so USB REPL works normally.
"""

try:
    import server

    server.run()
except Exception as e:
    print("Server error:", e)

try:
    import fall_watchdog

    fall_watchdog.start()
except Exception as e:
    print("Fall watchdog error:", e)
