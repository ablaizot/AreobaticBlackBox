%% convert baro data

%TEMPORARY: run temporary Pixhawk barometer fix.  Delete once we have data
%from plane altimeter dial.  TODO: delete this
Temp_Fix_Barometer

clear baro_data;
last_time = 0;
output_index = 1;
for source_index = 1:length(BARO_0)
    if (BARO_0(source_index,2) ~= last_time)
        baro_data.time_us(output_index,1) = BARO_0(source_index,2);
        baro_data.height(output_index) = BARO_0(source_index,3);
        last_time = BARO_0(source_index,2);
        output_index = output_index + 1;
    end
end
save baro_data.mat baro_data;

%% extract IMU delta angles and velocity data
clear imu_data;
imu_data.time_us = IMU_0(:,2);
imu_data.gyro_dt = IMU_0(:,5);
imu_data.del_ang = IMU_0(:,6:8);
imu_data.accel_dt = IMU_0(:,4);
imu_data.del_vel = IMU_0(:,9:11);
save imu_data.mat imu_data;

%% convert magnetometer data
clear mag_data;
last_time = 0;
output_index = 1;
for source_index = 1:length(MAG_0)
    mag_timestamp = MAG_0(source_index,2);
    if (mag_timestamp ~= last_time)
        mag_data.time_us(output_index,1) = mag_timestamp;
        mag_data.field_ga(output_index,:) = 0.001*[MAG_0(source_index,3),MAG_0(source_index,4),MAG_0(source_index,5)];
        last_time = mag_timestamp;
        output_index = output_index + 1;
    end
end
save mag_data.mat mag_data;

%% save GPS daa
clear gps_data;

maxindex = min(length(GPS_0),length(GPA_0));

gps_data.time_us = GPS_0(1:maxindex,2);
gps_data.pos_error = GPA_0(1:maxindex,5);
gps_data.spd_error = GPA_0(1:maxindex,7);
gps_data.hgt_error = GPA_0(1:maxindex,6);

% set reference point used to set NED origin when GPS accuracy is sufficient
gps_data.start_index = max(find(gps_data.pos_error < 5.0, 1 ),find(gps_data.spd_error < 1.0, 1 ));
gps_data.refLLH = [GPS_0(gps_data.start_index,8);GPS_0(gps_data.start_index,9);GPS_0(gps_data.start_index,10)];

% convert GPS data to NED
deg2rad = pi/180;
for index = 1:1:maxindex
    if (GPS_0(index,4) >= 3)
        gps_data.pos_ned(index,:) = LLH2NED([GPS_0(index,9);GPS_0(index,10);GPS_0(index,11)],gps_data.refLLH);
        gps_data.vel_ned(index,:) = [GPS_0(index,12).*cos(deg2rad*GPS_0(index,13)),GPS_0(index,12).*sin(deg2rad*GPS_0(index,13)),GPS_0(index,14)];
    else
        gps_data.pos_ned(index,:) = [0,0,0];
        gps_data.vel_ned(index,:) = [0,0,0];
    end
end

save gps_data.mat gps_data;

%% save range finder data
% clear rng_data;
% if (exist('RFND','var'))
%     rng_data.time_us = RFND(:,2);
%     rng_data.dist = RFND(:,3);
%     save rng_data.mat rng_data;
% end

%% save optical flow data
% clear flow_data;
% if (exist('OF','var'))
%     flow_data.time_us = OF(:,2);
%     flow_data.qual = OF(:,3)/255; % scale quality from 0 to 1
%     flow_data.flowX = OF(:,4); % optical flow rate about the X body axis (rad/sec)
%     flow_data.flowY = OF(:,5); % optical flow rate about the Y body axis (rad/sec)
%     flow_data.bodyX = OF(:,6); % angular rate about the X body axis (rad/sec)
%     flow_data.bodyY = OF(:,7); % angular rate about the Y body axis (rad/sec)
%     save flow_data.mat flow_data;
% end

%% save visual odometry data
% clear viso_data;
% if (exist('VISO','var'))
%     viso_data.time_us = VISO(:,2);
%     viso_data.dt = VISO(:,3); % time period the measurement was sampled across (sec)
%     viso_data.dAngX = VISO(:,4); % delta angle about the X body axis (rad)
%     viso_data.dAngY = VISO(:,5); % delta angle about the Y body axis (rad)
%     viso_data.dAngZ = VISO(:,6); % delta angle about the Z body axis (rad)
%     viso_data.dPosX = VISO(:,7); % delta position along the X body axis (m)
%     viso_data.dPosY = VISO(:,8); % delta position along the Y body axis (m)
%     viso_data.dPosZ = VISO(:,9); % delta position along the Z body axis (m)
%     viso_data.qual = VISO(:,10)/100; % quality from 0 - 1
%     save viso_data.mat viso_data;
% end

%% save data and clear workspace
clearvars -except baro_data imu_data mag_data gps_data rng_data flow_data viso_data;


%% Save data to APM folder under TestData

targetFolder = 'C:\Users\ramph\Documents\Capstone MATLAB\EKF_replay\TestData\APM';

fullFilePath = fullfile(targetFolder, 'baro_data.mat');
save(fullFilePath, 'baro_data');

fullFilePath = fullfile(targetFolder, 'gps_data.mat');
save(fullFilePath, 'gps_data');

fullFilePath = fullfile(targetFolder, 'imu_data.mat');
save(fullFilePath, 'imu_data');

fullFilePath = fullfile(targetFolder, 'mag_data.mat');
save(fullFilePath, 'mag_data');



