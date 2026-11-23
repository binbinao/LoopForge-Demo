#!/usr/bin/env python3
"""用 Python 标准库生成 1200x630 的本地 OG 封面（无字体、无外部依赖）。"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "og-cover.png"
WIDTH, HEIGHT = 1200, 630


def clamp(value: float) -> int:
    return max(0, min(255, int(round(value))))


def star_points(cx: float, cy: float, outer: float, inner: float) -> list[tuple[float, float]]:
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = outer if i % 2 == 0 else inner
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def in_polygon(x: float, y: float, points: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(points) - 1
    for i in range(len(points)):
        xi, yi = points[i]
        xj, yj = points[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def blend(
    base: tuple[float, float, float],
    color: tuple[int, int, int],
    strength: float,
) -> tuple[float, float, float]:
    factor = max(0.0, min(1.0, strength))
    return tuple(base[i] * (1 - factor) + color[i] * factor for i in range(3))


def glow(
    x: int,
    y: int,
    center: tuple[int, int],
    radius: float,
    color: tuple[int, int, int],
    strength: float,
) -> float:
    distance = math.hypot(x - center[0], y - center[1])
    if distance >= radius:
        return 0.0
    return (1 - distance / radius) ** 2 * strength


def chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def build_png() -> bytes:
    star = star_points(600, 315, 118, 50)
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)  # PNG filter type 0
        t = y / (HEIGHT - 1)
        base = (10 + 7 * t, 13 + 9 * t, 20 + 15 * t)
        for x in range(WIDTH):
            pixel = blend(base, (255, 138, 61), glow(x, y, (235, 110), 520, (255, 138, 61), 0.42))
            pixel = blend(pixel, (155, 140, 255), glow(x, y, (980, 520), 560, (155, 140, 255), 0.34))
            pixel = blend(pixel, (79, 209, 197), glow(x, y, (600, 630), 430, (79, 209, 197), 0.14))
            if in_polygon(x, y, star):
                pixel = blend(pixel, (255, 181, 69), 0.92)
            raw.extend(clamp(channel) for channel in pixel)

    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(build_png())
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({WIDTH}x{HEIGHT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
