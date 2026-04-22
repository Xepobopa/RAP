# processors.py
import queue
from collections import deque

import numpy as np

from core.base import BaseProcessor, BaseSource
from core.sources import QueueSource, DequeSource


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
    def __init__(self, source: BaseSource):
        super().__init__(source)
        self._queues: list[deque[np.ndarray]] = []

    def branch_strict(self, maxsize = 10) -> QueueSource:
        q = queue.Queue(maxsize=maxsize)
        self._queues.append(q)
        return QueueSource(q, self.source.samplerate, self.source.chunk_size)

    # def branch_lazy(self) -> DequeSource:
    #     # q = queue.Queue(maxsize=1)
    #     # Use Deque
    #     q = deque(maxlen=1)
    #     self._queues.append(q)
    #     return DequeSource(q, self.source.samplerate, self.source.chunk_size)

    def process(self, chunk: np.ndarray) -> np.ndarray:
        try:
            for q in self._queues:
                q.append(chunk.copy())
        except queue.Full:
            pass

        return chunk