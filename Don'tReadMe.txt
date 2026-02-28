1. PC scripts goes in PC and Pi scripts goes in Pi. (duh)
2. Install Mission Planner, Inkscape, Matlab in pc.
3. Install Mavlink in Pi and make it as startup to establish connection as soon as drone is online.
4. make sure to Transfer .json files into pi before generating a new .waypoint files with .svg drawings.
5. you will need a lot of libraries to get mavlink data into pi scrips.
6. Feel free to add new colors in led25.py

List of helpful commands:

SVG to waypts and LED cmd files : python svg_to_basic_wpl.py q.svg mission_config.json q.waypoints

Visualize 3D MATLAB : plot_waypoints('1.waypoints')

To transfer files via SSH: scp M1.led.json user@raspberrypi:/home/

To run the main LED script : python3 /home/mission_led_runtime.py

Goodluck..:)
