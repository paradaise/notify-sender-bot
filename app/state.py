import threading

# Global state variables
tasks = {}
broadcast_thread = None
stop_event = threading.Event() 