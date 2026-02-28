import json
import math
import sys
from pathlib import Path

from svgpathtools import svg2paths

EARTH_RADIUS_M = 6378137.0  # WGS84


def load_config(config_path):
    with open(config_path, "r") as f:
        cfg = json.load(f)

    return {
        "lat0_deg": float(cfg["first_wp_lat_deg"]),
        "lon0_deg": float(cfg["first_wp_lon_deg"]),
        "heading_deg": float(cfg.get("heading_deg", 0.0)),
        "min_alt_m": float(cfg["min_alt_m"]),
        "max_alt_m": float(cfg["max_alt_m"]),
    }


# ---------- SVG helpers ----------

def parse_style(style_str: str) -> dict:
    """Parse an SVG 'style' string into a dict."""
    out = {}
    if not style_str:
        return out
    for part in style_str.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def choose_longest_path(paths):
    """Fallback: pick the longest path."""
    best = None
    best_len = -1.0
    for p in paths:
        length = p.length()
        if length > best_len:
            best_len = length
            best = p
    return best


def choose_flight_path(paths, attrs):
    """
    Try to pick the path you drew as a stroked, unfilled path
    (on your Flight Path layer), instead of filled shapes.

    Heuristic:
    - Prefer paths with stroke != none and fill == none.
    - Among those, pick the longest.
    - If none match, fall back to the overall longest path.
    """
    candidates = []

    for p, a in zip(paths, attrs):
        style = a.get("style", "")
        style_dict = parse_style(style)

        fill = style_dict.get("fill", a.get("fill", "")).lower()
        stroke = style_dict.get("stroke", a.get("stroke", "")).lower()

        has_stroke = stroke not in ("", "none")
        no_fill = (fill in ("", "none"))

        if has_stroke and no_fill:
            length = p.length()
            candidates.append((length, p))

    if candidates:
        candidates.sort(key=lambda t: t[0], reverse=True)
        return candidates[0][1]

    return choose_longest_path(paths)


def extract_nodes(path):
    """
    Extract ONLY the path nodes (the points you clicked with the Pen tool),
    not a dense sampling along the curve.

    Returns list of (x, y) pairs in SVG coordinate space.
    """
    if len(path) == 0:
        raise ValueError("Empty path")

    points = []

    first_seg = path[0]
    last_x = first_seg.start.real
    last_y = first_seg.start.imag
    points.append((last_x, last_y))

    for seg in path:
        x = seg.end.real
        y = seg.end.imag
        if abs(x - last_x) > 1e-9 or abs(y - last_y) > 1e-9:
            points.append((x, y))
            last_x, last_y = x, y

    return points


# ---------- Geometry: wall mode with altitude-defined scale ----------

