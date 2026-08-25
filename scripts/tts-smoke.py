#!/usr/bin/env python3
"""Measure Edge TTS availability without saving or logging audio content."""

from __future__ import annotations

import argparse
import asyncio
import time

import edge_tts


async def synthesize(text: str, voice: str) -> None:
    started = time.monotonic()
    audio_bytes = 0
    async for chunk in edge_tts.Communicate(text, voice=voice).stream():
        if chunk.get("type") == "audio":
            audio_bytes += len(chunk.get("data", b""))
    elapsed = time.monotonic() - started
    if audio_bytes == 0:
        raise RuntimeError("TTS returned no audio")
    print(f"edge-tts\t{audio_bytes} bytes\t{elapsed:.3f}s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="?", default="主卧空调已打开")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    args = parser.parse_args()
    asyncio.run(synthesize(args.text, args.voice))


if __name__ == "__main__":
    main()
