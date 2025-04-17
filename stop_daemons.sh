#!/bin/bash
sudo systemctl stop stamp_video.service
sudo systemctl stop mavproxy.service
sudo systemctl stop gps_logger.service
sudo systemctl status stamp_video.service
sudo systemctl status mavproxy.service
sudo systemctl status gps_logger.service