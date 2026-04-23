import matplotlib

from sys import platform

from core.processors import FFTProcessor, Splitter
from core.telemetry import MonitorBuffers

if platform == "linux" or platform == "linux2":
    matplotlib.use('TkAgg') # Исправляет "non-interactive"

from core.sources import DeviceSource
from core.sinks import PlotSink

CHUNK_SIZE = 1024
monitor = MonitorBuffers()

source = DeviceSource(chunk_size=CHUNK_SIZE, monitor=monitor)

fft = FFTProcessor(source)

sink1 = PlotSink([
    (source, source.chunk_size),
    (fft, fft.chunk_size // 2 + 1)
])

with source, monitor:
    sink1.show()