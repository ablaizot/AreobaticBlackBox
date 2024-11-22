%% Using this to check if GPS values qualify parameter defaults

%From parameter defaults:
gpsSpdErrLim = 2.5; %GPS use will not start if reported GPS speed error is greater than this (m/s)
gpsPosErrLim = 5.0; %GPS use will not start if reported GPS position error is greater than this (m)

%Check if values qualify
Speed_used = gps_data.spd_error <= gpsSpdErrLim;
Postion_used = gps_data.pos_error <= gpsPosErrLim;
GPS_ON = Speed_used.*Postion_used; %And by element-wise multiplication

%See what fraction of values qualify
Speed_percent = 100*mean(Speed_used)
Pos_percent = 100*mean(Postion_used)
Total_percent = 100*mean(GPS_ON)

%PROBLEM: Currently 91% of GPS values qualify position, but <5% qualify on
%speed.  In total only 4.5% of GPS points are used.

%% Plotting GPS data
