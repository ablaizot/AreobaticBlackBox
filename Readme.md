# Instructions

There are two main components to start. After clonining the repo, make sure you run the commands from the top directory of the repo. The name of the folder is AreobaticBlackBox.

Connect the Red to 5V. Green to GND. Brown to TX. Orange to RX.

Connect to the raspberry pi with 

```
ssh coolhippo159@hostname
```

Start all of the processes with:
```
nohup python3 run_all.py &
```

Make sure the process is running by going to the gps_logs folder and opening the log with the largest number. Additionally, go the mav_logs folder and make sure the tlog size is increasing by running ls -lh multiple times. 

## Cameras
The python script run_all.py starts two UVC cameras and records the output in the Videos folder. They are both recording at 1920x1080 30 fps. The script increments the filename for every new recording.

## Pixhawk and GPS

The mavproxy program is responsible for handling the pixhawk. I followed https://ardupilot.org/mavproxy/docs/getting_started/download_and_installation.html to install it.

Start mavproxy with:

```
nohup mavproxy.py --non-interactive --baudrate=912000 > mavproxy.log & 
```

Listen to the GPS to Raspberry Pi

```
nohup cat /dev/ttyACM1 > gps.log &
```

We referenced this guide https://oscarliang.com/gps-settings-u-center/ on configuring the GPS.
The Pixhawk logs are saved in D:\APM\LOGS in the pixhawk sd card. The file cubeblack.param contains the parameters for the Pixhawk.

## Reviewing data


Go to the DataFlash log in Mission planner and download DataFlash log via Mavlink. This will give you a tlog from which you can get a .mat file or play back the log.