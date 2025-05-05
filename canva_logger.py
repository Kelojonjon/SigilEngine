import logging
from space import LOGGER_SPACE
from space import LOGGER_LOCK

"""

TODO add all the command packet stuff to the packet creator
TODO also handle them in the canva_thread parser
TODO 

🚀 Logger Plan Overview

Flow:
Canvas → logger.log(level, message + metadata) → handler.emit(record) → prebuffer (batch size N) → central queue → filtering → storage → file tailing

Components:
- Canvas logger:
    - logger = logging.getLogger(canvas_id)
    - registers itself into logger space (shared registry)
    - logging is auto-enabled when a logger is registered; 
      if no logger is registered, logging is effectively disabled
    - adds metadata: owner, canvas_id
    - batches messages into prebuffer to reduce spam

- Custom handler:
    - MyMonsterHandler
    - receives record → pushes into prebuffer

- Prebuffer:
    - holds raw records temporarily
    - batch size configurable (e.g., 10 messages)
    - flushes batch into central queue

- Central handler:
    - reads from central queue
    - applies:
        - per-level discard / sample rules (info, warning, error)
    - manages:
        - max buffer size
        - file write frequency
        - file rotation (max file size, retention count)
    - **no live render pipeline — file tailing only**

- Storage:
    - writes logs to file every X messages or seconds
    - rotates file when max size is reached

- File tailing:
    - users can monitor logs with external tools (e.g., `tail -f log.txt`)
    - supports filtering on canvas_id, owner (via log metadata)

Control options:
- Enable/disable logging dynamically (via logger space presence)
- Per-level sample rates
- Max queue / buffer sizes
- Max log file size & rotation count

✨ Notes:
- Canvas → minimal logic: batching + metadata only
- Prebuffer → smooths bursts, sends batches to central queue
- Central handler → handles filtering, rotation, file writing
- External tailing → live monitoring via file tools only
"""


class MyMonsterHandler(logging.Handler):
    """
    Custom handler that will append the records to the prebuffer
    Prebuffer will send records in batches to the central logging queue
    Anything above warning --> straight to the central logging queue
    """
    def __init__(self, buffer, canva_logger):
        super().__init__()
        self.log_buffer = buffer
        # We need this reference to dynamicly use the enabled flag from the canva_logger
        self.canva_logger = canva_logger
        
    def emit(self, log_record):
        if self.canva_logger.logging_enabled:
            if log_record.levelno <= 30:
                self.log_buffer.append(log_record)
            else:
                with LOGGER_LOCK:
                    LOGGER_SPACE["central"]
        else:
            return


class CANVA_LOGGER():
    """
    This logger is canvas-native each canvas will have its own little logger
    Logger wrapper that attaches the owner metadata automaticly
    Has functions to check the buffer size
    """
    def __init__(self, canvas_id, owner, batch_size=10):
        
        # Extra metadata for teh records
        self.owner = owner
        
        # Every buffer flush the alive flag of the central logger is checked
        # If its false we will set logging to false and make the emit function early return 
        # When re-enabling the central logging, the ocasiaonal check_log_buffer will 
        self.logging_enabled = False
        
        # We will send the logs the central queue in batches to limit spam
        # Messages above a certain level will skip this buffer
        self.log_buffer = []
        self.batch_size = batch_size

        # Setup the logger and handler/s
        self.logger = logging.getLogger(canvas_id) # Logger channel
        self.handler = MyMonsterHandler(self.log_buffer, self)
        #self.test_handler = logging.StreamHandler()
        
        # Add handlers to the logger
        self.logger.addHandler(self.handler)
        #self.logger.addHandler(self.test_handler)
        
        # Set the levels to pass everything trough DEBUG ---> CRITICAL
        self.logger.setLevel(logging.DEBUG)
        self.handler.setLevel(logging.DEBUG)
        #self.test_handler.setLevel(logging.DEBUG)
        
        # Set some pretty formatting for the handler/s
        formatter = logging.Formatter('%(name)s %(levelname)s %(asctime)s: %(message)s')
        self.handler.setFormatter(formatter)
        #self.test_handler.setFormatter(formatter)


    def set_log_batch(self, batch_size: int):
        """
        Set a new batch size, default on init is 10
        """
        if isinstance(batch_size, int) and batch_size > 0:
            self.batch_size = batch_size
        else:
            self.error("Logger batch size must be a integer and above 0")
    
    def check_log_buffer(self):
        """
        
        """
        with LOGGER_LOCK:
            if LOGGER_SPACE.get("central", False):
                self.logging_enabled = True
                if len(self.log_buffer) >= self.batch_size:
                    pass #TODO SEND TO CENTRAL QUEUE && CLEAR THE BUFFER
            else:
                self.logging_enabled = False
            
        
    def info(self, msg):
        self.logger.info(msg, extra={"owner": self.owner})
    
    def warning(self, msg):
        self.logger.warning(msg, extra={"owner": self.owner})
    
    def error(self, msg):
        self.logger.error(msg, extra={"owner": self.owner})
    
    def critical(self, msg):
        self.logger.critical(msg, extra={"owner": self.owner})
    
