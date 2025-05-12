import logging
from sigilengine.space import LOGGER_SPACE
from sigilengine.space import LOGGER_LOCK


class MyMonsterHandler(logging.Handler):
    """
    Custom handler that will append the records to the prebuffer
    Prebuffer will send records in batches to the central logging queue
    Anything above warning --> straight to the central logging queue
    """
    def __init__(self, buffer, logforwarder, loghub):
        super().__init__()
        self.log_buffer = buffer
        # We need this reference to dynamicly use the enabled flag from the canva_logger
        self.logforwarder = logforwarder
        self.loghub = loghub
        
    def emit(self, log_record):
        if self.logforwarder.logging_enabled:
            if log_record.levelno <= 30:
                self.log_buffer.append(log_record)
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
    This logger is canvas-native each canvas will have its own little logger
    Logger wrapper that attaches the owner metadata automaticly
    Has functions to check the buffer size
    The same logger will be usable in the main structure its not only canvas native
    Will have to rename the thing to something more generic XD
    """
    def __init__(self, loghub, entity_id="unset", owner="unset", batch_size=10):
        
        # Extra metadata for teh records
        self.owner = owner
        self.entity_id = entity_id # The "entity" being logged
        
        # Every buffer flush the alive flag of the central logger is checked
        # If its false we will set logging to false and make the emit function early return 
        # When re-enabling the central logging, the ocasiaonal check_log_buffer will make sure
        # the logging will be enabled again
        self.logging_enabled = False
        
        # We will send the logs the central queue in batches to limit spam
        # Messages above a certain level will skip this buffer
        self.log_buffer = []
        self.batch_size = batch_size

        # Logs will be sent here to be processed, could later allow acting as a forwarder to other hubs
        self.loghub = loghub
        
        # Setup the logger and handler/s
        self.logger = logging.getLogger(entity_id) # Logger channel
        self.handler = MyMonsterHandler(self.log_buffer, self, loghub)


        # Add handlers to the logger
        self.logger.addHandler(self.handler)

        # Set the levels to pass everything trough DEBUG ---> CRITICAL
        self.logger.setLevel(logging.DEBUG)
        self.handler.setLevel(logging.DEBUG)

        
    def log_batch_size(self, batch_size: int):
        """
        Set a new batch size, default on init is 10
        """
        # TODO handle the checking in the create packet later 
        if isinstance(batch_size, int) and batch_size > 0:
            self.batch_size = batch_size
        else:
            self.error("Logger batch size must be a integer and above 0")
    
    def check_log_buffer(self):
        """
        Check if central logger is alive and flush batch if needed.
        """
        with LOGGER_LOCK:
            if LOGGER_SPACE.get(self.loghub, False):
                self.logging_enabled = True
                if len(self.log_buffer) >= self.batch_size:
                    # Use try so if the central_log_queue is full or the central is down
                    # it doesnt crash the canva_thread
                    try:
                        LOGGER_SPACE[self.loghub]["hub_log_queue"].put(self.log_buffer.copy())
                        self.log_buffer.clear()
                    except Exception:
                        return
            else:
                self.logging_enabled = False
            
    def info(self, msg):
        self.logger.info(msg, extra={"owner": self.owner, "entity_id": self.entity_id})

    def warning(self, msg):
        self.logger.warning(msg, extra={"owner": self.owner, "entity_id": self.entity_id})

    def error(self, msg):
        self.logger.error(msg, extra={"owner": self.owner, "entity_id": self.entity_id})

    def critical(self, msg):
        self.logger.critical(msg, extra={"owner": self.owner, "entity_id": self.entity_id})
