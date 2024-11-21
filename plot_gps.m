function plot_gps(GPS_0)
%gps_status Plot diagnostics of GPS
%   Detailed explanation goes here
figure
tiledlayout(6,1)

ax1 = nexttile;
time_GPS = GPS_0(:,2) / 1e6;
plot(time_GPS,GPS_0(:,11))
title(ax1, "GPS Data")
xlabel("Time (s)")
ylabel("Altitude (m)")

nexttile
plot(diff(GPS_0(:,2)/1e6))

nexttile
plot(time_GPS,GPS_0(:,12))
xlabel("Time (s)")
ylabel("Ground Speed (m/s)")

nexttile
plot(time_GPS, GPS_0(:,14))
xlabel("Time (s)")
ylabel("Vertical Speed (m/s)") 

nexttile
plot(time_GPS, GPS_0(:,13))
xlabel("Time (s)")
ylabel("Ground Course (deg heading)")

nexttile
plot(time_GPS, GPS_0(:,15))
xlabel("Time (s)")
ylabel("Yaw (deg)")

figure
lat = nonzeros(GPS_0(:,9));
lon = nonzeros(GPS_0(:,10));

geoscatter(lat,lon,"filled")
geolimits([min(lat) max(lat)],[min(lon) max(lon)])
 

end