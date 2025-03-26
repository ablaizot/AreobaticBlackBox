import subprocess
import os
from multiprocess import Process
import datetime
from video_stamp import stamp_video

def increment_filename(filepath):
    base, ext = os.path.splitext(filepath)
    counter = 1
    new_filepath = filepath
    while os.path.exists(new_filepath):
        new_filepath = f"{base}_{counter}{ext}"
        counter += 1
    return new_filepath

def see_cam():
    output_file = increment_filename("Videos/see_cam.mjpeg")
    see_cam_cmd = f"sudo v4l2-ctl --device /dev/video0 --stream-mmap --stream-to={output_file} --stream-count=1000000 --set-fmt-video=width=1920,height=1080,pixelformat=MJPG --set-parm 30"
    print(see_cam_cmd)
    subprocess.run(see_cam_cmd, shell=True)

def web_cam():
    output_file = increment_filename("Videos/web_cam.mjpeg")
    web_cam_cmd = f"sudo v4l2-ctl --device /dev/video2 --stream-mmap --stream-to={output_file} --stream-count=1000000 --set-fmt-video=width=1920,height=1080,pixelformat=MJPG --set-parm 30"

    print(web_cam_cmd)
    subprocess.run(web_cam_cmd, shell=True)

def mavproxy():
    folder_name = increment_filename("mav_logs")
    subprocess.run(f"mkdir {folder_name}", shell=True)
    output_file = increment_filename(f"{folder_name}/mavproxy.log")
    mission = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    mavproxy_cmd = f"nohup mavproxy.py --non-interactive --baudrate=912000 --mission={mission} --state-basedir={folder_name} > {output_file} &"
    print(mavproxy_cmd)
    subprocess.run(mavproxy_cmd, shell=True)

def gps_logger():
    # Try ttyACM1 first
    output_file = increment_filename("gps_logs/gps.log")
    device = "/dev/ttyACM1"
    
    # Check if ttyACM1 exists and is readable
    if not os.path.exists(device):
        print(f"{device} not found, trying ttyACM0")
        device = "/dev/ttyACM0"
        
    if not os.path.exists(device):
        print("No GPS device found")
        return
    
    
    try:
        # Try to open the device to verify it's accessible
        with open(device, 'r') as f:
            print(f"GPS device found at {device}")
        gps_test_cmd = f"cat {device}"
        print(gps_test_cmd)
        out = subprocess.run(gps_test_cmd, shell=True)

        #check if out is empty
        if out.stdout == None:
            device = "/dev/ttyACM0"
        
        gps_logger_cmd = f"nohup cat {device} > {output_file} &"
        print(gps_logger_cmd)
        subprocess.run(gps_logger_cmd, shell=True)
        
    except (PermissionError, IOError) as e:
        print(f"Error accessing GPS device: {e}")

def main():
    p1 = Process(target=stamp_video)
    p3 = Process(target=mavproxy)
    p4 = Process(target=gps_logger)

    p1.start()
    p3.start()
    p4.start()

if __name__ == '__main__':
    main()