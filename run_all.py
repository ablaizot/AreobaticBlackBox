import subprocess
import os
import signal
import sys
from multiprocess import Process
import datetime
import time
from video_stamp import stamp_video
from flask import Flask, render_template_string, send_file
import socket
import glob
import threading

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
    if (ssh_connection):
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

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket and connect to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return "127.0.0.1"  # Fallback to localhost

def image_server():
    """
    Start a Flask web server that displays the latest images from both cameras
    """
    app = Flask(__name__)
    
    # Define the HTML template
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Camera Feeds</title>
        <meta http-equiv="refresh" content="1">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .camera-feed {
                background-color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            h1, h2 {
                color: #333;
            }
            img {
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .timestamp {
                color: #666;
                margin-top: 5px;
                font-size: 0.8rem;
            }
            .image-wrapper {
                position: relative;
            }
            .loading {
                display: none;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: white;
                background-color: rgba(0,0,0,0.7);
                padding: 10px;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <h1>Camera Feeds</h1>
        <div class="container">
            <div class="camera-feed">
                <h2>Camera 0 (Latest Image)</h2>
                <div class="image-wrapper">
                    <img src="/camera0_latest?timestamp={{ timestamp }}" alt="Camera 0">
                    <div class="loading">Loading...</div>
                </div>
                <div class="timestamp">Last updated: {{ timestamp }}</div>
            </div>
            <div class="camera-feed">
                <h2>Camera 1 (Latest Image)</h2>
                <div class="image-wrapper">
                    <img src="/camera1_latest?timestamp={{ timestamp }}" alt="Camera 1">
                    <div class="loading">Loading...</div>
                </div>
                <div class="timestamp">Last updated: {{ timestamp }}</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    @app.route('/')
    def index():
        """Serve the main page with both camera feeds"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return render_template_string(HTML_TEMPLATE, timestamp=timestamp)
    
    @app.route('/camera0_latest')
    def camera0_latest():
        """Serve the latest image from camera 0"""
        try:
            # Find the latest image directory for camera 0
            dirs = sorted(glob.glob("Images/cam0_*"), key=os.path.getmtime, reverse=True)
            if not dirs:
                return "No camera 0 images available", 404
                
            # Find the latest image file in that directory
            latest_dir = dirs[0]
            files = sorted(glob.glob(f"{latest_dir}/*.jpg"), key=os.path.getmtime, reverse=True)
            if not files:
                return "No images in the latest directory", 404
                
            # Return the latest image
            return send_file(files[0], mimetype='image/jpeg')
        except Exception as e:
            print(f"Error serving camera 0 image: {e}")
            return str(e), 500
    
    @app.route('/camera1_latest')
    def camera1_latest():
        """Serve the latest image from camera 1"""
        try:
            # Find the latest image directory for camera 1
            dirs = sorted(glob.glob("Images/cam1_*"), key=os.path.getmtime, reverse=True)
            if not dirs:
                return "No camera 1 images available", 404
                
            # Find the latest image file in that directory
            latest_dir = dirs[0]
            files = sorted(glob.glob(f"{latest_dir}/*.jpg"), key=os.path.getmtime, reverse=True)
            if not files:
                return "No images in the latest directory", 404
                
            # Return the latest image
            return send_file(files[0], mimetype='image/jpeg')
        except Exception as e:
            print(f"Error serving camera 1 image: {e}")
            return str(e), 500
    
    # Get the local IP address
    local_ip = get_local_ip()
    port = 5000
    
    print(f"Starting image server at http://{local_ip}:{port}/")
    print(f"Access this URL from any device on your local network")
    
    # Start Flask in a thread-safe way - use threading mode for compatibility
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


def main():
    p1 = Process(target=stamp_video)
    p2 = Process(target=image_server)  # Add the image server process
    p3 = Process(target=mavproxy)
    #p4 = Process(target=gps_logger)

    p1.start()
    p2.start()  # Start the image server
    p3.start()
    #p4.start()

    print("All processes started. Press Ctrl+C to stop.")
    
    try:
        # Keep the main process running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping all processes...")
        # Add cleanup code here if needed

if __name__ == '__main__':
    main()