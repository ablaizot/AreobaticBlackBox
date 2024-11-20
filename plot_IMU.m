function plot_IMU(IMU_0 )
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
figure
time_IMU = IMU_0(:,2) / 1e6;
plot(time_IMU,IMU_0(:,7),time_IMU,IMU_0(:,8),time_IMU,IMU_0(:,9) )
xlabel("Time (s)")
ylabel("Acceleration (m/s)")
legend('x', 'y', 'z')
title("Acceleration")

figure
time_IMU = IMU_0(:,2) / 1e6;
plot(time_IMU,IMU_0(:,4),time_IMU,IMU_0(:,5),time_IMU,IMU_0(:,6) )
xlabel("Time (s)")
ylabel("Rotation rate rad/s")
legend('x', 'y', 'z')
title("Gyroscope")


end 