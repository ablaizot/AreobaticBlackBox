# Instructions

There are two main components to start. After clonining the repo, make sure you run the commands from the top directory of the repo.

## Cameras
The python script both_cam.py starts two UVC cameras and records the output in the Videos folder. They are both recording at 1920x1080 30 fps. The script increments the filename for every new recording.

Start the cameras with:
```
nohup python3 both_cam.py &
```

## Pixhawk and GPS

The mavproxy program is responsible for handling the pixhawk. I followed https://ardupilot.org/mavproxy/docs/getting_started/download_and_installation.html to install it.

Start mavproxy with:

```
nohup mavproxy.py > mav.log &
```


