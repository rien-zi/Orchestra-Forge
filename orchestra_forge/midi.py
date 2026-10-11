"""Small Standard MIDI File (SMF) type-1 writer using only the Python stdlib."""
from pathlib import Path
import struct

from .composition import PPQ, Composition


def _vlq(value: int) -> bytes:
    value = max(0, value)
    buffer = value & 0x7F
    while (value := value >> 7):
        buffer <<= 8
        buffer |= (value & 0x7F) | 0x80
    out = bytearray()
    while True:
        out.append(buffer & 0xFF)
        if buffer & 0x80:
            buffer >>= 8
        else:
            break
    return bytes(out)


def _track_chunk(events: list[tuple[int, int, bytes]], end_tick: int) -> bytes:
    events.sort(key=lambda e: (e[0], e[1]))
    data = bytearray()
    previous = 0
    for tick, _, payload in events:
        data.extend(_vlq(tick - previous))
        data.extend(payload)
        previous = tick
    data.extend(_vlq(max(0, end_tick - previous)) + b"\xff\x2f\x00")
    return b"MTrk" + struct.pack(">I", len(data)) + data


def write_midi(path: Path, composition: Composition) -> None:
    tempo = round(60_000_000 / composition.bpm)
    title = composition.title.encode("utf-8")
    end_tick = round(composition.beats * PPQ)
    conductor = [
        (0, 0, b"\xff\x03" + _vlq(len(title)) + title),
        (0, 1, b"\xff\x51\x03" + tempo.to_bytes(3, "big")),
        (0, 2, b"\xff\x58\x04\x04\x02\x18\x08"),
    ]
    chunks = [_track_chunk(conductor, end_tick)]
    for part in composition.parts:
        name = part.name.encode("utf-8")
        events = [(0, 0, b"\xff\x03" + _vlq(len(name)) + name),
                  (0, 1, bytes((0xC0 | part.channel, part.program)))]
        for note in part.notes:
            start = round(note.start * PPQ)
            end = round((note.start + note.duration) * PPQ)
            events.append((start, 3, bytes((0x90 | part.channel, note.pitch, note.velocity))))
            events.append((end, 2, bytes((0x80 | part.channel, note.pitch, 0))))
        chunks.append(_track_chunk(events, end_tick))
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQ)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + b"".join(chunks))
