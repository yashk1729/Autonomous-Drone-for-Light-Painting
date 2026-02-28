# Build a QGroundControl .plan from lat/lon/alt points (relative-alt mission by default)
import json, numpy as np, sys

def make_item(seq, lat, lon, alt, dwell_s=None, frame=3):
    # frame=3 => MAV_FRAME_GLOBAL_RELATIVE_ALT
    cmd_wp = 16  # MAV_CMD_NAV_WAYPOINT
    item = {
      "AMSLAltAboveTerrain": None,
      "Altitude": float(alt),
      "AltitudeMode": 1,
      "autoContinue": True,
      "command": cmd_wp,
      "doJumpId": seq+1,
      "frame": frame,
      "params": [0, 0, 0, 0, float(lat), float(lon), float(alt)],
      "type": "SimpleItem"
    }
    if dwell_s is not None:
        item["params"][0] = float(dwell_s)
    return item

def wrap_qgc(items, cruise=2.0):
    return {
      "fileType": "Plan",
      "geoFence": {"circles":[], "polygons":[], "version":2},
      "groundStation": "QGroundControl",
      "mission": {
        "cruiseSpeed": float(cruise),
        "firmwareType": 12,
        "hoverSpeed": 3,
        "items": items,
        "plannedHomePosition": [0,0,0],
        "vehicleType": 2,
        "version": 2
      },
      "rallyPoints": {"points":[], "version":2},
      "version":1
    }

if __name__ == "__main__":
    # Usage: python geo_to_qgc_plan.py geo_points.csv mission.plan 2.0 0.0
    _, csv_in, plan_out, speed_mps, dwell_s = sys.argv
    arr = np.loadtxt(csv_in, delimiter=",", skiprows=1)  # lat,lon,alt
    if arr.ndim == 1 and arr.size == 3:
        arr = arr.reshape(1,3)
    items = [make_item(i, lat, lon, alt, dwell_s=None if float(dwell_s)==0 else float(dwell_s), frame=3)
             for i,(lat,lon,alt) in enumerate(arr)]
    plan = wrap_qgc(items, cruise=float(speed_mps))
    with open(plan_out, "w") as f:
        json.dump(plan, f, indent=2)
    print(f"Wrote {len(items)} waypoints to {plan_out}")
