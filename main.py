"""main.py — runs after boot.py on every device boot.

Starts the HTTP command server in a background thread, then returns
so the main thread stays free for WebREPL / interactive REPL access.
If the server module is unavailable, exits silently so USB REPL works normally.
"""
try:
    import server
    server.run()
except Exception as e:
    print("Server error:", e)
