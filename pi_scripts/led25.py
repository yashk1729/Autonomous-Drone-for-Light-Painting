#!/usr/bin/env python3
import sys
import time

import board
import neopixel

# ===== CONFIG =====
LED_PIN = board.D18        # GPIO18 (physical pin 12)
LED_COUNT = 25             # First 25 LEDs
BRIGHTNESS = 1.0           # 0.0 - 1.0
# ===================

COLOR_MAP = {
    "red":        (255,   0,   0),
    "green":      (  0, 255,   0),
    "blue":       (  0,   0, 255),
    "brown":      (255, 100,  20),
    "white":      (255, 255, 255),
    "yellow":     (255, 255,   0),
    "cyan":       (  0, 255, 255),
    "magenta":    (255,   0, 255),
    "orange":     (255, 165,   0),
    "purple":     (128,   0, 128),
    "pink":       (255, 105, 180),
    "warmwhite":  (255, 244, 229),
    "coldwhite":  (200, 220, 255),
    "off":        (  0,   0,   0),
}

pixels = neopixel.NeoPixel(
    LED_PIN,
    LED_COUNT,
    brightness=BRIGHTNESS,
    auto_write=False,
    pixel_order=neopixel.GRB,
)

def set_all(color):
    for i in range(LED_COUNT):
        pixels[i] = color
    pixels.show()

def usage():
    print("Usage:")
    print("  sudo python3 led25.py <color>")
    print("")
    print("Colors:")
    print("  " + ", ".join(sorted(COLOR_MAP.keys())))
    sys.exit(1)

def main():
    if len(sys.argv) != 2:
        usage()

    name = sys.argv[1].lower()
    if name not in COLOR_MAP:
        print(f"Unknown color '{name}'")
        usage()

    set_all(COLOR_MAP[name])
    print(f"LEDs: {name.upper()}")

    time.sleep(0.1)

if __name__ == "__main__":
    main()
