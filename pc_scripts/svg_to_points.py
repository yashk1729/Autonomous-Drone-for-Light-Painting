# pip install svgpathtools numpy
from svgpathtools import svg2paths2
import numpy as np
import sys

def sample_path(path, step_m_local):
    L = path.length()
    if L == 0:
        return []
    n = max(1, int(np.ceil(L / step_m_local)))
    ts = np.linspace(0, 1, n+1)
    pts = [path.point(t) for t in ts]
    return np.array([[p.real, p.imag] for p in pts], dtype=float)

def svg_to_local_points(svg_file, step_m_local=1.0, z_local=0.0):
    paths, attrs, svg_attr = svg2paths2(svg_file)
    all_pts = []
    for p in paths:
        try:
            segments = p.continuous_subpaths()
        except:
            segments = [p]
        for s in segments:
            pts2d = sample_path(s, step_m_local)
            if len(pts2d) == 0:
                continue
            zcol = np.full((pts2d.shape[0],1), float(z_local))
            all_pts.append(np.hstack([pts2d, zcol]))
    if not all_pts:
        return np.zeros((0,3))
    return np.vstack(all_pts)

if __name__ == "__main__":
    svg = sys.argv[1]
    step = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    pts = svg_to_local_points(svg, step_m_local=step, z_local=0.0)
    np.savetxt("local_points.csv", pts, delimiter=",", header="x_local,y_local,z_local", comments="")
    print(f"Saved {pts.shape[0]} points to local_points.csv")
