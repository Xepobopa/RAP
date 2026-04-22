import queue
import threading
import time
from abc import ABC, abstractmethod
from collections import deque


class Buffer(ABC):
    def __init__(self, maxsize: int, name: str | None):
        self.maxsize = maxsize
        self.name = name

        self.total_in = 0
        self.total_out = 0
        self.dropped = 0

    @abstractmethod
    def qsize(self) -> int:
        pass

    def clear_telemetry(self):
        self.dropped = 0
        self.total_in = 0
        self.total_out = 0


class Queue[T](Buffer):
    """Custom queue.Queue wrapper"""

    def __init__(self, maxsize: int = 10, name: str = None):
        super().__init__(maxsize, name)
        self._q = queue.Queue(maxsize)

    def get_nowait(self) -> T:
        e = self._q.get_nowait()
        self.total_out += 1  # increment counter only after 'get_nowait', so throw exception first
        return e

    def put_nowait(self, e: T):
        try:
            self._q.put_nowait(e)
            self.total_in += 1
        except queue.Full:
            self.dropped += 1
            raise queue.Full

    def empty(self):
        return self._q.empty()

    def qsize(self):
        return self._q.qsize()


class Deque[T](Buffer):
    """Custom queue.Queue wrapper"""

    def __init__(self, maxsize: int = 10, name: str = None):
        super().__init__(maxsize, name)
        self._dq = deque(maxlen=maxsize)

    def get_latest(self) -> T:
        if not self._dq:
            raise queue.Empty

        item = self._dq[-1]
        self.total_out += 1
        return item

    def append(self, e: T):
        if self.qsize() == 1:
            self.dropped += 1

        self._dq.append(e)
        self.total_in += 1

    def qsize(self):
        return len(self._dq)


class MonitorBuffers:
    def __init__(self):
        self._q: list[Buffer] = []
        self._running = False

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def _open(self):
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()
        pass

    def _close(self):
        self._running = False
        pass

    def add_buffer(self, b: Buffer):
        self._q.append(b)

    def _loop(self):
        while self._running:
            time.sleep(1.0)

            print(f"\n--- 📊 Pipeline Telemetry [{time.strftime('%H:%M:%S')}] ---")
            for idx, q in enumerate(self._q):
                name = f"Queue #{idx}" if (q.name is None) else q.name
                load_pct = int((q.qsize() / q.maxsize) * 100) if q.maxsize else 0

                print(
                    f"\n[{name:<15}] IN: {q.total_in:^4}/sec | OUT: {q.total_out:^4}/sec | Buffer: {q.qsize():>2}/{q.maxsize} ({load_pct:>3}%) | Dropped: {q.dropped}"
                )

                q.clear_telemetry()
