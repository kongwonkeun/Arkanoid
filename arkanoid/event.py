#
#
#

from collections import defaultdict
import pygame

class EventReceiver:

    def __init__(self):
        self._handlers = defaultdict(list)

    def receive(self):
        event_list = pygame.event.get()
        for event in event_list:
            try:
                handlers = self._handlers[event.type]
            except KeyError:
                pass
            else:
                for handler in handlers:
                    handler(event)

    def register_handler(self, event_type, *handlers):
        assert len(handlers) > 0
        self._handlers[event_type] += handlers

    def unregister_handler(self, *handlers):
        assert len(handlers) > 0
        for event_type, evt_handlers in self._handlers.items():
            for h in list(evt_handlers):
                if  h in handlers:
                    evt_handlers.remove(h)

receiver = EventReceiver()

#
#
#
