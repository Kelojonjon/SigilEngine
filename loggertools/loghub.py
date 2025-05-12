
from logging.handlers import RotatingFileHandler
import logging
from pathlib import Path
from queue import Queue

from utilities.timermodule import TIMER
from sigilengine.space import LOGGER_SPACE
from sigilengine.space import LOGGER_LOCK

class LOGHUB():
    
    def __init__(self, hub_id):
        """
        Missing command_queue handling currently
        """
        # Alive flag
        self.alive = True
        # Similar to the canvases, loggers can be plenty,
        # they register themselves to the LOGGER_SPACE to be interacted with  
        self.hub_id = hub_id
        
            
        # Where all the logs are sent to be handled
        self.hub_queue = Queue()
        # Queue to send command packages to the central logger
        self.command_queue = Queue()
        
        
        # We will save the logs inside the "logs" subfolder of "loggertools"
        # Also handle creating a folder is none exists
        self.log_folder_path = Path(__file__).parent / "logs"
        self.log_folder_path.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_folder_path / f"{self.hub_id}.log"
        # The size of log files in MB
        self.log_file_size = 5
        
        # This logger will take the records format them, and write to the file
        self.minilogger = logging.getLogger(self.hub_id)
        self.rotating_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.log_file_size * 1024 * 1024,
            backupCount=3
        )
        
        # Format the log records and add handler to the minilogger
        formatter = logging.Formatter('%(asctime)s  | %(levelname)s | %(owner)s | %(entity_id)s | %(message)s')
        
        #TEST FORMATTER! MISSING OWNER AND CANVA_ID
        #formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        self.minilogger.addHandler(self.rotating_handler)
        self.rotating_handler.setFormatter(formatter)
        
        # We will write logs that are < loglevel 40 only every second, to prevent I/O spam
        # Errors and criticals are written instantly as they arrive, to hopefully catch them 
        self.file_buffer = []
        
        
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
            10: 0, # DEBUG
            20: 0, # INFO
            30: 0, # WARNING
            40: 0, # ERROR
            50: 0  # CRITICAL
        }

        self.timer = TIMER()
        self.timer.event(write_to_file=1)
        self.timer.action(write_to_file=self.write_buffered_records)
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
            
        
    def write_buffered_records(self):
        """
        Writes the whole file_buffer to a file, and flushes
        Timer
        """
        if len(self.file_buffer) > 0:
            for record in self.file_buffer:
                self.minilogger.handle(record)
            self.file_buffer.clear()
            
           
    def handle_my_record(self, record):
        levelno = record.levelno
        
        if record == None:
            return
        
        # Handle high priority without buffer        
        if levelno >= 40:
            self.minilogger.handle(record)
        # Append the record to file_buffer
        if levelno < 40:
            self.file_buffer.append(record)
       
              
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
                    # Check if time to write to the file
                    # Executes the write_buffered_records when it is the time
                    self.timer.update_timer()

                    item = self.hub_queue.get(timeout=0.1)
                    self.gatekeeper(item)
                except Exception:
                    continue # Idle loop
            
        # Shutdown    
        finally:
            with LOGGER_LOCK:
                LOGGER_SPACE.pop(self.hub_id, None)
                
  
