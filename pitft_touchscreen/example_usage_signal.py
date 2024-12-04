# !/usr/bin/python
#  -*- coding: utf-8 -*-

import signal
from pitft_touchscreen import pitft_touchscreen
from time import sleep


class example_usage_signal():

    # Init touchscreen
    ts = pitft_touchscreen()
    running = True

    @classmethod
    def shutdown(cls, signum, frame):
        print("Shutdown detected.  Exiting")
        # Set flag to stop processing events
        cls.running = False

    @classmethod
    def start(cls):
        # Set signals to be handled by shutdown method.
        signal.signal(signal.SIG_IGN, cls.shutdown)
        signal.signal(signal.SIGTERM, cls.shutdown)
        cls.ts.start()
        print("Touchscreen events will be collected until CTL-C is pressed.")
        try:
            while cls.running:
                # Handle waiting events
                if not cls.ts.queue_empty():
                    for e in cls.ts.get_event():
                        print("Event received: {}".format(e))
                sleep(0.01)
        except KeyboardInterrupt:
            # Keeps error from displaying when CTL-C is pressed
            print(""),
        finally:
            # Since we are about to exit, cancel SIG_IGN handler
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            # In real program you need to call stop to stop collecting events
            cls.ts.stop()


example_usage_signal.start()