def normalise_and_scale_wall(points, cfg):
    """
    Treat the drawing like a vertical wall:

    - X axis on paper: horizontal distance along the ground.
    - Y axis on paper: altitude.

    The vertical span in the drawing [y_min, y_max] is mapped linearly to
    [min_alt_m, max_alt_m].

    The same meters-per-SVG-unit factor is used for X and Y, so the wall
    keeps its proportions in meters.
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 points in path for scaling")

    x0, y0 = points[0]

    # Collect Y values to determine vertical span in the drawing
    y_values = [p[1] for p in points]
    y_min = min(y_values)  # top of drawing (smallest y)
    y_max = max(y_values)  # bottom of drawing (largest y)

    alt_min = cfg["min_alt_m"]
    alt_max = cfg["max_alt_m"]
    alt_range = alt_max - alt_min

    if abs(alt_range) < 1e-9:
        raise ValueError("min_alt_m and max_alt_m must be different")

    if abs(y_max - y_min) < 1e-9:
        # All points have the same Y -> flat altitude at mid of range
        alt_flat = 0.5 * (alt_min + alt_max)
        meters_per_svg = 1.0  # arbitrary; no true vertical scale

        heading_rad = math.radians(cfg["heading_deg"])
        cos_h = math.cos(heading_rad)
        sin_h = math.sin(heading_rad)

        en_points = []
        alt_list = []
        for (x, y) in points:
            s_svg = x - x0
            s_m = s_svg * meters_per_svg
            east = s_m * cos_h
            north = s_m * sin_h
            en_points.append((east, north))
            alt_list.append(alt_flat)
        return en_points, alt_list

    # Compute meters per SVG unit from vertical span:
    # y_min (highest point in drawing) -> alt_max
    # y_max (lowest point in drawing)  -> alt_min
    # so |y_max - y_min| SVG units correspond to |alt_range| meters
    meters_per_svg = abs(alt_range) / abs(y_max - y_min)

    # Precompute heading rotation
    heading_rad = math.radians(cfg["heading_deg"])
    cos_h = math.cos(heading_rad)
    sin_h = math.sin(heading_rad)

    en_points = []
    alt_list = []

    for (x, y) in points:
        # Horizontal ground distance: along X
        s_svg = x - x0            # +right on paper
        s_m = s_svg * meters_per_svg

        east = s_m * cos_h
        north = s_m * sin_h
        en_points.append((east, north))

        # Vertical mapping:
        # y_max (bottom on page) -> alt_min
        # y_min (top on page)    -> alt_max
        t = (y_max - y) / (y_max - y_min)  # 0 at y = y_max, 1 at y = y_min
        alt = alt_min + t * alt_range
        alt_list.append(alt)

    return en_points, alt_list


def en_to_latlon(cfg, en_points):
    """
    Convert (east_m, north_m) offsets to lat/lon using local flat-earth approx.
    """
    lat0 = math.radians(cfg["lat0_deg"])
    lon0 = math.radians(cfg["lon0_deg"])

    out = []
    for (east, north) in en_points:
        dlat = north / EARTH_RADIUS_M
        dlon = east / (EARTH_RADIUS_M * math.cos(lat0))

        lat = lat0 + dlat
        lon = lon0 + dlon

        out.append((math.degrees(lat), math.degrees(lon)))
    return out

def write_led_template(path_out, num_pattern_points):
    """
    Create LED config template JSON.

    Waypoint indices:
      0           : TAKEOFF  -> default "OFF"
      1..N        : pattern  -> default "" (blank, means 'no change')
      N+1         : LAND     -> default "OFF"
    """
    total_wp = num_pattern_points + 2  # TAKEOFF + pattern + LAND

    data = {}

    for i in range(total_wp):
        if i == 0 or i == total_wp - 1:
            # TAKEOFF and LAND: safe default
            data[str(i)] = "OFF"
        else:
            # Pattern waypoints: blank -> Pi script should 'do nothing'
            data[str(i)] = ""

    import json
    Path(path_out).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote LED template for {total_wp} waypoints to {path_out}")


def write_wpl(path_out, cfg, latlon_points, alt_list):
    """
    Write a Mission Planner .waypoints file with:
      0: TAKEOFF at home (cfg lat/lon)
      1..N: NAV_WAYPOINT from the drawing
      N+1: LAND at home
    """
    lines = ["QGC WPL 110"]

    lat_home = cfg["lat0_deg"]
    lon_home = cfg["lon0_deg"]

    # --- 0: TAKEOFF at home ---
    # Use altitude of the first drawing waypoint as target takeoff altitude
    takeoff_alt = alt_list[0] if alt_list else cfg["min_alt_m"]

    index = 0
    current = 1              # start here
    coord_frame = 3          # MAV_FRAME_GLOBAL_RELATIVE_ALT
    command = 22             # MAV_CMD_NAV_TAKEOFF
    p1 = 0                   # pitch, leave 0
    p2 = 0
    p3 = 0
    p4 = 0
    autocontinue = 1

    lines.append(
        f"{index}\t{current}\t{coord_frame}\t{command}\t"
        f"{p1}\t{p2}\t{p3}\t{p4}\t"
        f"{lat_home:.7f}\t{lon_home:.7f}\t{takeoff_alt:.2f}\t{autocontinue}"
    )

    # --- 1..N: drawing waypoints ---
    for i, ((lat, lon), alt) in enumerate(zip(latlon_points, alt_list), start=1):
        index = i
        current = 0
        coord_frame = 3        # MAV_FRAME_GLOBAL_RELATIVE_ALT
        command = 16           # MAV_CMD_NAV_WAYPOINT
        p1 = 0
        p2 = 0
        p3 = 0
        p4 = 0
        autocontinue = 1

        lines.append(
            f"{index}\t{current}\t{coord_frame}\t{command}\t"
            f"{p1}\t{p2}\t{p3}\t{p4}\t"
            f"{lat:.7f}\t{lon:.7f}\t{alt:.2f}\t{autocontinue}"
        )

    # --- N+1: LAND at home ---
    land_index = len(latlon_points) + 1
    index = land_index
    current = 0
    coord_frame = 3            # MAV_FRAME_GLOBAL_RELATIVE_ALT
    command = 21               # MAV_CMD_NAV_LAND
    p1 = 0
    p2 = 0
    p3 = 0
    p4 = 0
    land_alt = cfg["min_alt_m"]   # usually ignored by LAND, but set anyway
    autocontinue = 1

    lines.append(
        f"{index}\t{current}\t{coord_frame}\t{command}\t"
        f"{p1}\t{p2}\t{p3}\t{p4}\t"
        f"{lat_home:.7f}\t{lon_home:.7f}\t{land_alt:.2f}\t{autocontinue}"
    )

    Path(path_out).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(latlon_points)} pattern waypoints (+ TAKEOFF & LAND) to {path_out}")



def main():
    if len(sys.argv) != 4:
        print("Usage: python svg_to_basic_wpl.py <input.svg> <mission_config.json> <output.waypoints>")
        sys.exit(1)

    svg_path = sys.argv[1]
    cfg_path = sys.argv[2]
    out_path = sys.argv[3]

    cfg = load_config(cfg_path)

    paths, attrs = svg2paths(svg_path)

    main_path = choose_flight_path(paths, attrs)
    if main_path is None:
        raise RuntimeError("No paths found in SVG")

    # Use ONLY your pen-tool nodes
    node_points = extract_nodes(main_path)

    # Wall mode with altitude-defined scale
    en_points, alt_list = normalise_and_scale_wall(node_points, cfg)

    latlon_points = en_to_latlon(cfg, en_points)

    write_wpl(out_path, cfg, latlon_points, alt_list)
        # Also write an LED config template next to the waypoint file
    led_path = Path(out_path).with_suffix(".led.json")
    write_led_template(led_path, len(latlon_points))



if __name__ == "__main__":
    main()
