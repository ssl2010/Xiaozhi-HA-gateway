#!/usr/bin/env python3
"""Run the deployed Paraformer model against one or more mono PCM WAV files."""

from __future__ import annotations

import argparse
import time
import wave
from pathlib import Path

import numpy as np
import sherpa_onnx


def read_wave(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as source:
        if source.getnchannels() != 1 or source.getsampwidth() != 2:
            raise ValueError(f"{path}: expected mono 16-bit PCM WAV")
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype=np.int16)
        return samples.astype(np.float32) / 32768.0, source.getframerate()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", type=Path)
    parser.add_argument("wav", nargs="+", type=Path)
    args = parser.parse_args()

    recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
        paraformer=str(args.model_dir / "model.int8.onnx"),
        tokens=str(args.model_dir / "tokens.txt"),
        num_threads=2,
        sample_rate=16000,
        feature_dim=80,
        decoding_method="greedy_search",
        debug=False,
    )
    for wav_path in args.wav:
        samples, sample_rate = read_wave(wav_path)
        stream = recognizer.create_stream()
        started = time.monotonic()
        stream.accept_waveform(sample_rate, samples)
        recognizer.decode_stream(stream)
        elapsed = time.monotonic() - started
        duration = len(samples) / sample_rate
        print(f"{wav_path.name}\t{duration:.2f}s\t{elapsed:.3f}s\t{stream.result.text}")


if __name__ == "__main__":
    main()
