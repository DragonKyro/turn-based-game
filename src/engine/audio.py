"""Procedural chiptune audio — music + SFX synthesized to WAV files on first run.

Keeps the repo free of binary assets. First load generates the tracks under
`saves/audio/` via the `wave` module; subsequent loads use the cached files.
Style is square-wave chiptune with simple arpeggiated chord progressions, in the
spirit of Advance Wars / Wargroove map themes (on a much smaller budget).
"""
from __future__ import annotations

import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path

import arcade

from src.config import ASSETS_DIR

_AUDIO_DIR = ASSETS_DIR / "audio"
_SAMPLE_RATE = 22_050
_AMPLITUDE = 6_000  # int16, safely below clipping when voices sum

# --- Music ------------------------------------------------------------------
# Notes in Hz (C minor palette — works for both martial and lyrical moods).
_NOTES = {
    "C2": 65.41,  "D2": 73.42,  "Eb2": 77.78, "F2": 87.31, "G2": 98.00, "Ab2": 103.83, "Bb2": 116.54,
    "C3": 130.81, "D3": 146.83, "Eb3": 155.56, "F3": 174.61, "G3": 196.00, "Ab3": 207.65, "Bb3": 233.08,
    "C4": 261.63, "D4": 293.66, "Eb4": 311.13, "F4": 349.23, "G4": 392.00, "Ab4": 415.30, "Bb4": 466.16,
    "C5": 523.25, "D5": 587.33, "Eb5": 622.25, "F5": 698.46, "G5": 783.99,
    "REST": 0.0,
}

# --- Track data -------------------------------------------------------------
# Each track is a (bass, melody) pair of note lists with a tempo.
# Notes are played as eighth-notes at the given tempo.

_EMBERCROWN_THEME_BASS = [
    "C3", "C3", "G2", "G2", "Ab2", "Ab2", "Eb3", "Eb3",
    "F2", "F2", "C3", "C3", "G2", "G2", "Bb2", "Bb2",
    "C3", "C3", "G2", "G2", "Ab2", "Ab2", "Eb3", "Eb3",
    "F2", "F2", "C3", "C3", "G2", "Bb2", "C3", "REST",
]
_EMBERCROWN_THEME_MELODY = [
    "C5", "Eb5", "G5", "Eb5", "C5", "Bb4", "G4", "Bb4",
    "Ab4", "C5", "F5", "C5", "Ab4", "G4", "F4", "G4",
    "C5", "Eb5", "G5", "Eb5", "Bb4", "C5", "D5", "C5",
    "F5", "Eb5", "C5", "Bb4", "C5", "D5", "Eb5", "REST",
]

_BATTLE_BASS = [
    "C3", "C3", "C3", "G2", "Ab2", "Ab2", "Eb3", "G3",
    "F2", "F2", "F2", "C3", "Bb2", "Bb2", "Bb2", "F3",
    "C3", "G2", "Ab2", "Eb3", "F2", "C3", "Bb2", "G3",
    "C3", "Eb3", "G3", "Bb3", "G3", "Eb3", "C3", "REST",
]
_BATTLE_MELODY = [
    "G5", "Eb5", "C5", "Eb5", "G5", "F5", "Eb5", "D5",
    "F5", "D5", "Bb4", "D5", "F5", "Eb5", "D5", "C5",
    "G5", "Eb5", "C5", "Bb4", "C5", "D5", "Eb5", "F5",
    "G5", "Ab4", "C5", "Eb5", "G5", "Eb5", "C5", "REST",
]


@dataclass(frozen=True)
class _TrackSpec:
    filename: str
    bass: list[str]
    melody: list[str]
    bpm: int


_MUSIC_TRACKS: dict[str, _TrackSpec] = {
    "title":  _TrackSpec("theme_embercrown.wav",
                         _EMBERCROWN_THEME_BASS, _EMBERCROWN_THEME_MELODY, bpm=96),
    "battle": _TrackSpec("theme_battle.wav",
                         _BATTLE_BASS, _BATTLE_MELODY, bpm=124),
}


# --- SFX specs --------------------------------------------------------------
# (filename, frequency_start, frequency_end, duration_seconds, waveform)
_SFX_SPECS: dict[str, tuple[str, float, float, float, str]] = {
    "click":     ("sfx_click.wav",      880, 660, 0.07, "square"),
    "select":    ("sfx_select.wav",     660, 880, 0.08, "square"),
    "move":      ("sfx_move.wav",       440, 550, 0.08, "triangle"),
    "attack":    ("sfx_attack.wav",     240, 110, 0.18, "noise"),
    "build":     ("sfx_build.wav",      330, 660, 0.20, "square"),
    "turn_end":  ("sfx_turn_end.wav",   523, 784, 0.22, "square"),
    "victory":   ("sfx_victory.wav",    523, 1046, 0.55, "square"),
}


# --- Waveform helpers -------------------------------------------------------

def _square(phase: float) -> float:
    return 1.0 if (phase % 1.0) < 0.5 else -1.0


def _triangle(phase: float) -> float:
    p = phase % 1.0
    return 4 * p - 1 if p < 0.5 else 3 - 4 * p


def _saw(phase: float) -> float:
    return 2 * (phase % 1.0) - 1


def _noise(_phase: float) -> float:
    # Deterministic pseudo-noise from phase so successive calls differ.
    x = math.sin(_phase * 127.1) * 43758.5453
    return (x - math.floor(x)) * 2 - 1


