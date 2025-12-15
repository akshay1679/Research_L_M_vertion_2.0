import time
import threading
import random
import statistics
from common.of_db import of_db

class NetworkMonitor:
    """
    Measures delay and jitter and updates OF-DB.
    """

    def __init__(self, simulation_mode=True):
        self.simulation_mode = simulation_mode
        self.running = False
        self.history = {}

    def start_monitoring(self):
        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while self.running:
            for key, link in of_db.links.items():
                delay = self._measure_delay(link)

                if key not in self.history:
                    self.history[key] = []
                self.history[key].append(delay)

                if len(self.history[key]) > 10:
                    self.history[key].pop(0)

                link.propagation_delay = delay
                link.jitter = (
                    statistics.stdev(self.history[key])
                    if len(self.history[key]) > 1 else 0.0
                )

            time.sleep(5)

    def _measure_delay(self, link):
        if self.simulation_mode:
            base = 5.0
            noise = random.uniform(-0.5, 0.5)
            load = (link.bw_used / link.bw_capacity) * 2 if link.bw_capacity else 0
            return base + noise + load
        return 0.1
