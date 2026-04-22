from core.processors import PitchProcessor
from core.sinks import PlotSink, AudioSink
from core.sources import DeviceSource

chunk_size = 1024

source = DeviceSource(chunk_size)
shifted_data = PitchProcessor(source, 1)
# plot = PlotSink(shifted_data, chunk_size)
# plot.show()

player = AudioSink(shifted_data, 44100, chunk_size)
player.play()