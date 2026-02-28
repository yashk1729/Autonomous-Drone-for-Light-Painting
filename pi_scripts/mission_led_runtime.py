#!/usr/bin/env python3
"""
mission_led_runtime.py

Interactive LED controller for real missions:

1. Lists all .led.json LED plans in /home/led_plans
2. Asks you which one to use
3. Listens on UDP port 14550 for MAVLink (Mission Planner forwarding)
4. Watches MISSION_CURRENT and calls /home/led25.py
   whenever a waypoint has a non-blank LED command.

JSON file format (example):

{
  "0": "OFF",
  "1": "",
  "2": "red",
  "3": "",
  "4": "green",
  "5": ""
}

Rules:
- key  = waypoint index (0..N+1)
- val  = ""      -> NO CHANGE (keep current LED color)
- val  = "off"   -> turn LEDs off
- val  = "red"... -> set that color (must match led25.py COLOR_MAP keys)
"""

import json
import time
import subprocess
from pathlib import Path

from pymavlink import mavutil


# ====== CONFIG ======

LED_PLANS_DIR = Path("/home/led_plans")

# LISTEN on UDP port 14550 for MAVLink forwarded from Mission Planner
MAVLINK_CONNECTION = "udpin:0.0.0.0:14550"

# Path to the low-level LED driver script
LED25_PATH = "/home/led25.py"

# ====================


def choose_led_plan() -> Path:
    """List available LED plans (*.led.json) and ask the user to pick one."""
    if not LED_PLANS_DIR.exists():
        print(f"[LED] Directory does not exist: {LED_PLANS_DIR}")
        raise SystemExit(1)

    files = sorted(
        [p for p in LED_PLANS_DIR.iterdir()
         if p.is_file() and p.name.endswith(".led.json")]
    )

    if not files:
        print(f"[LED] No .led.json files found in {LED_PLANS_DIR}")
        raise SystemExit(1)

    print("[LED] Available LED plans:")
    for i, f in enumerate(files):
        print(f"  [{i}] {f.name}")

    while True:
        try:
            choice = input(f"Select LED plan [0-{len(files)-1}]: ").strip()
            idx = int(choice)
            if 0 <= idx < len(files):
                selected = files[idx]
                print(f"[LED] Using plan: {selected}")
                return selected
            else:
                print("Invalid index, try again.")
        except ValueError:
            print("Please enter a number.")


def load_led_config(path: Path) -> dict:
    """Load the LED plan JSON from disk."""
    if not path.exists():
        print(f"[LED] Config file not found: {path}")
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            print("[LED] Config file is not a dict, ignoring")
            return {}
        print(f"[LED] Loaded config with {len(data)} entries from {path}")
        return data
    except Exception as e:
        print(f"[LED] Failed to load config: {e}")
        return {}


def get_led_command(led_cfg: dict, wp_index: int):
    """
    Return:
      None       -> no change
      "off"      -> turn LEDs off
      "red"/...  -> set that color (lowercase)
    """
    key = str(wp_index)
    if key not in led_cfg:
        return None

    val = str(led_cfg[key]).strip()
    if val == "":
        return None
    return val.lower()


def set_all_leds(color_name: str):
    """Call led25.py with the given color name."""
    print(f"[LED] Setting LEDs: {color_name}")
    try:
        subprocess.run(
            ["sudo", "python3", LED25_PATH, color_name],
            check=False
        )
    except Exception as e:
        print(f"[LED] Error running led25.py: {e}")


def main():
    # 1) Choose plan
    plan = choose_led_plan()
    led_cfg = load_led_config(plan)

    if not led_cfg:
        print("[LED] Empty config, nothing to do.")
        return

    # 2) Connect to MAVLink (listen for UDP from Mission Planner)
    print(f"[MAV] Connecting (listening) on {MAVLINK_CONNECTION} ...")
    mav = mavutil.mavlink_connection(MAVLINK_CONNECTION)

    current_wp = None
    current_color = None
    heartbeat_seen = False

    print("[MAV] Waiting for MAVLink messages (HEARTBEAT / MISSION_CURRENT)...")

    while True:
        msg = mav.recv_match(blocking=True, timeout=5)

        if msg is None:
            print("[MAV] No message for 5s, still listening...")
            continue

        mtype = msg.get_type()

        # Debug: show first few message types
        if not heartbeat_seen and mtype == "HEARTBEAT":
            heartbeat_seen = True
            print(f"[MAV] HEARTBEAT received from sys {msg.get_srcSystem()} comp {msg.get_srcComponent()}")

        # Only react to MISSION_CURRENT
        if mtype != "MISSION_CURRENT":
            # Uncomment the next line if you want to see everything:
            # print("[MAV] Got:", mtype)
            continue

        wp = int(msg.seq)

        if wp == current_wp:
            continue

        print(f"[MAV] Waypoint changed: {current_wp} -> {wp}")
        current_wp = wp

        cmd = get_led_command(led_cfg, wp)

        if cmd is None:
            print("[LED] No command for this waypoint (no change).")
            continue

        if cmd == current_color:
            print("[LED] Command same as current color, skipping.")
            continue

        set_all_leds(cmd)
        current_color = cmd

        time.sleep(0.1)


if __name__ == "__main__":
    main()
