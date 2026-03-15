from __future__ import annotations

import io
import math
import wave
from array import array
from typing import Dict, Optional

import pygame


class AudioManager:
    def __init__(self) -> None:
        self.available = False
        self.master_volume = 0.8
        self.bgm_volume = 0.65
        self.sfx_volume = 0.8
        self.sfx: Dict[str, pygame.mixer.Sound] = {}
        self.bgm_sound: Optional[pygame.mixer.Sound] = None
        self.bgm_channel: Optional[pygame.mixer.Channel] = None
        self.sfx_channel: Optional[pygame.mixer.Channel] = None
        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        except pygame.error:
            self.available = False
            return
        self.available = True
        self.bgm_channel = pygame.mixer.Channel(0)
        self.sfx_channel = pygame.mixer.Channel(1)
        self._build_default_audio()

    def _build_default_audio(self) -> None:
        self.sfx["click"] = self._tone_sound(860, 0.06, 0.35)
        self.sfx["confirm"] = self._tone_sound(620, 0.10, 0.45)
        self.sfx["error"] = self._tone_sound(240, 0.12, 0.5)
        self.sfx["success"] = self._chord_sound((392, 494, 587), 0.20, 0.35)
        self.bgm_sound = self._bgm_loop_sound()

    def play_bgm(self) -> None:
        if not self.available or self.bgm_channel is None or self.bgm_sound is None:
            return
        if not self.bgm_channel.get_busy():
            self.bgm_channel.play(self.bgm_sound, loops=-1)
        self.bgm_channel.set_volume(self.master_volume * self.bgm_volume)

    def stop_bgm(self) -> None:
        if self.bgm_channel is not None:
            self.bgm_channel.stop()

    def play_sfx(self, key: str) -> None:
        if not self.available or self.sfx_channel is None:
            return
        sound = self.sfx.get(key)
        if sound is None:
            return
        sound.set_volume(self.master_volume * self.sfx_volume)
        self.sfx_channel.play(sound)

    def set_volumes(self, master: float, bgm: float, sfx: float) -> None:
        self.master_volume = max(0.0, min(1.0, master))
        self.bgm_volume = max(0.0, min(1.0, bgm))
        self.sfx_volume = max(0.0, min(1.0, sfx))
        if self.bgm_channel is not None:
            self.bgm_channel.set_volume(self.master_volume * self.bgm_volume)

    def _tone_sound(self, frequency: float, duration_sec: float, amplitude: float) -> pygame.mixer.Sound:
        wav_bytes = _build_wave_bytes([(frequency, duration_sec, amplitude)])
        return pygame.mixer.Sound(file=io.BytesIO(wav_bytes))

    def _chord_sound(self, frequencies: tuple[float, ...], duration_sec: float, amplitude: float) -> pygame.mixer.Sound:
        steps = [(freq, duration_sec, amplitude / len(frequencies)) for freq in frequencies]
        wav_bytes = _build_mixed_wave_bytes(steps)
        return pygame.mixer.Sound(file=io.BytesIO(wav_bytes))

    def _bgm_loop_sound(self) -> pygame.mixer.Sound:
        # Procedural chiptune loop to avoid shipping licensed music assets.
        sequence = [
            (261.63, 0.24, 0.20),
            (329.63, 0.24, 0.20),
            (392.00, 0.24, 0.20),
            (329.63, 0.24, 0.20),
            (293.66, 0.24, 0.18),
            (349.23, 0.24, 0.20),
            (440.00, 0.24, 0.20),
            (349.23, 0.24, 0.20),
        ]
        sequence = sequence * 4
        wav_bytes = _build_wave_bytes(sequence, waveform="triangle")
        return pygame.mixer.Sound(file=io.BytesIO(wav_bytes))


def _build_wave_bytes(
    sequence: list[tuple[float, float, float]],
    *,
    sample_rate: int = 44100,
    waveform: str = "square",
) -> bytes:
    samples = array("h")
    for frequency, duration_sec, amplitude in sequence:
        count = max(1, int(sample_rate * duration_sec))
        for i in range(count):
            t = i / sample_rate
            if waveform == "triangle":
                phase = (t * frequency) % 1.0
                value = 4 * abs(phase - 0.5) - 1
            elif waveform == "sine":
                value = math.sin(2 * math.pi * frequency * t)
            else:
                value = 1.0 if math.sin(2 * math.pi * frequency * t) >= 0 else -1.0
            sample = int(32767 * amplitude * value)
            samples.append(max(-32767, min(32767, sample)))
    return _pack_wav(samples, sample_rate)


def _build_mixed_wave_bytes(
    sequence: list[tuple[float, float, float]],
    *,
    sample_rate: int = 44100,
) -> bytes:
    count = max(1, int(sample_rate * max(item[1] for item in sequence)))
    samples = array("h", [0] * count)
    for frequency, duration_sec, amplitude in sequence:
        duration_count = max(1, int(sample_rate * duration_sec))
        for i in range(min(count, duration_count)):
            t = i / sample_rate
            value = math.sin(2 * math.pi * frequency * t)
            sample = int(32767 * amplitude * value)
            mixed = samples[i] + sample
            samples[i] = max(-32767, min(32767, mixed))
    return _pack_wav(samples, sample_rate)


def _pack_wav(samples: array, sample_rate: int) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())
    return output.getvalue()

