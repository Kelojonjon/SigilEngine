import logging
from sigilengine.space import LOGGER_SPACE
from sigilengine.space import LOGGER_LOCK


class MyMonsterHandler(logging.Handler):
    """
    Custom logging handler for the LOGFORWARDER
    
    References LOGFORWARDER state, with its attributes
    
    Appends logrecords below levelno 40 to a local logbuffer
    Above levelno 40 logrecords are sent straight to a loghub queue 
    
    If no loghub is not connected to the logforwarder logging is halted
    If a loghub is found, logging will resume automaticly
    """
    def __init__(self, buffer, logforwarder, loghub):
        super().__init__()
        
        # References for logforwarder instance, loghub, and the log_buffer
        self.logforwarder = logforwarder
        self.loghub = loghub
        self.log_buffer = buffer
        
    def emit(self, log_record):
        
        if self.logforwarder.logging_enabled:
            # Handle records under levelno 40
            if log_record.levelno < 40:
                self.log_buffer.append(log_record)
            # Handle records above levelno 40        
            else:
                with LOGGER_LOCK:
                    try:
                        LOGGER_SPACE[self.loghub]["hub_log_queue"].put(log_record)
                    except Exception:
                        return
        else:   
            return


class LOGFORWARDER():
    """
    Allows creating logrecords with extra metada using custom logger functions
    Handles routing the logrecords to LOGHUB module
    
    If a LOGHUB is set, automaticly detects if LOGHUB is running and reachable trough LOGGER_SPACE
    If no valid LOGHUB exists, logging is automaticly halted
    
    Uses buffered forwarding with anything < levelno 40
    Batch sizes are controllable (From the state variable at the moment only)
    Logrecords with higher than 40 levelno, skip this buffer
    
    Buffer flushing happens by placing the check_log_buffer function in a external loop  
    """
    def __init__(self, loghub, entity_id="unset", owner="unset", batch_size=10):
        
        # LOGFORWARDER targets this loghubs queue
        self.loghub = loghub
        # False if no valid LOGHUB set
        self.logging_enabled = False
        
        # Logbuffer and its batchsize
        self.log_buffer = []
        self.batch_size = batch_size

        # Setup the logger and handler/s
        self.logger = logging.getLogger(entity_id)
        self.handler = MyMonsterHandler(self.log_buffer, self, loghub) # CUSTOM handler
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)
        self.handler.setLevel(logging.DEBUG)
        
        # Extra metadata for extra identifying
        self.owner = owner
        self.entity_id = entity_id # Choose a name for the logger
        
        
    def log_batch_size(self, batch_size: int):
        """
        Update the batch size used when flushing the log buffer.

        Only accepts integers greater than zero.
        If the input is invalid, logs an error using the internal logger.
        """
        
        # input validation to check for int and > 0
        if isinstance(batch_size, int) and batch_size > 0:
            self.batch_size = batch_size
        else:
            self.error("Logger batch size must be a integer and above 0")
    
    
    def check_log_buffer(self):
        """
        Flushes buffered logs to LOGHUB if reachable.

        If loghub exists and buffer has enough records,
        forwards them to hub_log_queue. Disables logging
        if hub is missing. Errors are silently ignored.
        """
        with LOGGER_LOCK:
            
            if LOGGER_SPACE.get(self.loghub, False):
                # If LOGHUB is found enable logging
                self.logging_enabled = True    
                if len(self.log_buffer) >= self.batch_size:
                    try:
                        LOGGER_SPACE[self.loghub]["hub_log_queue"].put(self.log_buffer.copy())
                        self.log_buffer.clear()
                    except Exception:
                        return
            # If no loghub  is found disable logging
            else:
                self.logging_enabled = False
           
           
    # Custom "print" functions that attaches "owner" and "entity_id" fields and sends them to be logged
    def info(self, msg):
        self.logger.info(msg, extra={"owner": self.owner, "entity_id": self.entity_id})

    def warning(self, msg):
        self.logger.warning(msg, extra={"owner": self.owner, "entity_id": self.entity_id})

    def error(self, msg):
        self.logger.error(msg, extra={"owner": self.owner, "entity_id": self.entity_id})

    def critical(self, msg):
        self.logger.critical(msg, extra={"owner": self.owner, "entity_id": self.entity_id})
