from threading import Lock

"""
Global registry and synchronization lock for canvas threads.

SPACE:
    A global dictionary storing all active CANVA_THREAD instances.
    Tracks dimensions, queues, and thread addresses.

SPACE_LOCK:
    A global threading.Lock to prevent race conditions
    during access, registration, or removal of canvases.
"""

SPACE = {}
SPACE_LOCK = Lock()