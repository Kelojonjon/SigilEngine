import time
import threading
import random


"""
Below are all the modules provided in the project:
1. **SPACE** is a library where all canvas threads keep their registries.  
   Canvases register their queues and buffers here for easy interaction.

2. **ASCII_SCREEN** is a class of reusable, stateless static methods used across the modules.

3. **CANVA_THREAD** is a writable buffer that can perform various tasks on its buffer.  
   Most of the ASCII_SCREEN tools are designed to modify the state of this class.

4. **PACKET_CREATOR** is a simple API that allows interaction with canvases through simple commands.  
   Requests are validated and returned as ready-to-send packets for the CANVA_THREAD parser.
"""
from space import SPACE
from space import SPACE_LOCK
from ascii_screen import ASCII_SCREEN
from canva_thread import CANVA_THREAD
from packet_creator import PACKET_CREATOR


class EXAMPLES():

    """
    Basic tests that serve as simple examples of usage.    
    If the tests show weird behavior, try changing the `host_id`s and canvas dimensions below. 
    Also keep in mind the order of operations, the packet_creator class has a state that it uses for certain commands. 
    """
    
    def __init__(self):
        
        """
        Initialize and start multiple CANVA_THREAD instances.

        This sets up five canvas threads:
        - `canvas1`: Main canvas.
        - `canvas2`, `canvas3`, `canvas4`, `canvas5`: Child canvases hosted on `canvas1`, each with specific origin positions.

        Each CANVA_THREAD is wrapped in a threading.Thread targeting its `run()` method, and all threads are started immediately.
        For details about CANVA_THREAD arguments, check the `canva_thread` module.
        """    
        
        print("🚀 Starting CANVA_THREADS...\n")
        
        # Create thread objects
        self.t1 = CANVA_THREAD("canvas1", "main", 15, 70)
        self.t2 = CANVA_THREAD("canvas2", "main", 3, 9, host="canvas1", origin_yx=(1, 1))
        self.t3 = CANVA_THREAD("canvas3", "main", 4, 10, host="canvas1", origin_yx=(1, 1))
        self.t4 = CANVA_THREAD("canvas4", "main", 7, 50, host="canvas1", origin_yx=(1, 1))
        self.t5 = CANVA_THREAD("canvas5", "main", 3, 20, host="canvas4", origin_yx=(1, 1))
        
        # Wrap in real threading.Thread runners, target the CANVA_THREAD run function
        self.thread1 = threading.Thread(target=self.t1.run)
        self.thread2 = threading.Thread(target=self.t2.run)
        self.thread3 = threading.Thread(target=self.t3.run)
        self.thread4 = threading.Thread(target=self.t4.run)
        self.thread5 = threading.Thread(target=self.t5.run)

        # Start the threads
        self.thread1.start()
        self.thread2.start()
        self.thread3.start()
        self.thread4.start()
        self.thread5.start()
        
        # Packet creator, init with the desired content width
        # For manual \n wrapping be sure to set it wide enough for your canvas
        self.packet_boi = PACKET_CREATOR(8)
        
        print("All up and running!")
        time.sleep(1)
    


    def test_loop(self):
        """
        Test random teleportation of canvases on the host canvas.

        This test creates messages for each canvas and continuously:
        - Clears the main canvas.
        - Randomly repositions canvases.
        - Forwards auto-generated messages through the chain.
        - Displays the host canvas and a child reference canvas.

        Play around with host IDs and canvas sizes if behavior looks odd.
        Also try setting different target widths for the `packet_creator` object to test different wrapping behaviors.
        """
        
        # Create a template where additional metadata will be injected
        template = {}
        self.packet_boi.set_template(template)
        
        # Create message commands for each canvas (auto-forward until no host canvas is found)
        # \n Newlines are also supported for manual wrapping
        message2 = self.packet_boi.auto_forward("CANVAS2\nWRAPPING")
        message3 = self.packet_boi.auto_forward("CANVAS3 ALSO IS WRAPPING")
        self.packet_boi.set_target_width(50)
        message4 = self.packet_boi.auto_forward(":D:D:D:D:D:D:D THIS IS A LONG TEXT")
        
        # Create a clear command
        clear_cmd = self.packet_boi.clear_canvas()
        
        canvases = [self.t2, self.t3, self.t4]
        messages = [message2, message3, message4]
        
        try:
            while True:
                # Clear the main canvas by generating a new one
                self.t1.queue.put(clear_cmd)
                time.sleep(0.1)
                
                # Update each canvas with a new random position and message
                for i, canvas in enumerate(canvases):
                    y = random.randint(1, 10)
                    x = random.randint(1, 60)
                    # Create a command to move canvases on their host canvas
                    move_cmd = self.packet_boi.set_origin_on_host((y, x))
                    
                    # Send move and message commands
                    canvas.queue.put(move_cmd)
                    canvas.queue.put(messages[i])
                
                # Display the result
                ASCII_SCREEN.clear_screen()
                # Render canvas1 and replace "·" with " "
                print(ASCII_SCREEN.render(self.t1.canvas, "·"))
                # Render canvas2's host reference canvas to see its placement on canvas1
                print(ASCII_SCREEN.render(self.t2.host_ref_canvas))
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nTest loop stopped by user.")


    def chaining_test(self):
        """
        Test chaining behavior between canvases.

        Play around with the host IDs in the __init__ and try running this test.
        It demonstrates how canvases can be moved and forwarded through the chain.

        Steps:
        - Clear all canvases.
        - Set a new content origin.
        - Forward a message through the canvas chain.
        - Move canvases on their host canvases.
        - Render the chain progression.
        """
        
        print("\n🔗 Starting chaining test...")
        time.sleep(1)

        # Set up a template to work on
        template = {}
        self.packet_boi.set_template(template)

        # Clear all canvases first
        clear_cmd = self.packet_boi.clear_canvas()
        for canvas in [self.t1, self.t2, self.t3, self.t4, self.t5]:
            canvas.queue.put(clear_cmd)

        time.sleep(0.1)  # Give them a moment to clear

        # Move the content origin on the target canvas
        self.packet_boi.set_content_origin((1, 4))
        
        # Set a new target_width for the packet_creator to show the message correctly
        # You can also set the target width to None and handle the wrapping using \n newline
        self.packet_boi.set_target_width(20)

        # Create a message to be forwarded to canvas1 (you can also use the 'auto_forward' command)
        start_message = self.packet_boi.forward_to("canvas1", "[CHAIN\nSTARTED\nHERE]")
        
        # Create commands to move the canvases on their host canvases
        move_window = self.packet_boi.set_origin_on_host((2, 7))
        move_again = self.packet_boi.set_origin_on_host((6, 17))
        
        # Send move commands to canvases
        self.t5.queue.put(move_window)    
        self.t4.queue.put(move_again)   
        
        time.sleep(0.1)
        
        # Send the starting message through the chain
        self.t5.queue.put(start_message)

        # Render results
        ASCII_SCREEN.clear_screen()
        print("🎨 canvas1 (top of chain):")
        print(ASCII_SCREEN.render(self.t1.canvas))

        print("\n🎨 canvas4 (middle of chain):")
        print(ASCII_SCREEN.render(self.t4.host_ref_canvas))
        print(ASCII_SCREEN.render(self.t4.canvas))

        print("\n🎨 canvas5 (deep child):")
        print("´host_reference_canvas´ showing canvas5 position on canvas4")
        print(ASCII_SCREEN.render(self.t5.host_ref_canvas))
        print(ASCII_SCREEN.render(self.t5.canvas))

        print("\n✅ Chaining test completed.\n")

        
    def kill_test(self):
        """
        Test the kill behavior of canvases.

        Steps:
        - Print the current SPACE registry.
        - Send a `!kill` command to selected canvases.
        - Wait to allow canvases time to delete themselves.
        - Print the updated SPACE registry to verify removal.
        """
        with SPACE_LOCK:
            if not SPACE:
                print("No registered canvases found in SPACE")
                return
        
            # Are the canvases registered
            print("\nRegistered canvases: \n")
            for id in list(SPACE.keys()):
                print(SPACE.get(id))
            
        kill = self.packet_boi.kill_canvas()
        canvases = [self.t2, self.t3, self.t4]
        # Send !kill command
        for canvas in canvases:
            time.sleep(0.5)
            canvas.queue.put(kill)
        
        # Sleep so the canvases have time to delete themselves
        time.sleep(1)
        # Did the canvases delete themselves? 
        print("\nRegistered canvases: \n")
        with SPACE_LOCK:
            for id in list(SPACE.keys()):
                print(SPACE.get(id))
        
    
    def resize_and_fillvalue_test(self):
        """
        Randomly change the fill value and resize the canvas.

        Continuously:
        - Set a random fill value for the main canvas.
        - Resize the main canvas to random dimensions.
        - Refresh the host reference on canvas2 to follow changes.
        - Render both canvas1 and canvas2's host reference canvas.

        Order of operations matters for synchronization.
        """
        
        fillvalues = ["@", "#", "·", "$"]
        try:
            while True:
                # Random dimensions
                y = random.randint(1, 15)
                x = random.randint(1, 70)

                random_fillvalue = random.choice(fillvalues)
                
                # Create commands
                new_fillvalue = self.packet_boi.set_fillvalue(random_fillvalue)
                resize = self.packet_boi.resize_canvas(y, x)
                refresh_host = self.packet_boi.set_host("canvas1")  # Refresh child canvas with host changes

                # Send commands (order matters!)
                self.t1.queue.put(new_fillvalue)
                self.t1.queue.put(resize)

                # Tiny nap so the canvases have time to sync correctly
                time.sleep(0.01)
                self.t2.queue.put(refresh_host)

                # Render the results
                time.sleep(1)
                ASCII_SCREEN.clear_screen()
                print(ASCII_SCREEN.render(self.t1.canvas))
                print(ASCII_SCREEN.render(self.t2.host_ref_canvas))

        except KeyboardInterrupt:
            print("\nTest loop stopped by user.")


    def random_packet_generation(self):
        """
        Generate a random packet to send to a canvas.

        Randomly chooses one of the following packet types:
        - Resize the canvas
        - Set a new fill value
        - Move the content origin
        - Write random text to the canvas

        Returns:
            A ready-to-send packet command.
        """
        
        # List of possible packet types
        packets = [
            self.packet_boi.resize_canvas,   # Resize command
            self.packet_boi.set_fillvalue,   # Fill value command
            self.packet_boi.set_content_origin,  # Origin movement
            self.packet_boi.write_to_canvas  # Writing text
        ]
        
        # Randomly choose a packet type
        packet_type = random.choice(packets)
        
        # Randomly generate packet data
        if packet_type == self.packet_boi.resize_canvas:
            return packet_type(random.randint(10, 100), random.randint(10, 100))
        elif packet_type == self.packet_boi.set_fillvalue:
            return packet_type(random.choice(["@", "#", "·", "$"]))
        elif packet_type == self.packet_boi.set_content_origin:
            return packet_type((random.randint(1, 10), random.randint(1, 60)))
        elif packet_type == self.packet_boi.write_to_canvas:
            return packet_type("Random Text " + str(random.randint(100, 999)))


    def run_random_test(self):
        """
        Continuously send random packets to canvases and monitor their behavior.

        This test:
        - Randomly targets canvases with different packet commands.
        - Monitors thread status and queue sizes.
        - Displays canvas space sizes for host reference canvases.
        
        Play around with the sleep timer for more intensive or relaxed testing.
        """
        
        canvases = [self.t1, self.t2, self.t3, self.t4, self.t5]  # Include all canvases hosted on canvas1
        try:
            while True:
                random_canvas = random.choice(canvases)  # Choose a random canvas
                
                # Generate a random packet
                packet = self.random_packet_generation()
                
                # Send the packet to the chosen canvas
                random_canvas.queue.put(packet)
                
                # Clear the screen
                ASCII_SCREEN.clear_screen()
                
                # Monitor threads
                print("Thread Status:")
                print(f"Thread 1 Alive: {self.thread1.is_alive()}  |  Queue Size: {self.t1.queue.qsize()}")
                print(f"Thread 2 Alive: {self.thread2.is_alive()}  |  Queue Size: {self.t2.queue.qsize()}")
                print(f"Thread 3 Alive: {self.thread3.is_alive()}  |  Queue Size: {self.t3.queue.qsize()}")
                print(f"Thread 4 Alive: {self.thread4.is_alive()}  |  Queue Size: {self.t4.queue.qsize()}")
                print(f"Thread 5 Alive: {self.thread5.is_alive()}  |  Queue Size: {self.t5.queue.qsize()}")

                # Monitor canvas space (size and content)
                print("\nCanvas Space Data:")
                print(f"Canvas 1 Size: {len(self.t1.canvas)}")
                print(f"Canvas 2 Size: {len(self.t2.host_ref_canvas)}")
                print(f"Canvas 3 Size: {len(self.t3.host_ref_canvas)}")
                print(f"Canvas 4 Size: {len(self.t4.host_ref_canvas)}")
                print(f"Canvas 5 Size: {len(self.t5.host_ref_canvas)}")

                #print(ASCII_SCREEN.render(self.t1.canvas))
                time.sleep(0.05)
                    
        except KeyboardInterrupt:
            print("\nTest loop stopped by user.")


                
    
    
    def shutdown(self):
        """
        Shut down all canvas threads cleanly.

        This:
        - Sets each canvas thread's `alive` flag to False.
        - Joins all threads to ensure proper exit.
        - Prints a confirmation message once shutdown is complete.
        """
        # Clean shutdown via alive flag
        self.t1.alive = False
        self.t2.alive = False
        self.t3.alive = False
        self.t4.alive = False
        self.t5.alive = False
 
        # Wait for the threads to exit
        self.threads = [self.thread1, self.thread2, self.thread3, self.thread4, self.thread5]
        for thread in self.threads:
            if thread != None:
                thread.join()
        
        print("✅ All threads have shut down cleanly.")
        


try:
    test = EXAMPLES()
    test.resize_and_fillvalue_test()
finally:
    test.shutdown()
