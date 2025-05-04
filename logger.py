import logging
from space import LOGGER_SPACE

"""
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
    Prebuffer will send records in batches to the central logging handler
    """
    def __init__(self, buffer):
        # Inherit the handler init :D
        super().__init__()
        def emit():
            pass


class CANVA_LOGGER():
    """
    Logger wrapper that attaches the owner metadata automaticly
    """
    def __init__(self, canvas_id, owner, batch_size=10):
        
        self.owner = owner
        
        # We will send the logs the central queue in batches to limit spam
        self.buffer = []
        self.batch_size = batch_size
    
        self.handler = MyMonsterHandler(self.buffer)
        self.logger = logging.getLogger(canvas_id) # Logger channel
        
        
        self.logger.setLevel(logging.DEBUG) # Filtering will be handled later
        self.handler.setLevel(logging.DEBUG)
        

    def info(self, msg):
        self.logger.info(msg, extra={"owner": self.owner})
    
    def warning(self, msg):
        self.logger.warning(msg, extra={"owner": self.owner})
    
    def error(self, msg):
        self.logger.error(msg, extra={"owner": self.owner})
    
    def critical(self, msg):
        self.logger.critical(msg, extra={"owner": self.owner})
    
