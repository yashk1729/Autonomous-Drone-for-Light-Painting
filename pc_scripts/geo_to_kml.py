# Quick 3D preview KML from lat,lon,alt CSV
import sys

TPL = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <Placemark>
    <name>Drone Path</name>
    <Style><LineStyle><width>3</width></LineStyle></Style>
    <LineString>
      <altitudeMode>absolute</altitudeMode>
      <coordinates>
        {coords}
      </coordinates>
    </LineString>
  </Placemark>
</Document>
</kml>"""

if __name__ == "__main__":
    _, csv_in, kml_out = sys.argv
    coords = []
    with open(csv_in) as f:
        header = f.readline()
        for line in f:
            if not line.strip():
                continue
            lat,lon,alt = [float(x) for x in line.strip().split(",")]
            coords.append(f"{lon},{lat},{alt}")
    xml = TPL.format(coords="\n        ".join(coords))
    with open(kml_out, "w") as f:
        f.write(xml)
    print(f"Wrote {len(coords)} vertices to {kml_out}")
