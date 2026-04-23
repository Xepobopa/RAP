# This library has a Pipeline architecture.
# Chain looks like this: Source -> Processor -> Processor -> ... -> Sink

from abc import abstractmethod, ABC
from enum import Enum

import numpy as np


class BaseSource(ABC):
    def __init__(self, samplerate: int = 44100, chunk_size: int = 1024):
        self.samplerate = samplerate
        self.chunk_size = chunk_size
        pass

    # --- The Context Manager Protocol ---
    def __enter__(self):
        """Executed when entering 'with source:'"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Executed when leaving 'with source:', even if an error occurred!"""
        self.close()

    # --- The Iterator Protocol ---

    def __iter__(self):
        return self

    def __next__(self):
        chunk = self.read_chunk()
        if chunk is None:
            raise StopIteration
        return chunk

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def read_chunk(self):
        pass

    @abstractmethod
    def close(self):
        pass


class BaseSink(ABC):
    def __init__(self, source: BaseSource):
        self.source = source

    @abstractmethod
    def write(self, chunk: np.ndarray):
        """Action to perform on the data (plot, save, etc.)"""
        pass

    def run(self):
        """A simple loop to pull data through the whole pipeline."""
        with self.source:
            for chunk in self.source:
                if chunk is None:
                    break
                self.write(chunk)



# Processor change some input data, but acts like a source by itself
class BaseProcessor(BaseSource):
    """
    Acts as a wrapper around a source.
    It 'pulls' data from the source, processes it, and provides it to the next step.
    """

    def __init__(self, source: BaseSource):
        super().__init__(samplerate=source.samplerate, chunk_size=source.chunk_size)
        self.source = source

    def open(self):
        self.source.open()

    def read_chunk(self) -> np.ndarray | None:
        chunk = self.source.read_chunk()
        if chunk is None:
            return None
        return self.process(chunk)

    @abstractmethod
    def process(self, chunk: np.ndarray) -> np.ndarray:
        pass

    def close(self):
        pass

class Notes(Enum):
    C4 = 261.63
    CS4 = 277.18  # C# / Db
    D4 = 293.66
    DS4 = 311.13  # D# / Eb
    E4 = 329.63
    F4 = 349.23
    FS4 = 369.99  # F# / Gb
    G4 = 392.00
    GS4 = 415.30  # G# / Ab
    A4 = 440.00
    AS4 = 466.16  # A# / Bb
    B4 = 493.88

    Db4 = CS4
    Eb4 = DS4
    Gb4 = FS4
    Ab4 = GS4
    Bb4 = AS4