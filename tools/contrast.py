#!/usr/bin/env python3
"""按 WCAG 2.x 相对亮度公式复算 --faint 在站点实际背景上的对比度。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKGROUNDS = ["#0a0d14", "#13151c", "#171a21", "#111623", "#0d121c"]
THRESHOLD = 4.5


def rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def luminance(hex_color: str) -> float:
    channels = []
    for component in rgb(hex_color):
        srgb = component / 255
        linear = srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4
        channels.append(linear)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def ratio(foreground: str, background: str) -> float:
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def main() -> int:
    css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    match = re.search(r"--faint:\s*(#[0-9a-fA-F]{6})", css)
    if not match:
        print("FAIL: 无法从 assets/site.css 读取 --faint")
        return 1
    faint = match.group(1)

    print(f"token: --faint = {faint} (source: assets/site.css)")
    print(f"{'foreground':<12} {'background':<12} {'ratio':>8} {'threshold':>10} result")
    failed = False
    for background in BACKGROUNDS:
        value = ratio(faint, background)
        passed = value >= THRESHOLD
        failed = failed or not passed
        print(
            f"{faint:<12} {background:<12} {value:>7.2f}:1 {THRESHOLD:>9.1f}:1 "
            f"{'PASS' if passed else 'FAIL'}"
        )
    print("RESULT: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
