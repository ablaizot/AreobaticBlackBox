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
time_diff = diff(GPS_0(:,2)) ./ 1e6;
x = 2:length(GPS_0);
x2 = GPS_0(x,2) ./ 1e6;
plot(diff(GPS_0(:,2)/1e6))
xlabel("Time of the Delay (s)")
ylabel("Logged Time Delay (s)")

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
%lat = nonzeros(GPS_0(:,9));
%lon = nonzeros(GPS_0(:,10));
lat = GPS_0(:,9);
lon = GPS_0(:,10);
time_normalized = (GPS_0(:,2) - min(GPS_0(:,2)))/(max(GPS_0(:,2)) - min(GPS_0(:,2)));

geoscatter(lat,lon,20, time_normalized, "filled")
geolimits([min(lat) max(lat)],[min(lon) max(lon)])
colorbar('Ticks',[0,1],...
         'TickLabels',{'Start','End'});
colormap('jet');
 

end