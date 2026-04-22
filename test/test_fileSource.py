from core.sources import FileSource
from core.sinks import AudioSink, PlotSink

src = FileSource('/home/dima/Music/Billie Eilish - Billie Bossa Nova.wav')
sink = AudioSink(src)
sink.play()