from core.sources import FileSource
from core.sinks import AudioSink, PlotSink

src = FileSource('/home/dima/Music/Billie Eilish - Billie Bossa Nova.wav')
sink = PlotSink([(src, 1024)])
sink.show()