#!/bin/bash
sudo systemctl enable stamp_video.service
sudo systemctl enable mavproxy.service
sudo systemctl enable gps_logger.service
sudo systemctl start stamp_video.service
sudo systemctl start mavproxy.service
sudo systemctl start gps_logger.service
sudo systemctl status stamp_video.service
sudo systemctl status mavproxy.service
sudo systemctl status gps_logger.service