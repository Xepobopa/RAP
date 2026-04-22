# sink - output
import queue

import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from core.base import BaseSource, BaseSink


class PlotSink(BaseSink):
    """
    Params:
     - *sources*: a list of tuple, where (BaseSource, chunk_size). Maximum = 4
    """
    def __init__(self, sources: list[tuple[BaseSource, int]]):
        super().__init__(sources[0][0])
        self.ani = None
        self.sources = sources
        self._colors = ['green', 'red', 'black', 'magenta']

        self.fig, self.axes = plt.subplots(len(self.sources), 1)
        self.fig.set_size_inches((8, 6 * len(self.sources)))
        self.lines = []

        if len(self.sources) == 1:
            self.axes = [self.axes]

        for i, (_, chunk_size) in enumerate(sources):
            ax: plt.Axes = self.axes[i]
            x = np.arange(chunk_size)
            y = np.zeros(chunk_size)
            line, = ax.plot(x, y, color=self._colors[i]) # or i % len(self._colors)
            ax.grid(True, alpha=0.3)
            ax.set_ylim((-0.65, 0.65))
            ax.set_xlim((0, chunk_size))
            self.lines.append(line)
        self.fig.tight_layout()

    def write(self, chunk: np.ndarray):
        pass

    def _update(self, frame):
        for (i, src) in enumerate(self.sources):
            try:
                chunk = next(src[0])
                if chunk is not None:
                    # i = ax index
                    self.lines[i].set_ydata(chunk)
            except StopIteration:
                pass
            except Exception as e:
                print(f"Plot update error on track {i}: {e}")

        return self.lines

    def show(self):
        # Важно: открываем ВСЕ источники через контекстные менеджеры
        # Для простоты можно использовать ExitStack, но для школы пока хватит обычного запуска
        self.ani = FuncAnimation(
            self.fig, self._update, interval=40,
            blit=False, cache_frame_data=False
        )
        plt.show()

class AudioSink(BaseSink):
    def __init__(self, source: BaseSource):
        super().__init__(source)
        self.source = source
        self._stream = sd.OutputStream(
            samplerate=self.source.samplerate, channels=1, blocksize=self.source.chunk_size,
            callback=self._callback,
            latency='low' # test. Work well on good pc
        )

    def write(self, chunk: np.ndarray):
        """Action to perform on the data (plot, save, etc.)"""
        # self._queue.put(chunk)
        pass

    def __enter__(self):
        # Ничего не стартуем здесь, просто возвращаем сам объект
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Гарантированное выключение при любой ошибке
        if self._stream:
            self._stream.stop()
            self._stream.close()

    def _callback(self, outdata, frames, time, status):
        if status:
            print(f"Status: {status}")
        try:
            # Вытягиваем данные по цепочке
            chunk = next(self.source)

            # Подгоняем форму массива под outdata (нужно (frames, channels))
            outdata[:] = chunk.reshape(-1, 1)
        except StopIteration:
            # Если данные кончились, заполняем тишиной и останавливаемся
            outdata.fill(0)
            print('Ran out of data')
            raise sd.CallbackStop


    def _finished_callback(self):
        self._stream.stop()
        self._stream.__exit__()
        pass

    def start(self):
        self._stream.start()

    def play(self):
        with self:  # Гарантирует закрытие стрима (динамиков)
            with self.source:  # Гарантирует закрытие источника (микрофона/файла)

                self._stream.start()
                print("▶ Воспроизведение начато...")

                # Пока стрим активен, основной поток спит,
                # а всю работу в фоне делает _callback
                while self._stream.active:
                    sd.sleep(100)
