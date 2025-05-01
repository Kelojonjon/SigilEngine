

from ascii_screen import ASCII_SCREEN


class PACKET_CREATOR():
    
    """
    This class creates ready made packet structures, that can be sent
    to canvas, to be parsed and executed
    
    Most of the error handling happens here, CANVA_THREAD expects mostly pure packets
    
    Packets are sent to canva_parser to be parsed and executed.
    Canva parser directly calls methods in CANVA_THREAD and ASCII_SCREEN.
    CANVA_THREAD handles its own state with ASCII_SCREEN and its own class specific tools
    """
    

    def __init__(self, width):
        """
        Initialize the PACKET_CREATOR with the desired content width for wrapping.
        """
        self.content_origin = (1,1)
        self.target_width = width
        self.template = None

    
    def set_template(self, template: dict):
        """
        Template where the addittional metadata will be injected.
        Currently only 'char' is supported
        Example use
        
        template = {'char': '@'}
        PACKET_CREATOR.set_template(template)
        """
        if isinstance(template, dict):
            self.template = template

        
    def set_content_origin(self, origin: tuple):
        """
        Set the starting (y, x) coordinate for content placement on the target canvas.
        Default origin is (1,1), origin can be placed out of bounds.
        Only content thats inside the canvas will be written.
        Out of bounds content will be skipped in writing process
        
        The origin must be a tuple of two integers (y, x)
        Example use
        
        PACKET_CREATOR.set_content_origin((10,15))
        """
        if isinstance(origin, tuple) and len(origin) == 2 and isinstance(origin[0], int) and isinstance(origin[1], int):
            self.content_origin = origin
        
    
    def set_origin_on_host(self, host_origin: tuple):
        """
        Moves the targeted canvas around on its host canvas.
        You don’t need to specify the host ID — the canvas tracks its own host internally.
        Example use
        
        PACKET_CREATOR.set_origin_on_host((10,30))
        """
        if isinstance(host_origin, tuple) and len(host_origin) == 2 and isinstance(host_origin[0], int) and isinstance(host_origin[1], int):
            return {
                "command": {
                    "cmd": "set_origin",
                    "args": {"y": host_origin[0], "x": host_origin[1]}
                }
            }
            

    def set_host(self, host_id: str):
        """
        Set a new host for a canvas by ID.
        The target canvas will validate if the host exists in SPACE 
        If the host does not exist, the canvas will keep its current host.
        Example use
        
        PACKET_CREATOR.set_host(host_id)
        """
        return {
            "command": {
                "cmd": "set_host",
                "args": {"host": host_id}
            }
        }
    

    def clear_canvas(self):
        """
        Generate a new canvas using the CANVA_THREAD state variables 
        Overwrites everything on the buffer
        """
        return {
            "command": {
                "cmd": "clear",
                "args": {}
            }
        }
    

    def set_target_width(self, width: int):
        """
        Set a target width for chart generation.
        The contents will wrap around at this width.
        Has no Y limit, so long texts might overflow on the canvas
        Example use
        
        PACKET_CREATOR.set_target_width(20)
        """
        if isinstance(width, int) and width > 0:
            self.target_width = width
        
        
    def resize_canvas(self, height: int, width: int):
        """
        Resize the target canvas.
        Resizing will generate a new buffer and will overwrite,
        everything that might be written on the buffer
        Example use
        
        PACKET_CREATOR.resize_canvas(50, 100)
        """
        if height > 0 and isinstance(height, int) and width > 0 and isinstance(width, int):
            return {
                "command": {
                    "cmd": "resize",
                    "args": {"height": height, "width": width}
                }
            } 
            

    def kill_canvas(self):
        """
        Generate a kill command packet for the target canvas.
        The CANVA_THREAD will handle its own removal from the SPACE registry.
        Example use
        
        PACKET_CREATOR.kill_canvas()
        """
        return {
            "command": {
                "cmd": "!kill",
                "args": {}
            }
        }
        

    def set_fillvalue(self, char: str):
        """
        Set the default character used to fill the canvas when it’s generated.
        This is useful for setting a placeholder character that can later be
        rendered as a space or ignored.
        Example use
        
        PACKET_CREATOR.set_fillvalue("@")
        """
        if isinstance(char, str):
            return {
                "command": {
                    "cmd": "set_fillvalue",
                    "args": {"fillvalue": char}
                }
            }   

    
    def write_to_canvas(self, message: str):
        """
        Take a string input and automatically generate a chart matching its length.

        The chart will be generated using the "target_width" variable.
        "target_width" dictates how the message will be wrapped on the target canvas.
        
        All the characters will be injected onto the chosen template as 'char' type
        
        Used to write on a single canvas, for chaining write operations
        use "auto_forward" or "forward_to" commands
        Example use
        
        PACKET_CREATOR.write_to_canvas("Hello World!")
        """
        if isinstance(message, str) and len(message) > 0:
            chart = ASCII_SCREEN.generate_wrapped_chart(self.content_origin, message, self.target_width)
            
            metadata = []
            for char in message:
                if char == "\n":
                    continue
                char_data = {"char": char}
                if self.template:
                    template_copy = self.template.copy()
                    char_data.update(template_copy)
                metadata.append(char_data)
            
            return {
                "command": {
                    "cmd": "write",
                    "args": {}
                },
                "chart": chart,
                "metadata": metadata
            }
        

    def auto_forward(self, message: str):
        """
        Generate a packet using write_to_canvas and change the command to "auto_forward"
        to allow chaining across canvases.

        Allows chaining write operations from the first canvas to the last
        in the child-host chain.
        Example use
        
        PACKET_CREATOR.auto_forward("Hello World!")
        """
        
        packet = self.write_to_canvas(message)
        if packet:
            packet["command"]["cmd"] = "auto_forward"
        return packet


    def forward_to(self, target_id: str, message: str):
        """
        Generate a packet that writes through the canvas chain 
        and stops at the specified target_id.
        Example use
        
        PACKET_CREATOR.forward_to("canvas_1", "Hello_world")
        """
        packet = self.write_to_canvas(message)
        if packet:
            packet["command"]["cmd"] = "forward_to"
            packet["command"]["args"] = {"canvas_id": target_id}
        return packet
