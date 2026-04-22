from core.processors import Splitter, FFTProcessor
from core.sinks import AudioSink, PlotSink
from core.sources import DeviceSource, FileSource

CHUNK_SIZE = 1024

src = FileSource('/home/dima/Music/Billie Eilish - Billie Bossa Nova.wav', CHUNK_SIZE)
splt = Splitter(src)

src_raw = splt.branch()
src_analyzed = FFTProcessor(splt.branch())
audio = AudioSink(splt)
plot = PlotSink([
    (src_raw, src_raw.chunk_size),
    (src_analyzed, src_analyzed.chunk_size // 2 + 1)
])

with src, audio:
    audio.start()
    plot.show()
