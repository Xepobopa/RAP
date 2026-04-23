from core.processors import PitchProcessor, Splitter, FFTProcessor
from core.sinks import PlotSink, AudioSink
from core.sources import DeviceSource, FileSource

chunk_size = 1024

src = FileSource('/home/dima/Music/Billie Eilish - Billie Bossa Nova.wav', chunk_size)

shifted_data = PitchProcessor(src, 1)
splt = Splitter(shifted_data)

plot = PlotSink([
    (splt.branch_lossy(), chunk_size),
    (FFTProcessor(splt.branch_lossy()), chunk_size // 2 + 1)
])

player = AudioSink(splt)

with src, player:
    player.start()
    plot.show()