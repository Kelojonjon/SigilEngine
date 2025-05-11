
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
        Keyword args define event names and their intervals in seconds.

        Example of a timer_events folder, when something is added
        timer.events = {
            "added_event_1":{
                    "interval": 1,
                    "last_trigger": 0, # Works with no interaction
                    "action": None
                }
        }
        """

        for event, interval in kwargs.items():
            if isinstance(event, str) and isinstance(interval, int):
                self.timer_events[event] = {
                    "interval": interval,
                    "last_trigger": 0,
                    "action": None
                }
            else:
                continue
    
    def action(self, **kwargs):
        """
        Add actions to different timer events, actions must be callable functions.
        Doesnt allow passing arguments directly from the timer.
        For example state variables can be used as action arguments
        """
        if len(self.timer_events) > 0:
            for event_name, action in kwargs.items():
                if event_name in self.timer_events and callable(action):
                    self.timer_events[event_name]["action"] = action
            

    def update_timer(self):
        """
        Check intervals for all events and executes them as needed
        Doesnt thread, so the timer has to be updated in a running loop
        """
        current_time = time.time()

        for event_name, rules in self.timer_events.items():

            event_interval = rules.get("interval")
            last_trigger = rules.get("last_trigger")
            action = rules.get("action", None)

            if current_time - last_trigger >= event_interval and action != None:
                self.timer_events[event_name]["last_trigger"] += event_interval
                action()


    def reset(self):
        """
        Clear all timer events and actions
        """
        self.timer_events = {}
