
import logging
from queue import Queue
from space import SPACE
from space import SPACE_LOCK
from space import LOGGER_SPACE
from space import LOGGER_LOCK

class CENTRAL_LOGGER():
    
    def __init__(self):
        
        self.alive = True
        
        # Where all the logs are sent to be handled
        self.central_log_queue = Queue()
        # Queue to send command packages to the central logger
        self.command_queue = Queue()
        
        # Flags to decide if we handle levels
        self.handle_debug = True
        self.handle_info = True
        self.handle_warning = True
        self.handle_error = True
        self.handle_critical = True
        # Sample rates for different levels to reduce spam
        self.sample_debug = 1
        self.sample_info = 1
        self.sample_warning = 1
        self.sample_error = 1
        self.sample_critical = 1
    
    

    def run(self):
        
        # Init the LOGGER SPACE
        try:
            with LOGGER_LOCK:
                LOGGER_SPACE["central"] = {
                    "thread_obj": self,
                    "central_log_queue": self.central_log_queue,
                    "command_queue": self.command_queue
                }
            

        except Exception as e:
            return
        
        try:
            while self.alive:
                pass # TODO DO STUFF
                
        finally:
            with LOGGER_LOCK:
                LOGGER_SPACE.pop("central")
                
  