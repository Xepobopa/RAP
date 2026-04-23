from core.processors import Splitter, FFTProcessor
from core.sinks import AudioSink, PlotSink
from core.sources import DeviceSource, FileSource
from core.telemetry import MonitorBuffers

CHUNK_SIZE = 1024

monitor = MonitorBuffers()

src = FileSource('/home/dima/Music/Billie Eilish - Billie Bossa Nova.wav', CHUNK_SIZE)
splt = Splitter(src, monitor)

src_raw = splt.branch_lossy("RawBuff (1)")
src_analyzed = FFTProcessor(splt.branch_lossy())

audio = AudioSink(splt)
plot = PlotSink([
    (src_raw, src_raw.chunk_size),
    (src_analyzed, src_analyzed.chunk_size // 2 + 1)
])

with src, audio, monitor:
    audio.start()
    plot.show()
