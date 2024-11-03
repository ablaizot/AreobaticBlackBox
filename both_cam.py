import subprocess
import os
from multiprocess import Process

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

def main():
    p1 = Process(target=see_cam)
    p2 = Process(target=web_cam)
    p1.start()
    p2.start()

if __name__ == '__main__':
    main()