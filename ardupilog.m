load("4_19_25_data\flight_2\00000075.log-28536934.mat")
disp("https://ardupilot.org/plane/docs/logmessages.html")
close all
gps_status(GPS_0, GPA_0)
plot_altitudes(GPS_0,BARO_0, BARO_1)
plot_gps(GPS_0)
takeoff_F1 = 2069751136.00000;
figure
lat = POS(:,3);
lon = POS(:,4); 
plot_AHRS(AHR2)
plot_IMU(IMU_0)
plot_IMU(IMU_1)
plot_IMU(IMU_2)


% geoscatter(lat,lon,"filled")
% geolimits([min(lat) max(lat)],[min(lon) max(lon)])
% 
% 
% figure
% lat = POS(:,3);
% lon = POS(:,4);
% 
% geoscatter(lat,lon,"filled")
% geolimits([min(lat) max(lat)],[min(lon) max(lon)])
% 
% plot_IMU(IMU_0)
% plot_IMU(IMU_1)
% plot_IMU(IMU_2)
% 
% 
% plot_gps(GPS_0)
% 
% %load("11_17_24\00000006.BIN-3426423.mat")

