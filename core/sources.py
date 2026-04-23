import queue

import numpy as np
import sounddevice as sd
import soundfile as sf

from core.base import BaseSource
from core.telemetry import Queue, Deque, MonitorBuffers


class DeviceSource(BaseSource):
    def close(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    device_id: int | None
    channels: int | None
    chunk_size: int
    samplerate: int
    _queue: Queue
    _stream: sd.InputStream | None

    # """Change latency to """
    def __init__(self, latency: str = 'low', chunk_size: int = 1024, samplerate: int = 44100, monitor: MonitorBuffers = None):
        self.channels = 1
        self.device_id = None # default in system
        self._queue = Queue(30, "DeviceSourceBuff")
        self._stream = None
        self.latency = latency
        super().__init__(samplerate, chunk_size)

        if monitor is not None:
            monitor.add_buffer(self._queue)

    def _callback(self, indata: np.ndarray, frames, time, status):
        if status:
            print(f"Error: {status}")
        try:
            self._queue.put_nowait(indata.copy())
        except queue.Full:
            pass

    def open(self):
        if self._stream is None:  # Создаем только если еще не создан
            self._stream = sd.InputStream(
                device=self.device_id,
                channels=self.channels,
                samplerate=self.samplerate,
                blocksize=self.chunk_size,
                callback=self._callback,
                latency=self.latency
            )
            self._stream.start()

    def read_chunk(self) -> np.ndarray | None:
        try:
            # Пытаемся взять данные. Timeout можно уменьшить для отзывчивости.
            chunk = self._queue.get_nowait()
            return chunk.flatten()
        except queue.Empty:
            # Если данных нет, возвращаем "тишину" вместо None.
            # Это не даст итератору выбросить StopIteration раньше времени.
            return np.zeros(self.chunk_size, dtype=np.float32)


class FileSource(BaseSource):
    """Only WAV files are supported. Does not need Monitor, because it words due to generators"""
    def __init__(self, filepath: str, chunk_size: int = 1024):
        # maybe move 'samplerate' to the 'BaseSource'?
        self.filepath = filepath
        self._file: sf.SoundFile | None = None
        self._iter = None

        info = sf.info(self.filepath)
        self.samplerate = info.samplerate
        self.chunk_size = chunk_size
        super().__init__(self.samplerate, self.chunk_size)

    def open(self):
        self._file = sf.SoundFile(self.filepath)
        if self._file is not None:
            self._iter = self._file.blocks(blocksize=self.chunk_size, dtype='float32', always_2d=False, fill_value=0)

    def read_chunk(self):
        try:
            chunk: np.ndarray = next(self._iter)
            if chunk is None:
                return np.zeros(self.chunk_size, dtype=np.float32)

            # multi channel to one channel
            if len(chunk.shape) > 1:
                chunk = chunk[:, 0]

            return chunk
        except StopIteration:
            return None


    def close(self):
        if self._file is not None:
            if not self._file.closed:
                self._file.close()
                self._file = None


class QueueSource(BaseSource):
    """Strict Source. Use it, when the consumer needs all the data and its loss / changes are unacceptable. For example: AudioSink. Cons: Latency, but sometimes not"""
    def __init__(self, q: Queue[np.ndarray], samplerate: int, chunk_size: int):
        super().__init__(samplerate, chunk_size)
        self.q = q
        self._empty_chunk = np.zeros(chunk_size, dtype=np.float32)


    def open(self): pass
    def close(self): pass

    # get the latest
    def read_chunk(self):
        if self.q.empty():
            return self._empty_chunk

        return self.q.get_nowait()

# without monitor ??
class DequeSource(BaseSource):
    """Lossy Source. Use it, when the consumer needs the newest data and some loss / changes are acceptable. For example: PlotSink"""
    def __init__(self, q: Deque[np.ndarray], samplerate: int, chunk_size: int):
        super().__init__(samplerate, chunk_size)
        self.q = q
        self._empty_chunk = np.zeros(chunk_size, dtype=np.float32)

    def open(self): pass
    def close(self): pass

    def read_chunk(self):
        try:
            # read the value, but do not delete it. This prevents from returning empty chunks, that will ruin the plot
            return self.q.get_latest()
        except queue.Empty:
            return self._empty_chunk
