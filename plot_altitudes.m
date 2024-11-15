function  plot_altitudes(GPS_0,BARO_0, BARO_1)
%UNTITLED5 Summary of this function goes here
%   Detailed explanation goes here
time_BARO_0 = BARO_0(:,2)/1e6;
time_BARO_1 = BARO_1(:,2)/1e6;
figure
plot(GPS_0(:,2)/1e6,GPS_0(:,11), time_BARO_0, BARO_0(:,4), time_BARO_1, BARO_1(:,4))
title("Altitudes")
xlabel("Time (s)")
ylabel("Altitude (m)")
legend('GPS','BARO 0', 'BARO 1')
end