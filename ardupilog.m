load("11_8_24\00000011.log-9169881.mat")
disp("https://ardupilot.org/plane/docs/logmessages.html")
gps_status(GPS_0, GPA_0)
plot_altitudes(GPS_0,BARO_0, BARO_1)
plot_gps(GPS_0)


load("11_8_24\00000008.BIN-13546824.mat")
gps_status(GPS_0, GPA_0)
plot_altitudes(GPS_0,BARO_0, BARO_1)

figure
lat = POS(:,3);
lon = POS(:,4);

geoscatter(lat,lon,"filled")
geolimits([min(lat) max(lat)],[min(lon) max(lon)])
