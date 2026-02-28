# Convert local XY (meters after scaling) to lat/lon/alt with site origin and yaw.
import numpy as np
import math, sys

R_EARTH = 6378137.0  # meters

def apply_scene_transform(xy_local, scale_m_per_svg, yaw_deg, offset_xy=(0,0)):
    xy = xy_local * float(scale_m_per_svg)
    yaw = math.radians(yaw_deg)
    R = np.array([[ math.cos(yaw), -math.sin(yaw)],
                  [ math.sin(yaw),  math.cos(yaw)]])
    xy = xy @ R.T
    xy[:,0] += offset_xy[0]  # East
    xy[:,1] += offset_xy[1]  # North
    return xy

def enu_to_ll(x_m_east, y_m_north, lat0_deg, lon0_deg):
    lat0 = math.radians(lat0_deg)
    dlat = y_m_north / R_EARTH
    dlon = x_m_east / (R_EARTH * math.cos(lat0))
    lat = lat0 + dlat
    lon = math.radians(lon0_deg) + dlon
    return math.degrees(lat), math.degrees(lon)

def convert(csv_in, csv_out, lat0, lon0, alt0, scale, yaw_deg, z_mode="REL", z_offset=0.0):
    pts = np.loadtxt(csv_in, delimiter=",", skiprows=1)  # x_local,y_local,z_local
    if pts.ndim == 1 and pts.size > 0:
        pts = pts.reshape(1, -1)
    xy_local = pts[:, :2]
    z_local  = pts[:, 2] if pts.shape[1] > 2 else np.zeros(len(pts))
    xy = apply_scene_transform(xy_local, scale, yaw_deg, (0,0))
    lats, lons, alts = [], [], []
    for (x_e, y_n), z in zip(xy, z_local):
        lat, lon = enu_to_ll(x_e, y_n, lat0, lon0)
        if z_mode.upper() == "AMSL":
            alt = alt0 + z + z_offset
        elif z_mode.upper() == "REL":
            alt = z + z_offset  # relative altitude is handled by mission frame
        else:
            alt = alt0 + z + z_offset
        lats.append(lat); lons.append(lon); alts.append(alt)
    arr = np.vstack([lats,lons,alts]).T
    np.savetxt(csv_out, arr, delimiter=",", header="lat,lon,alt", comments="")
    print(f"Saved {arr.shape[0]} geo points to {csv_out}")

if __name__ == "__main__":
    # Example: python local_to_geo.py local_points.csv geo_points.csv 50.962894 11.330310 0.0 0.001 90 REL 5.0
    _, csv_in, csv_out, lat0, lon0, alt0, scale, yaw, zmode, zoff = sys.argv
    convert(csv_in, csv_out, float(lat0), float(lon0), float(alt0), float(scale), float(yaw), zmode, float(zoff))
