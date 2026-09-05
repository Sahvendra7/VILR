import time
from typing import Dict

class PerformanceTracker:
    def __init__(self):
        self.timings: Dict[str, float] = {}
        self._starts: Dict[str, float] = {}
        self.overall_start = time.perf_counter()

    def start(self, metric: str):
        self._starts[metric] = time.perf_counter()

    def stop(self, metric: str):
        if metric in self._starts:
            self.timings[metric] = time.perf_counter() - self._starts[metric]

    def stop_all(self):
        self.timings["deterministic_authorization"] = time.perf_counter() - self.overall_start
