import subprocess
import os
from multiprocess import Process
import datetime

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
    output_file = increment_filename("gps_logs/gps.log")
    gps_logger_cmd = f"nohup cat /dev/ttyACM1 > {output_file} &"
    print(gps_logger_cmd)
    subprocess.run(gps_logger_cmd, shell=True)

def main():
    p1 = Process(target=see_cam)
    p2 = Process(target=web_cam)
    p3 = Process(target=mavproxy)
    p4 = Process(target=gps_logger)

    p1.start()
    p2.start()
    p3.start()
    p4.start()

if __name__ == '__main__':
    main()