def _render_voice(freq: float, samples: int, wave_fn, volume: float) -> list[float]:
    if freq <= 0.0:
        return [0.0] * samples
    out = []
    phase_step = freq / _SAMPLE_RATE
    phase = 0.0
    for _ in range(samples):
        out.append(wave_fn(phase) * volume)
        phase += phase_step
    return out


def _envelope(samples: int) -> list[float]:
    """Tiny attack / decay envelope to avoid clicks."""
    attack = min(samples // 10, 200)
    decay = min(samples // 5, 600)
    env = [1.0] * samples
    for i in range(attack):
        env[i] = i / max(1, attack)
    for i in range(decay):
        k = samples - 1 - i
        if k >= 0:
            env[k] = min(env[k], i / max(1, decay))
    return env


def _mix_to_int16(channels: list[list[float]]) -> list[int]:
    """Sum voices, clip, scale to int16."""
    n = min(len(c) for c in channels)
    out = []
    for i in range(n):
        s = sum(c[i] for c in channels)
        s = max(-1.0, min(1.0, s))
        out.append(int(s * _AMPLITUDE))
    return out


def _write_wav(path: Path, samples: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_SAMPLE_RATE)
        w.writeframes(b"".join(struct.pack("<h", s) for s in samples))


# --- Generators -------------------------------------------------------------

def _render_note(freq: float, samples: int, wave_fn, volume: float) -> list[float]:
    voice = _render_voice(freq, samples, wave_fn, volume)
    env = _envelope(samples)
    return [voice[i] * env[i] for i in range(samples)]


def _build_music(spec: _TrackSpec) -> list[int]:
    eighth_note_sec = 60.0 / spec.bpm / 2.0
    samples_per_eighth = int(_SAMPLE_RATE * eighth_note_sec)
    bass_channel: list[float] = []
    melody_channel: list[float] = []
    for note in spec.bass:
        bass_channel.extend(_render_note(_NOTES[note], samples_per_eighth, _triangle, 0.55))
    for note in spec.melody:
        melody_channel.extend(_render_note(_NOTES[note], samples_per_eighth, _square, 0.32))
    # Trim to the shorter for safe mixing.
    n = min(len(bass_channel), len(melody_channel))
    return _mix_to_int16([bass_channel[:n], melody_channel[:n]])


def _build_sfx(freq_start: float, freq_end: float, duration: float, waveform: str) -> list[int]:
    n = int(_SAMPLE_RATE * duration)
    wave_fn = {"square": _square, "triangle": _triangle,
               "saw": _saw, "noise": _noise}.get(waveform, _square)
    # Frequency sweep
    samples: list[float] = []
    phase = 0.0
    for i in range(n):
        f = freq_start + (freq_end - freq_start) * (i / max(1, n - 1))
        phase += f / _SAMPLE_RATE
        samples.append(wave_fn(phase) * 0.6)
    env = _envelope(n)
    merged = [samples[i] * env[i] for i in range(n)]
    return _mix_to_int16([merged])


# --- Public API -------------------------------------------------------------

class Audio:
    """Singleton-style: call `Audio.init()` once at startup."""

    _instance: "Audio | None" = None

    def __init__(self) -> None:
        self.enabled = True
        self.music_volume = 0.35
        self.sfx_volume = 0.6
        self._music_sounds: dict[str, arcade.Sound] = {}
        self._sfx_sounds: dict[str, arcade.Sound] = {}
        self._current_music_player = None
        self._current_track: str | None = None
        self._generate_if_missing()
        self._load_all()

    # --- class-level getter ---

    @classmethod
    def get(cls) -> "Audio":
        if cls._instance is None:
            cls._instance = Audio()
        return cls._instance

    # --- generation + loading ---

    def _generate_if_missing(self) -> None:
        try:
            for name, spec in _MUSIC_TRACKS.items():
                path = _AUDIO_DIR / spec.filename
                if not path.exists():
                    _write_wav(path, _build_music(spec))
            for name, (filename, fs, fe, dur, wf) in _SFX_SPECS.items():
                path = _AUDIO_DIR / filename
                if not path.exists():
                    _write_wav(path, _build_sfx(fs, fe, dur, wf))
        except Exception:
            # Audio is optional polish — if anything blows up here we just
            # silently disable audio and keep playing.
            self.enabled = False

    def _load_all(self) -> None:
        if not self.enabled:
            return
        try:
            for name, spec in _MUSIC_TRACKS.items():
                path = _AUDIO_DIR / spec.filename
                if path.exists():
                    self._music_sounds[name] = arcade.Sound(str(path), streaming=True)
            for name, (filename, *_rest) in _SFX_SPECS.items():
                path = _AUDIO_DIR / filename
                if path.exists():
                    self._sfx_sounds[name] = arcade.Sound(str(path))
        except Exception:
            self.enabled = False

    # --- playback ---

    def play_music(self, track: str) -> None:
        if not self.enabled or track == self._current_track:
            return
        self.stop_music()
        sound = self._music_sounds.get(track)
        if sound is None:
            return
        try:
            self._current_music_player = sound.play(volume=self.music_volume, loop=True)
            self._current_track = track
        except Exception:
            self.enabled = False

    def stop_music(self) -> None:
        if self._current_music_player is not None:
            try:
                self._current_music_player.pause()
            except Exception:
                pass
        self._current_music_player = None
        self._current_track = None

    def play_sfx(self, name: str) -> None:
        if not self.enabled:
            return
        sound = self._sfx_sounds.get(name)
        if sound is None:
            return
        try:
            sound.play(volume=self.sfx_volume)
        except Exception:
            pass
