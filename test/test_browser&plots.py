from core.processors import Splitter, FFTProcessor
from core.sinks import PlotSink
from core.sources import DeviceSource

src = DeviceSource()

splt = Splitter(src)
analyzed = FFTProcessor(splt.branch())

plot = PlotSink([
    (splt, splt.chunk_size),
    (analyzed, analyzed.chunk_size // 2 + 1)
])

with src:
    plot.show()