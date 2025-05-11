from queue import Queue
from utilities.timermodule import TIMER
from sigilengine.space import SPACE
from sigilengine.space import SPACE_LOCK
from sigilengine.ascii_screen import ASCII_SCREEN
from loggertools.canva_logger import CANVA_LOGGER


class CANVA_THREAD():
    
    """
    Canvas Thread that manages its own state, rendering, and message forwarding.
    
    CANVA_THREAD runs as an independent thread with its own queue, state variables,
    and message handling. It can operate standalone or as part of a chain of
    canvases that forward rendered content to each other.
    
    Each thread registers itself in the global SPACE registry, allowing other
    threads to discover and communicate with it. This design enables complex
    compositions of canvases with minimal coupling.
    """
    
    def __init__(
        self,
        canvas_id, 
        owner, 
        height,
        width,
        fillvalue = "·", 
        host = None, 
        visible = True,   
        origin_yx = (1,1),
        loghub = None
        ):
        """
        Initialize a CANVA_THREAD instance.

        Args:
            canvas_id (str): Name of the canvas.
            owner (str): Name of the process or owner managing the thread.
            height (int): Height of the canvas.
            width (int): Width of the canvas.
            fillvalue (str, optional): Character used to fill empty cells on the canvas. Defaults to "·".
            groups (list, optional): List of groups or tags associated with this canvas. Defaults to None.
            host (str, optional): ID of the host canvas. The thread will forward its local canvas only to this host. Defaults to None.
            visible (bool, optional): Whether the canvas is visible. Defaults to True.
            origin_yx (tuple, optional): Initial (y, x) placement coordinates on the host canvas. Defaults to (1, 1).
        """

        # Alive flag for the run loop
        self.alive = True

        self.canvas_id = canvas_id
        self.owner = owner
        self.host = host
 
        self.origin_yx = origin_yx
        self.height = height
        self.width = width
        self.fill_value = fillvalue
        self.visible = visible

        # Canvas sized y.x chart that starts from the origin_yx coordinates 
        self.conversion_chart = None
        
        # Command queue that the ´parse_packet´ is monitoring for recieved packets
        self.queue = Queue()
        # Canvas buffer
        self.canvas = None

        # Canvas buffer that follows ´host_id'dimensions fetched from the SPACE registry, if they exists. 
        self.host_ref_canvas = None
        self.host_height = None
        self.host_width = None
        
        # Log handler is the central address where all the logs are sent to being handled
        # If no handler is set or if it doesnt exist, logging will be disabled
        self.loghub = loghub
        # Logger module, the default prebuffer size for logger records is 10
        self.logger = CANVA_LOGGER(self.canvas_id, self.owner, self.loghub)
        # Seconds interval the logger_buffer lenght will be checked 
        
        # Timer module
        self.timer = TIMER()
        
        # Ecents added to the timer
        self.timer.event(self.logger.check_log_buffer, logevent=10)

    #############################################################
    
    
    def sync_to_space(self):
        """
        Update the global SPACE registry with this canvas's current state.

        Synchronizes the canvas dimensions and visibility status with the global
        SPACE registry, ensuring that other canvases have accurate information
        about this canvas when they need to interact with it.
        """
        with SPACE_LOCK:
            SPACE[self.canvas_id].update({
                "height": self.height,
                "width": self.width,
                "visible": self.visible,
            })
            #print(f"[{self.canvas_id}] 🧾 State synced → SPACE: height={self.height}, width={self.width}, visible={self.visible}")

    
    def clear_canvas(self):
        """
        Reset the canvas buffer to its default state.
        
        Regenerates the canvas using current state variables (ID, owner, dimensions,
        fill value, visibility). This effectively clears all content while maintaining
        the canvas configuration.
        """
        self.canvas = ASCII_SCREEN.create_canvas(self.canvas_id, self.owner, self.height, self.width, self.fill_value, self.visible)
    
    def check_host(self):
        """
        Check if the configured host exists in the SPACE registry.
        
        Returns:
            bool: True if the host exists in SPACE, False otherwise or if no host is set.
        """
        if not self.host:
            return False
        with SPACE_LOCK:
            host = SPACE.get(self.host, False)
            return bool(host)      
    
    def sync_host(self):
        """
        Sync this canvas with its host.
        
        Performs the following operations:
        1. Pulls host dimensions from SPACE registry
        2. Creates a reference canvas matching host dimensions
        3. Generates a conversion chart for coordinate mapping
        4. Draws debug borders on the reference canvas
        
        This method is essential for proper canvas chaining.
        """
            
        if not self.host:
            #print(f"[{self.canvas_id}] 💤 No host assigned")
            return
        
        with SPACE_LOCK:
            host_data = SPACE.get(self.host)
            
        if not host_data:
            #print(f"[{self.canvas_id}] ❌ Cannot set host — '{self.host}' not found in SPACE.")
            return

        self.host_height = host_data.get("height")
        self.host_width = host_data.get("width")
        
        self.host_ref_canvas = ASCII_SCREEN.create_ref_canvas(self.host_height, self.host_width)
        #print(f"[{self.canvas_id}] Host id: [{self.host}] Host size: {self.host_height} x {self.host_width}")

        self.conversion_chart = ASCII_SCREEN.generate_coords(self.origin_yx, self.height, self.width)
        
        ASCII_SCREEN.box_borders(self.host_ref_canvas, self.origin_yx, self.height, self.width)
        

    def kill(self):
        """
        Terminate the thread and remove it from SPACE.
        
        This method is called when a "!kill" command is received.
        It removes the canvas from the global registry and sets
        the alive flag to False, which will cause the thread to exit.
        """  
        with SPACE_LOCK:
            SPACE.pop(self.canvas_id, None)
        self.alive = False
        print(f"[{self.canvas_id}] 💀 Marked as dead by '!kill'.")
        
        
    def set_host(self, host_id: str):
        """
        Set a new host canvas for this thread.
        
        Updates the host reference and resyncs dimensions with the new host.
        If the specified host doesn't exist in SPACE, no change occurs.
        
        Args:
            host_id (str): ID of the new host canvas.
        """
        with SPACE_LOCK:
            if host_id not in SPACE:
                #print(f"[{self.canvas_id}] ❌ Cannot set host — '{host_id}' not found in SPACE.")
                return
            
        self.host = host_id
        #print(f"[{self.canvas_id}] 🔁 Host set to '{self.host}'. Resyncing...")
        self.sync_host()
    
    
    def set_origin(self, new_origin: tuple):
        """
        Update the origin position of this canvas on its host.
        
        Changes where this canvas will appear when rendered on its host.
        Regenerates the conversion chart for coordinate mapping and rebuilds
        the host reference canvas if a host is configured.
        
        Args:
            new_origin (tuple): New (y, x) coordinates where this canvas should be positioned.
                               Negative values are allowed for off-screen positioning.
        """
        self.origin_yx = new_origin
        self.conversion_chart = ASCII_SCREEN.generate_coords(self.origin_yx, self.height, self.width)

        if self.host:
            self.sync_host()  # Rebuild host_ref_canvas and overlay

        #print(f"[{self.canvas_id}] 🎯 Origin set to {self.origin_yx}")

    
    def resize_canvas(self, new_height: int, new_width: int):
        """
        Resize the internal canvas buffer.
        
        Recreates the canvas with new dimensions, updates SPACE registry,
        and resyncs with host if one is configured.
        
        Args:
            new_height (int): New height for the canvas.
            new_width (int): New width for the canvas.
        """
        self.height = new_height
        self.width = new_width
        self.canvas = ASCII_SCREEN.create_canvas(
            self.canvas_id,
            self.owner,
            self.height,
            self.width,
            self.fill_value,
            self.visible
        )
        self.sync_to_space()
        #print(f"[{self.canvas_id}] 📏 Canvas resized to {self.height}x{self.width}")

        if self.host:
            self.sync_host()


    def set_fillvalue(self, char: str):
        """
        Set the default fill value for the canvas.
        
        Updates the character used for empty cells and regenerates
        the canvas to apply the change. Also resyncs with host if needed.
        
        Args:
            char (str): Character to use for filling empty cells.
                       Should be a single character for proper grid display.
        """

        self.fill_value = char
        self.canvas = ASCII_SCREEN.create_canvas(
            self.canvas_id,
            self.owner,
            self.height,
            self.width,
            self.fill_value,
            self.visible
        )

       #print(f"[{self.canvas_id}] 🪄 Fill value set to '{self.fill_value}' and canvas refreshed.")

        if self.host:
            self.sync_host()
    

    def parse_packet(self, packet):
        """
        Process and execute commands from an incoming packet.
        
        This is the core command processor for the canvas thread.
        It handles various operations like writing, forwarding,
        resizing, and other state changes based on the incoming packet.
        
        Supported commands:
            - "write" - Write content locally
            - "auto_forward" - Write locally and forward to host
            - "forward_to" - Write locally and forward until target
            - "resize" - Change canvas dimensions
            - "set_origin" - Reposition on host
            - "set_host" - Change host canvas
            - "set_fillvalue" - Change default fill character
            - "clear" - Regenerate canvas
            - "!kill" - Terminate thread
            
        Args:
            packet (dict): Command packet with "command", "chart", and "metadata" keys.
        """
        
        command_package = packet.get("command") # Nested dict
        chart = packet.get("chart")
        metadata = packet.get("metadata")

        command = command_package.get("cmd") # Command
        args_package = command_package.get("args", {}) # Dict or args  
        
        # Some basic checking to see if the packet arrived intact
        # Could be later replaced with checksum          
        if not isinstance(packet, dict):
            #print(f"[{self.canvas_id}] ❌ Malformed packet — not a dict.")
            return
        
        if not command_package:
            #print(f"[{self.canvas_id}] ⚠️ Received packet without a command block.")
            return

        elif command == "write":
            written = ASCII_SCREEN.zip_and_write(self.canvas, chart, metadata)
            #print(f"[{self.canvas_id}] ✍️ Wrote {written} cells.") # Debug


        elif command == "forward_to":
            written = ASCII_SCREEN.zip_and_write(self.canvas, chart, metadata)
            #print(f"[{self.canvas_id}] ✍️ Wrote {written} cells.")

            target_id = args_package.get("canvas_id")
            if target_id == self.canvas_id:
                #print(f"[{self.canvas_id}] 🛑 Packet reached target canvas. Not forwarding further.")
                return

            host_check = self.check_host()
            if host_check:
                forward_chart = []
                forward_metadata = []
                
                # Scan through the canvas to find all non-fill characters
                for y in range(1, self.height + 1):
                    for x in range(1, self.width + 1):
                        cell = self.canvas[y][x]
                        # Only forward cells that have actual content
                        if cell['char'] != self.fill_value:
                            # Calculate position on host canvas
                            host_y = self.origin_yx[0] + (y - 1)
                            host_x = self.origin_yx[1] + (x - 1)
                            forward_chart.append((host_y, host_x))
                            forward_metadata.append(cell)
                
                # Only forward if we found content to forward
                if forward_chart and forward_metadata:
                    packet = {
                        "command": {
                            "cmd": "forward_to",
                            "args": {"canvas_id":  args_package.get("canvas_id")}
                        },
                        "chart": forward_chart,
                        "metadata": forward_metadata
                    }
                    with SPACE_LOCK:
                        host_queue = SPACE.get(self.host).get("queue")
                    if host_queue:
                        host_queue.put(packet)
                        #print(f"[{self.canvas_id}] 🚀 Forwarded {len(forward_metadata)} cells to host '{self.host}'")
                        
                               
        elif command == "auto_forward":
            # First, write the content to the local canvas
            written = ASCII_SCREEN.zip_and_write(self.canvas, chart, metadata)
            #print(f"[{self.canvas_id}] ✍️ Wrote {written} cells.")

            host_check = self.check_host()
            # Only forward if we successfully wrote something and have a host
            if written > 0 and host_check:
                # Create new chart and metadata arrays for forwarding
                forward_chart = []
                forward_metadata = []
                
                # Scan through the canvas to find all non-fill characters
                for y in range(1, self.height + 1):
                    for x in range(1, self.width + 1):
                        cell = self.canvas[y][x]
                        # Only forward cells that have actual content
                        if cell['char'] != self.fill_value:
                            # Calculate position on host canvas
                            host_y = self.origin_yx[0] + (y - 1)
                            host_x = self.origin_yx[1] + (x - 1)
                            forward_chart.append((host_y, host_x))
                            forward_metadata.append(cell)
                
                # Only forward if we found content to forward
                if forward_chart and forward_metadata:
                    packet = {
                        "command": {
                            "cmd": "auto_forward",
                            "args": {}
                        },
                        "chart": forward_chart,
                        "metadata": forward_metadata
                    }
                    with SPACE_LOCK:
                        host_queue = SPACE.get(self.host).get("queue")
                    if host_queue:
                        host_queue.put(packet)
                        #print(f"[{self.canvas_id}] 🚀 Forwarded {len(forward_metadata)} cells to host '{self.host}'")
              
                    
        elif command ==  "clear":
            self.clear_canvas()
        
        elif command == "resize":
            h = args_package.get("height")
            w = args_package.get("width")
            self.resize_canvas(h, w)

        elif command == "set_origin":
            y = args_package.get("y")
            x = args_package.get("x")
            yx = y, x 
            self.set_origin(yx)

        elif command == "set_host":
            self.set_host(args_package.get("host"))

        elif command == "set_fillvalue":
            self.set_fillvalue(args_package.get("fillvalue"))

        elif command == "!kill":
            self.kill()
            
        else:
            #print(f"[{self.canvas_id}] ⚠️ Unknown command: {command}")
            return
        
    def run(self):
        """
        Main thread loop that processes the command queue.
        
        This method initializes the canvas, registers it in SPACE,
        and then enters a processing loop where it:
        1. Waits for commands on the queue
        2. Processes each command via parse_packet
        3. Continues until killed or marked as not alive
        4. Cleans up by removing itself from SPACE
        
        All canvas threads have this as their entry point.
        """
        # Init the local canvas
        try:
            with SPACE_LOCK:
                SPACE[self.canvas_id] = { # Init to the global thread-canvas register
                    "id": self.canvas_id,
                    "owner": self.owner,
                    "height": self.height,
                    "width": self.width,
                    "visible": self.visible,
                    "queue": self.queue, # Queue address
                    "thread_obj": self,  # Thread reference
            } 
            self.canvas = ASCII_SCREEN.create_canvas(
                self.canvas_id,
                self.owner,
                self.height,
                self.width,
                self.fill_value,
                self.visible)
        
        except Exception as e:
            #print(f"[{self.canvas_id}] ❌ Canvas init failed: {e}")
            return
        
       
        #print(f"[{self.canvas_id}] 🖼️ Canvas created ({self.height}x{self.width}) with fill '{self.fill_value}' — visible: {self.visible}")
        # Try to init the host_ref canvas
        self.sync_host()
        
        
        #print(f"[THREAD {self.canvas_id}] Running.")
        
        try:
            while self.alive:
                try:
                    # Execute all the scheduled events, based on their attributes
                    self.timer.update_timer()
                    cmd = self.queue.get(timeout=0.1)
                    self.parse_packet(cmd)
                except Exception:
                    continue # Idle loop 
        finally:
            with SPACE_LOCK:
                SPACE.pop(self.canvas_id, None)
            #print(f"[{self.canvas_id}] 🚪 Exiting thread cleanly.")