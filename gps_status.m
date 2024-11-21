function gps_status(GPS_0, GPA_0)
%gps_status Plot diagnostics of GPS
%   Detailed explanation goes here
figure
tiledlayout(6,1)

ax1 = nexttile;
time_GPS = GPS_0(:,2) / 1e6;
plot(time_GPS,GPS_0(:,4))
title(ax1, "GPS INFO")
xlabel("Time (s)")
ylabel("GPS Status")

nexttile
plot(time_GPS,GPS_0(:,7))
xlabel("Time (s)")
ylabel("Number of Satellites")

time_GPA = GPA_0(:,2) / 1e6;

nexttile
plot(diff(GPS_0(:,2)/1e6))

nexttile

plot(time_GPA, GPA_0(:,5))
xlabel("Time (s)")
ylabel("Horizontal Accuracy (m)")

nexttile
plot(time_GPA, GPA_0(:,6))
xlabel("Time (s)")
ylabel("Vertical Accuracy (m)")

nexttile
plot(time_GPA, GPA_0(:,7))
xlabel("Time (s)")
ylabel("Speed Accuracy (m/s)");
end