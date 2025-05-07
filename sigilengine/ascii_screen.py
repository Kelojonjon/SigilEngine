import os


class ASCII_SCREEN:

    """
    Static reusable methods, that are used around in  different modules
    """    
    
    @staticmethod
    def clear_screen():
        """
        Clear the terminal screen
        """
        os.system('cls' if os.name == 'nt' else 'clear')


    @staticmethod
    def create_canvas(canvas_id: str, owner: str, height: int, width: int, fillvalue: str, visible: bool):
        """
        Create a new canvas buffer 'grid' as a nested dictionary.
        Coordinates start from (y,x) == (1,1) == top left corner 

        Dimensions used to create the canvas
        - 'height': Y rows of the canvas
        - 'width': X columns of the canvas 

        Each cell of the canvas is initialized with:
        - 'char': The 'char' used as the fillvalue.  
        - 'canvas_id': the name of the canvas
        - 'owner': optional owner label, usefull for identifying the processes by their owner 'process'.
        - 'visible': visibility flag (default: True)

        Returns:
            dict[y][x] → cell metadata dictionary
        """
        canvas = {}
        for y in range(1, height + 1):
            canvas[y] = {}
            for x in range(1, width + 1):
                canvas[y][x] = {
                    'char': fillvalue,
                    'owner': owner,
                    'visible': visible,
                    'canvas_id': canvas_id
                }
        return canvas 
    
   
    @staticmethod
    def create_ref_canvas(height: int, width: int):
        """
        Create a minimal canvas buffer used for host reference binding.
        Combine with box_borders, to debug canvas location on its host.
        
        Uses hardcoded values:
        - fillvalue: '·'
        - owner: 'ref'
        - visible: True

        Returns:
            dict[y][x] → cell metadata dictionary
        """
        canvas = {}
        for y in range(1, height + 1):
            canvas[y] = {}
            for x in range(1, width + 1):
                canvas[y][x] = {
                    'char': '·',
                    'owner': 'ref',
                    'visible': True,
                    'canvas_id': 'ref'
                }
        return canvas
    
   
    @staticmethod
    def render(buffer: dict, ignore=None):
        """
        Convert a canvas buffer into a visual string for terminal output.

        Args:
            buffer (dict): The canvas buffer (dict of dicts with metadata per (y, x) coordinate).
            ignore (str): Character to treat as transparent (replaced with space). Default is 'None'.

        Returns:
            str: Rendered canvas as a multi-line string.
        """
        result = ''
        for y in buffer:
            row = []
            for x in buffer[y]:
                cell = buffer[y][x]
                char = cell.get('char', ' ')
                row.append(' ' if char == ignore else char)
            result += ''.join(row) + '\n'
        return result

    @staticmethod
    def write_cell(buffer: dict, y: int, x: int, metadata: dict):
        """
        Update the metadata of a single cell in the buffer at position (y, x).

        Args:
            buffer (dict): The canvas buffer (dict of dicts).
            y (int): Row index of the cell.
            x (int): Column index of the cell.
            metadata (dict): Dictionary of metadata to merge into the cell.

        Returns:
            bool: True if the cell existed and was updated, False otherwise.
        """
        try:
            buffer[y][x].update(metadata)
            return True 
        except KeyError:
            return False 
        

    @staticmethod
    def zip_and_write(buffer: dict, chart: list, metadata_list: list):
        """
        Zip coordinates and metadata, then write directly to the canvas buffer.

        Args:
            buffer (dict): The canvas buffer to write into.
            chart (list of (y, x)): Coordinates to write to.
            metadata_list (list of dict): Metadata to write at each coord.

        Returns:
            int: Number of cells successfully written.
        """
 
        count = 0
        for (y, x), data in zip(chart, metadata_list):
            if ASCII_SCREEN.write_cell(buffer, y, x, data):
                count += 1

        return count


    @staticmethod
    def box_borders(buffer: dict, yx_corner: tuple, height: int, width: int, char="#"):
        """
        Draw a border around a rectangular region on the buffer using the given character.

        This is especially useful for visualizing the placement of a canvas or module
        on its host canvas during development or debugging.

        Args:
            buffer (dict): The canvas buffer to modify.
            yx_corner (tuple): Top-left corner (y, x) of the box.
            height (int): Height of the box.
            width (int): Width of the box.
            char (str): Character to use for the border. Default is '#'.

        Returns:
            None. The buffer is modified in place.
        """
        # Top and bottom edges
        y, x = yx_corner
        for col in range(x, x + width):
            ASCII_SCREEN.write_cell(buffer, y, col, {'char': char}) # Top 
            ASCII_SCREEN.write_cell(buffer, y + height - 1, col, {'char': char}) # Bottom 

        # Left and right edges
        for row in range(y + 1, y + height - 1):
            ASCII_SCREEN.write_cell(buffer, row, x, {'char': char}) # Left side
            ASCII_SCREEN.write_cell(buffer, row, x + width - 1, {'char': char}) # Right side
    

    @staticmethod
    def generate_wrapped_chart(origin_yx, string, width):
        """
        Generate coordinates for text placement, wrapping when reaching the given width.
        Also wraps around with newline.
        To disable automatic wrapping, set the width larger than the expected line length.
        """
        y, x = origin_yx
        original_x = x
        chart = []
        
        for char in string:
            
            if char == "\n":
                y += 1
                x = original_x
                continue
            
            chart.append((y, x))
            x += 1
            if (x - original_x) >= width: 
                x = original_x
                y += 1

        return chart

    @staticmethod
    def generate_coords(yx_corner: tuple, height: int, width: int):
        """
        Generate a list of (y, x) coordinates for a rectangular area.

        Args:
            yx_corner (tuple): Top-left starting point of the area (y, x).
            height (int): Number of rows in the area.
            width (int): Number of columns in the area.

        Returns:
            list: List of (y, x) tuples covering the area in row-major order.
        """
        y0, x0 = yx_corner
        return [
            (y, x)
            for y in range(y0, y0 + height)
            for x in range(x0, x0 + width)
        ]