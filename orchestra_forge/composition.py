"""Composition data and JSON loading. Timing is measured in quarter-note beats."""
from dataclasses import dataclass
import json
import math
from pathlib import Path

PPQ = 480

@dataclass(frozen=True)
class Note:
    start: float
    duration: float
    pitch: int
    velocity: int

@dataclass(frozen=True)
class Part:
    name: str
    program: int
    channel: int
    notes: tuple[Note, ...]

@dataclass(frozen=True)
class Composition:
    title: str
    bpm: float
    beats: float
    parts: tuple[Part, ...]

    @property
    def seconds(self) -> float:
        return self.beats * 60 / self.bpm


def _number(value, label, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{label} must be between {low} and {high}")
    return value


def _integer(value, label, low, high):
    _number(value, label, low, high)
    if not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def load_composition(path: Path) -> Composition:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("Composition must be a JSON object")
    if not isinstance(data.get("parts"), list):
        raise ValueError("parts must be a list")
    title = data["title"]
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a nonempty string")
    bpm = _number(data["bpm"], "bpm", 4, 1000)
    beats = _number(data["beats"], "beats", 0.01, 100000)
    parts = []
    channels = set()
    for item in data["parts"]:
        if not isinstance(item, dict) or not isinstance(item.get("notes"), list):
            raise ValueError("Each part must be an object with a notes list")
        name = item["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("part name must be a nonempty string")
        channel = _integer(item["channel"], "channel", 0, 15)
        if channel in channels or channel == 9:
            raise ValueError("Use unique melodic channels; channel 9 is reserved for percussion")
        channels.add(channel)
        program = _integer(item["program"], "program", 0, 127)
        notes = []
        for start, duration, pitch, velocity in item["notes"]:
            _number(start, "note start", 0, beats)
            _number(duration, "note duration", 0.001, beats)
            if start + duration > beats + 1e-8:
                raise ValueError("note extends beyond composition beats")
            notes.append(Note(start, duration, _integer(pitch, "pitch", 0, 127), _integer(velocity, "velocity", 1, 127)))
        parts.append(Part(name, program, channel, tuple(notes)))
    if not parts:
        raise ValueError("At least one part is required")
    return Composition(title, bpm, beats, tuple(parts))
