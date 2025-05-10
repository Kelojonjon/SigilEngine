
import time

class TIMER():
    
    """
    A lightweight timer utility for scheduling multiple named events
    that share a common action. No threading involved — must be updated
    manually in a loop using `.update_timer()`.

    Currently doesn't take arguments for the action, they need to be handled elsewhere

    Example:
        timer = TIMER()
        timer.event(action=some_func, ping=1, pong=5)

        while True:
            timer.update_timer()
            time.sleep(0.01)
    """
    
    def __init__(self):

        # All the events added are stored here
        self.timer_events = {}
    
        
    def event(self, action=None, **kwargs):
        """
        Add events that execute the same action when triggered.
        Keyword args define event names and their intervals in seconds.
        Action must be a callable.

        Example:
            timer.event(action=handler, fast=1, slow=5)

        Example of a timer_events folder, when something is added
        timer.events = {
            "action": self.scheduled_event,
            
            "added_event_1":{"
                    "interval": 1,
                    "last_trigger": 0 # Works with no interaction
                "}
        }
        """
        # Store the shared action (if any)
        self.timer_events["action"] = action if callable(action) else None
                
                
        for event, interval in kwargs.items():
            if isinstance(event, str) and isinstance(interval, int):
                self.timer_events[event] = {
                    "interval": interval,
                    "last_trigger": 0
                }
            else:
                continue
            
            

    def update_timer(self):
        """
        Check intervals for all events and executes them as needed
        Doesnt thread, so the timer has to be updated in a running loop
        """
        action = self.timer_events.get("action", None)
        current_time = time.time()

        if action is None:
            return  # Nothing to do

        for event_name, rules in self.timer_events.items():
            if event_name == "action":
                continue

            event_interval = rules.get("interval")
            last_trigger = rules.get("last_trigger")

            if abs(current_time - last_trigger) >= event_interval:
                self.timer_events[event_name]["last_trigger"] = current_time
                action()


    def reset(self):
        """
        Clear all timer events and actions
        """
        self.timer_events = {}
