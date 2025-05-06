
import logging
from queue import Queue
from space import SPACE
from space import SPACE_LOCK
from space import LOGGER_SPACE
from space import LOGGER_LOCK

class LOGHUB():
    
    def __init__(self, hub_id):
        
        # Alive flag
        self.alive = True
        # Similar to the canvases, loggers can be plenty,
        # they register themselves to the LOGGER_SPACE to be interacted with  
        self.hub_id = hub_id
        
        
        # Where all the logs are sent to be handled
        self.hub_queue = Queue()
        # Queue to send command packages to the central logger
        self.command_queue = Queue()
        
        
        # Flags to decide if we handle levels
        # Both filters work directly with the logger levelno's
        self.level_filter = {
            10: True,   # DEBUG
            20: True,   # INFO
            30: True,   # WARNING
            40: True,   # ERROR
            50: True    # CRITICAL
        }
        
        # Sample rates for different levels to reduce spam
        self.sample_filter = {
            10: 1, # DEBUG
            20: 1, # INFO
            30: 1, # WARNING
            40: 1, # ERROR
            50: 1  # CRITICAL
        }

        # Helper counter for the sample_filtering
        self.sample_counter = {
            10: 1, # DEBUG
            20: 1, # INFO
            30: 1, # WARNING
            40: 1, # ERROR
            50: 1  # CRITICAL
        }

        self.formatter = logging.Formatter('%(name)s %(levelname)s %(asctime)s: %(message)s')
    
    
    ##################################################################################################
    
    
    def filter(self, record):
        """
        Appliess the filtering rules to a single record
        """
        levelno = record.levelno
        
        # Check if the levelno is set to be handled
        condition = self.level_filter.get(levelno, 1)
        if condition == False:
            return None
        
        # Cycle the sample counter  
        counter = self.sample_counter.get(levelno, 1) + 1
        # If counter goes over the sample rate, reset and return the record
        if counter >= self.sample_filter.get(levelno, 1):
            self.sample_counter[levelno] = 0
            return record
        
        return None
        
        
    
    def gatekeeper(self, item):
        """
        Flattens the lists, routes the records trough the filter
        and then sends the records to be handled
        """
        if isinstance(item, list):
            for record in item:
                filtered_record = self.filter(record)
                self.handle_my_record(filtered_record)
        else:
            filtered_item = self.filter(item)
            self.handle_my_record(filtered_item)
                
            
    
    def run(self):
        
        # Init 
        try:
            with LOGGER_LOCK:
                LOGGER_SPACE[self.hub_id] = {
                    "thread_obj": self,
                    "hub_log_queue": self.hub_queue,
                    "hub_command_queue": self.command_queue
                }
        except Exception as e:
            return
        
        # Loop
        try:
            while self.alive:
                try:
                    item = self.hub_queue.get(timeout=0.1)
                    self.gatekeeper(item)
                except Exception:
                    continue # Idle loop
            
        # Shutdown    
        finally:
            with LOGGER_LOCK:
                LOGGER_SPACE.pop(self.hub_id, None)
                
  