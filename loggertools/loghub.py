
from logging.handlers import RotatingFileHandler
import logging
from pathlib import Path
from queue import Queue

from utilities.timermodule import TIMER
from sigilengine.space import LOGGER_SPACE
from sigilengine.space import LOGGER_LOCK


class LOGHUB():
    """
    Threaded module that hosts queues for logrecords and commands.
    
    Logrecords are filtered and written to a file in format:  asctime | levelname | owner | entity_id | message
    Logs are rotated between 3 files using RotatingFileHandler.
    Records with levelno that's equal or above 40, get handled ASAP, lower loglevels are written in batches
    
    Currently all loglevels are collected via 1 public queue
    Uses buffering and timed event scheduling to limit I/O spam
    Filters levels with True flags, and uses sample rating.
    
    Command queue is defined but not currently handled.
    """
    
    def __init__(self, hub_id):
        
        # Alive flag
        self.alive = True
       
        # Name of the hub 
        self.hub_id = hub_id
        
        # Queues hosted in the LOGGER_SPACE
        self.hub_queue = Queue()
        self.command_queue = Queue()
        
        
        # Log folder path, creates a "logs" folder, that is stored in the same folder that the code is being executed from.
        self.log_folder_path = Path(__file__).parent / "logs"
        self.log_folder_path.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_folder_path / f"{self.hub_id}.log"
        # The size of log files in MB
        self.log_file_size = 5
        
        # File I/O is handled via sublogger and a RotatingFileHandler
        self.minilogger = logging.getLogger(self.hub_id)
        self.rotating_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.log_file_size * 1024 * 1024,
            backupCount=3
        )
        self.minilogger.addHandler(self.rotating_handler)
        
        # Format the records, 
        formatter = logging.Formatter('%(asctime)s  | %(levelname)s | %(owner)s | %(entity_id)s | %(message)s')
        self.rotating_handler.setFormatter(formatter)
        
        
        # A Buffer holding records before the I/O cycle, thats handled using a timer 
        self.file_buffer = []
        
        # Timer that flushes the buffered records to a file
        self.timer = TIMER()
        self.timer.event(write_to_file=1) # 1 second interval
        self.timer.action(write_to_file=self.write_buffered_records)
        
        
        # Filtering using True flags and Sample rating
        # True == Records get passed trough
        self.level_filter = {
            10: True,   # DEBUG
            20: True,   # INFO
            30: True,   # WARNING
            40: True,   # ERROR
            50: True    # CRITICAL
        }
        
        # Sample rating, default is 1/1
        self.sample_filter = {
            10: 1, # DEBUG
            20: 1, # INFO
            30: 1, # WARNING
            40: 1, # ERROR
            50: 1  # CRITICAL
        }

        # Used in keeping track of the sample rates.
        self.sample_counter = {
            10: 0, # DEBUG
            20: 0, # INFO
            30: 0, # WARNING
            40: 0, # ERROR
            50: 0  # CRITICAL
        }


    ##################################################################################################
    
    
    def filter(self, record):
        """
        Applies the filtering rules to a single logrecord
        """
        levelno = record.levelno
        
        # Check if the levelno is set to be handled
        condition = self.level_filter.get(levelno, 1)
        if condition == False:
            return None
        
        counter = self.sample_counter.get(levelno, 1) + 1
        
        # If counter goes over the sample rate, reset and return the logrecord
        if counter >= self.sample_filter.get(levelno, 1):
            self.sample_counter[levelno] = 0
            return record
        
        return None
            
           
    def handle_my_record(self, record):
        """
        Either handles important logrecords ASAP, or appends them to the I/O file_buffer
        """
        
        if record == None:
            return

        levelno = record.levelno
        
        # Handle high priority without buffer        
        if levelno >= 40:
            self.minilogger.handle(record)
        # Append the logrecord to file_buffer
        if levelno < 40:
            self.file_buffer.append(record)
       
              
    def gatekeeper(self, item):
        """
        Entry point for all incoming logrecords.
        Handles the flattening, if logrecords come in a list
        Calls handle_my_record every logrecord.
        """
        # If item is a list, flatten it down, and pass forward
        if isinstance(item, list):
            for record in item:
                filtered_record = self.filter(record)
                self.handle_my_record(filtered_record)
        # Else just pass forward
        else:
            filtered_item = self.filter(item)
            self.handle_my_record(filtered_item)
                
            
    def write_buffered_records(self):
        """
        Flushes all records from the file buffer and writes them to file.
        """
        if len(self.file_buffer) > 0:
            for record in self.file_buffer:
                self.minilogger.handle(record)
            self.file_buffer.clear()
                    
            
    def run(self):
        """
        Runs the loop
        Loghub registers itself to LOGGER_SPACE
        Loops and listens for the queue/s
        """
        # Registers to LOGGER_SPACE
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
                    # Checks if  it is time to write to the file
                    self.timer.update_timer()

                    # Handles incoming Traffic
                    item = self.hub_queue.get(timeout=0.1)
                    self.gatekeeper(item)
                
                except Exception:
                    continue # Idle loop
            
        # Deletes itself from LOGGER_SPACE when the loop ends 
        finally:
            with LOGGER_LOCK:
                LOGGER_SPACE.pop(self.hub_id, None)
                
  
