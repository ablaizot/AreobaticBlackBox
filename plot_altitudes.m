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
legend('GPS','BARO 0', 'BARO 1',Location='southwest')
% xline(2069751136.00000/1e6,'-','Take off', 'HandleVisibility','off')
% xline(2363711114.00000/1e6,'-','Landing','HandleVisibility','off')

figure
plot(time_BARO_0, BARO_0(:,5), time_BARO_1, BARO_1(:,5))
title("Atmospheric Pressure")
xlabel("Time (s)")
ylabel("Pressure (Pa 1e5 Pa = 14.7 Psi)")
legend('BARO 0', 'BARO 1',Location='southwest')
% xline(2069751136.00000/1e6,'-','Take off','HandleVisibility','off')
% xline(2363711114.00000/1e6,'-','Landing','HandleVisibility','off')

figure
plot(time_BARO_0, BARO_0(:,6), time_BARO_1, BARO_1(:,6))
title("Barometric Temperature")
xlabel("Time (s)")
ylabel("Temperature (C)")
legend('BARO 0', 'BARO 1',Location='southwest')
% xline(2069751136.00000/1e6,'-','Take off','HandleVisibility','off')
% xline(2363711114.00000/1e6,'-','Landing','HandleVisibility','off')

figure
base_pressure = BARO_0(1,5);
altitude_0 = 153.8462 .* (BARO_0(:,6)+273.15).* (1.0 - exp(0.190259.* log(BARO_0(:,5)/base_pressure)));
altitude_1 = 153.8462 .* (BARO_1(:,6)+273.15) .* (1.0 - exp(0.190259.* log(BARO_1(:,5)/base_pressure)));

plot(GPS_0(:,2)/1e6,GPS_0(:,11), time_BARO_0, altitude_0, time_BARO_1, altitude_1)
title("Altitudes")
xlabel("Time (s)")
ylabel("Altitude (m)")
legend('GPS','BARO 0', 'BARO 1',Location='southwest')
% xline(2069751136.00000/1e6,'-','Take off', 'HandleVisibility','off')
% xline(2363711114.00000/1e6,'-','Landing','HandleVisibility','off')
end