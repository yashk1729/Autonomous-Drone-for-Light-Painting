function plot_waypoints(wpFile)
%PLOT_WAYPOINTS Plot a QGC WPL 110 waypoint file in 3D (meters),
%excluding the final LAND waypoint.
%
%   plot_waypoints('pattern_test_01.waypoints')

    % Earth radius (same as Python script)
    R = 6378137.0;  % meters, WGS-84

    % Read table, skip the first header line "QGC WPL 110"
    T = readtable(wpFile, ...
        'FileType', 'text', ...
        'Delimiter', '\t', ...
        'HeaderLines', 1, ...
        'ReadVariableNames', false);

    % Use all rows except the last one (assumed LAND)
    n = height(T);
    rows = 1:n-1;

    % Columns in WPL:
    % 1:index  2:current  3:frame  4:command  5-8:params
    % 9:lat  10:lon  11:alt  12:autocontinue
    idx = T.Var1(rows);
    lat = T.Var9(rows);
    lon = T.Var10(rows);
    alt = T.Var11(rows);

    % Convert lat/lon to local ENU in meters around first point
    lat0 = deg2rad(lat(1));
    lon0 = deg2rad(lon(1));

    dlat = deg2rad(lat) - lat0;
    dlon = deg2rad(lon) - lon0;

    north_m = R * dlat;
    east_m  = R * cos(lat0) .* dlon;
    up_m    = alt;   % already meters

    x = east_m;
    y = north_m;
    z = up_m;

    figure;
    plot3(x, y, z, '-o', 'LineWidth', 1.5);
    grid on;
    axis equal;  % same scale for X,Y,Z (all in meters)
    xlabel('East (m)');
    ylabel('North (m)');
    zlabel('Altitude (m)');
    title(sprintf('Waypoints from %s (without LAND)', wpFile), 'Interpreter', 'none');
    hold on;

    % Add waypoint numbers
    for k = 1:numel(idx)
        text(x(k), y(k), z(k), sprintf('%d', idx(k)), ...
            'VerticalAlignment', 'bottom', ...
            'HorizontalAlignment', 'center');
    end

    hold off;
end
