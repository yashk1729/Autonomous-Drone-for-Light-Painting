#!/usr/bin/env python3
import sys, json, time, subprocess, os
from pymavlink import mavutil

LED_SCRIPT = "/home/led25.py"
MAVLINK_ENDPOINT = "udpout:127.0.0.1:14551"

def usage():
    print("Usage:")
    print("  sudo python3 mission_led.py <mission.leds.json>")
    print("")
    print("JSON example:")
    print('  { "0": "red", "1": "green", "2": "off", "3": "blue" }')
    print("Keys = waypoint indices (0,1,2,...)")
    print("Values = color names understood by led25.py (red, blue, off, ...)")
    sys.exit(1)

def load_led_map(path):
    if not os.path.exists(path):
        print(f"LED config file not found: {path}")
        usage()
    with open(path, "r") as f:
        raw = json.load(f)
    mapping = {}
    for k, v in raw.items():
        try:
            idx = int(k)
        except ValueError:
            print(f"Skipping invalid key (not int): {k}")
            continue
        color = str(v).lower()
        mapping[idx] = color
    print("Loaded LED map:", mapping)
    return mapping

def set_color(color):
    print(f"Setting LEDs to: {color}")
    subprocess.run(["python3", LED_SCRIPT, color], check=False)
def main():
    if len(sys.argv) != 2:
        usage()

    led_cfg_path = sys.argv[1]
    wp_to_color = load_led_map(led_cfg_path)
    if not wp_to_color:
        print("No valid LED mappings, exiting.")
        sys.exit(1)

    print(f"Connecting to MAVLink at {MAVLINK_ENDPOINT} ...")
    master = mavutil.mavlink_connection(MAVLINK_ENDPOINT)
    master.mav.heartbeat_send(0,0,0,0,0)
    master.wait_heartbeat()
    print(f"Heartbeat from system {master.target_system} component {master.target_component}")

    current_color = None
    print("Listening for MISSION_ITEM_REACHED messages...")
    try:
        while True:
            msg = master.recv_match(blocking=True, timeout=1)
            if msg is None:
                continue
            if msg.get_type() == "MISSION_ITEM_REACHED":
                seq = msg.seq
                print(f"MISSION_ITEM_REACHED seq={seq}")
                if seq in wp_to_color:
                    target_color = wp_to_color[seq]
                    if target_color != current_color:
                        set_color(target_color)
                        current_color = target_color
    except KeyboardInterrupt:
        print("Stopping mission_led, turning LEDs off")
        set_color("off")


if __name__ == "__main__":
    main()
