import subprocess
import os
import signal
import sys
from multiprocess import Process
import datetime
import time
from video_stamp import stamp_video
from ram_to_sd_transfer import RamDiskTransfer

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
    # First, kill any existing mavproxy processes
    print("Checking for existing mavproxy processes...")
    try:
        # Find and kill any existing mavproxy processes
        subprocess.run("pkill -f mavproxy.py", shell=True)
        print("Terminated existing mavproxy processes")
        # Small delay to ensure processes are fully terminated
        time.sleep(1)
    except Exception as e:
        print(f"Note: Error when trying to kill existing mavproxy processes: {e}")
    
    folder_name = increment_filename("mav_logs")
    
    # Get the remote IP address from SSH_CONNECTION
    ssh_connection = os.getenv("SSH_CONNECTION", "")
    if ssh_connection:
        # SSH_CONNECTION format: "<client_ip> <client_port> <server_ip> <server_port>"
        remote_ip = ssh_connection.split()[0]  # Get first element (client IP)
        print(f"Detected remote IP: {remote_ip}")
        # save to file
        with open("remote_ip.txt", "w") as f:
            f.write(remote_ip)
    else:
        # Fallback to a ip in remote_ip.txt if SSH_CONNECTION is not available
        try:
            with open("remote_ip.txt", "r") as f:
                remote_ip = f.read().strip()
                print(f"Using IP from remote_ip.txt: {remote_ip}")
        except FileNotFoundError:
            # Fallback to a default IP if remote_ip.txt is not available
            remote_ip = "127.0.0.1"
            print(f"SSH_CONNECTION not found, using default IP: {remote_ip}")

    subprocess.run(f"mkdir -p {folder_name}", shell=True)
    output_file = increment_filename(f"{folder_name}/mavproxy.log")
    mission = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    mavproxy_cmd = f"mavproxy.py --out {remote_ip}:14550 --non-interactive --baudrate=912000 --mission={mission} --state-basedir={folder_name} > {output_file} &"
    print(mavproxy_cmd)
    subprocess.run(mavproxy_cmd, shell=True)

def gps_logger():
    """Log GPS data to a file"""
    # Create the logs directory if it doesn't exist
    os.makedirs("gps_logs", exist_ok=True)
    
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
        
        # Test GPS device for NMEA sentences
        print(f"Testing GPS on {device}...")
        try:
            # Use preexec_fn to create a new process group
            gps_test_cmd = f"cat {device} > gps_test.log"
            print(gps_test_cmd)
            out = subprocess.Popen(gps_test_cmd, shell=True, 
                                   stdin=subprocess.PIPE,
                                   preexec_fn=os.setsid)
            time.sleep(1)  # Wait to collect some data
            
            try:
                # Try to terminate process group
                os.killpg(os.getpgid(out.pid), signal.SIGTERM)
                print("Test process terminated")
            except (ProcessLookupError, OSError) as e:
                print(f"Note: Process already terminated: {e}")
            
            # Check test output
            if os.path.exists("gps_test.log"):
                with open("gps_test.log", 'r') as f:
                    gps_test_output = f.read()
                    if not gps_test_output:
                        print("GPS test output is empty, trying other GPS port")
                        device = "/dev/ttyACM0"
                        if not os.path.exists(device):
                            print("No working GPS device found")
                            return
                    
                    # Check for valid NMEA sentences
                    if "GNGGA" not in gps_test_output and "GNRMC" not in gps_test_output:
                        print("GPS test output does not contain valid NMEA sentences")
                        device = "/dev/ttyACM0"
                        if not os.path.exists(device):
                            print("No working GPS device found")
                            return
            else:
                print("GPS test log not created, using default device")
        
        except Exception as e:
            print(f"GPS test failed: {e}")
            device = "/dev/ttyACM0"
            # Continue anyway - the device exists, we'll try to use it
        
        # Start actual GPS logging
        print(f"Starting GPS logger with device {device}")
        gps_logger_cmd = f"mkdir -p gps_logs && nohup cat {device} > {output_file} &"
        print(gps_logger_cmd)
        subprocess.run(gps_logger_cmd, shell=True)
        print(f"GPS logger started, writing to {output_file}")
        
    except (PermissionError, IOError) as e:
        print(f"Error accessing GPS device: {e}")

def ram_to_sd_transfer():
    """Transfer files from RAM disk to SD card in the background"""
    # Configure RAM disk path based on system

    ramdisk_path = "/mnt/ramdisk"
    
    print(f"Starting RAM disk to SD card transfer process using {ramdisk_path}")
    
    # Create and start the transfer process
    transfer = RamDiskTransfer(
        ramdisk_base=ramdisk_path,
        sd_base="Images",
        max_files_per_batch=50,
        sleep_interval=1
    )
    
    # Start the transfer process (this will run until the process is terminated)
    transfer.start()

def main():
    p1 = Process(target=stamp_video)
    p3 = Process(target=mavproxy)
    p4 = Process(target=gps_logger)
    p5 = Process(target=ram_to_sd_transfer)
    
    p1.start()
    p3.start()
    p4.start()
    p5.start()
    
    # Wait for all processes to finish
    p1.join()
    p3.join()
    p4.join()

if __name__ == '__main__':
    main()