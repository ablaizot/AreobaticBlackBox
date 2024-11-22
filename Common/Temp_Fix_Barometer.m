%% Temporary code to fix Pixhawk barometer readings
% Barometer altitude readings from the pixhawk are not very accurate as the
% cabin pressure of the aircraft varies with airspeed.  But they're better
% than nothing (matched GPS altitude pretty well), and we need something to
% test the filter with until data from the plane's altimiter is available.
% Currently the logs are bugged and just read 0 altitude, this calculates
% an approximate value from pressure.

%Working with BARO_0
%Columns are Time since log start, time since system start, sensor number
%(0), calculated altitude, altitue above mean sea level?, measured
%pressure, and measured temperature

%From pressure and temp we calculate and fill in the altitude
%Equation from other work in our Github plot_altitudes.m
base_pressure = mean(BARO_0(1:20, 5));
altitude_0 = 153.8462 .* (BARO_0(:,6)+273.15).* (1.0 - exp(0.190259.* log(BARO_0(:,5)/base_pressure)));

%Return into loaded BARO_0
BARO_0(:,3) = altitude_0;