from core.processors import Splitter, FFTProcessor, NoteDetector
from core.sinks import PlotSink, PumpSink
from core.sources import DeviceSource
from core.telemetry import MonitorBuffers

src = DeviceSource()

splt = Splitter(src)

raw = splt.branch_lossy("RawBuff")
analyzed = FFTProcessor(splt.branch_lossy())

# prev_note: str | None = None
# prev_octave: int | None = None
def at_note(note: str, octave: int):
    # global prev_note, prev_octave
    #
    # if prev_note != note or prev_octave != octave:
    #     prev_note = note
    #     prev_octave = octave
        print(f"Note: {note}, Octave: {octave}")


detector = NoteDetector(analyzed, at_note)

plot = PlotSink([
    (raw, raw.chunk_size),
    (detector, detector.chunk_size // 2 + 1)
])
pump = PumpSink(splt)

with src, pump:
    plot.show()
