# processors.py
import queue
from collections import deque

import numpy as np

from core.base import BaseProcessor, BaseSource
from core.sources import QueueSource, DequeSource
from core.telemetry import Queue, Deque, MonitorBuffers


class FFTProcessor(BaseProcessor):
    def process(self, chunk: np.ndarray) -> np.ndarray:
        # We use rfft because audio signals are real-valued.
        # It returns only the positive frequencies, which is what we need.
        fft_data = np.abs(np.fft.rfft(chunk))

        # Normalize (optional, depends on your visualization needs)
        fft_data = fft_data / len(chunk)
        return fft_data

# change voice tone
class PitchProcessor(BaseProcessor):
    def __init__(self, source: BaseSource, shift: float):
        """
        Params:
        shift: 1 - normal
              >1 - bass / deep voice
              <1 - squeaky
        """
        super().__init__(source)
        self.shift = shift

    def process(self, chunk: np.ndarray) -> np.ndarray:
        if self.shift == 1.0:
            return chunk

        old_indices = np.arange(len(chunk))
        new_indices = old_indices * self.shift
        new_chunk = np.interp(new_indices, old_indices, chunk, right=0.0)

        return new_chunk


class Splitter(BaseProcessor):
    def __init__(self, source: BaseSource, monitor: MonitorBuffers = None):
        super().__init__(source)
        # Strict consumers must have separate queue
        self._queues: list[Queue[np.ndarray]] = []
        self._deque: Deque[np.ndarray] = Deque(1, "")
        self._monitor = monitor

    def branch_strict(self, maxsize = 20, queue_name: str = None) -> QueueSource:
        q = Queue(maxsize, queue_name)
        self._queues.append(q)

        if self._monitor is not None:
            self._monitor.add_buffer(q)

        return QueueSource(q, self.source.samplerate, self.source.chunk_size)

    def branch_lossy(self, queue_name: str = None) -> DequeSource:
        if self._deque.name == "":
            self._deque.name = queue_name
            if self._monitor is not None:
                self._monitor.add_buffer(self._deque)

        return DequeSource(self._deque, self.source.samplerate, self.source.chunk_size)

    def process(self, chunk: np.ndarray) -> np.ndarray:
        try:
            # update strict queues
            for q in self._queues:
                q.put_nowait(chunk.copy())
        except queue.Full:
            pass

        # update lazy queue
        self._deque.append(chunk.copy())

        return chunk