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
ylabel("# of Satellites")

time_GPA = GPA_0(:,2) / 1e6;

nexttile
time_diff = diff(GPS_0(:,2)) ./ 1e6;
x = 2:length(GPS_0);
x2 = GPS_0(x,2) ./ 1e6;
plot(diff(GPS_0(:,2)/1e6))
xlabel("Time (s)")
ylabel("Time of Delay (s)")

nexttile

plot(time_GPA, GPA_0(:,5))
xlabel("Time (s)")
ylabel("H-Accuracy (m)")

nexttile
plot(time_GPA, GPA_0(:,6))
xlabel("Time (s)")
ylabel("V-Accuracy (m)")

nexttile
plot(time_GPA, GPA_0(:,7))
xlabel("Time (s)")
ylabel("Speed Accuracy (m/s)");
end