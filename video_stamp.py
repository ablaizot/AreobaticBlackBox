import cv2
import time
from datetime import datetime
import os
import subprocess
import glob

#ffmpeg -framerate 60 -i Images/opencv%d.jpg -c:v mjpeg output.mjpeg

def parse_gngll(gngll_sentence):
    """Parse UTC time and coordinates from GNGLL sentence"""
    try:
        # Split the sentence and get the relevant parts
        parts = gngll_sentence.split(',')
        if len(parts) >= 6:
            time_str = parts[5]
            # Extract hours, minutes, seconds
            hours = int(time_str[0:2])
            minutes = int(time_str[2:4])
            seconds = int(time_str[4:6])
            gps_time = f"{hours}:{minutes}:{seconds}"
            
            # Extract latitude and longitude
            latitude = parts[1] + ' ' + parts[2]
            longitude = parts[3] + ' ' + parts[4]
            
            return gps_time, latitude, longitude
    except (IndexError, ValueError):
        return "Time Error", "Lat Error", "Lon Error"
    return "No Time", "No Lat", "No Lon"

def get_latest_gngll_sentence(directory):
    """Read the latest GNGLL sentence from a file"""
    list_of_files = glob.glob(os.path.join(directory, '*.log'))
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getmtime)
    latest_gngll = None
    with open(latest_file, 'r') as file:
        for line in file:
            if line.startswith('$GNGLL'):
                latest_gngll = line.strip()
    return latest_gngll

def record_video_segment(output_dir, filename, width, height, fps, duration_seconds):
    camera = cv2.VideoCapture(0, apiPreference=cv2.CAP_V4L2)
    if not camera.isOpened():
        print("Error: Could not open webcam.")
        return False

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec for AVI video
    video_writer = cv2.VideoWriter('output_stamped.mp4', fourcc, fps, (width, height))
    
    if not video_writer.isOpened():
        print("Error: video writer failed")
        return False
    
    frame_count = 0
    start_time = time.time()
    assert camera.isOpened()
    i = 0
    while (time.time() - start_time) < duration_seconds:
        ret, frame = camera.read()
        
        if not ret:
            print("Error: Could not read frame from webcam.")
            break

        # Get the latest GNGLL sentence from the file
        gngll_sentence = get_latest_gngll_sentence('gps_logs')
        gngll_sentence = False
        if gngll_sentence:
            gps_time, latitude, longitude = parse_gngll(gngll_sentence)
        else:
            gps_time, latitude, longitude = "No GPS Time", "No Lat", "No Lon"
        
        # Get current date from Raspberry Pi
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Combine date and GPS time
        timestamp = f"{current_date} {gps_time}"
        
        elapsed_time = int(time.time() - start_time)
        frame_text = f"Frame {i} {elapsed_time}/{duration_seconds} seconds"
        time_text = f"Time: {timestamp}"
        coord_text = f"Lat: {latitude} Lon: {longitude}"

        # Calculate FPS
        frame_count += 1
        fps_text = f"FPS: {frame_count / (time.time() - start_time):.2f}"
        
        # Add frame counter
        cv2.putText(frame, frame_text, (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        # Add timestamp
        cv2.putText(frame, time_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        # Add coordinates
        cv2.putText(frame, coord_text, (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Add FPS
        cv2.putText(frame, fps_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        # Display the frame
        #cv2.imshow('Recording in progress', frame)
        cv2.imwrite(f'Images/opencv{str(i)}.jpg', frame)
        i = i + 1
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    video_writer.release()
    cv2.destroyAllWindows()
    return True

output_directory = "Recordings"
os.makedirs(output_directory, exist_ok=True) # Create directory if it doesn't exist

recording_interval_seconds = 300 # 5 minutes
video_duration_seconds = 10 # 1 minute

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
video_filename = f"recording_{timestamp}.mp4"
subprocess.run(f"sudo usbreset 2560:c128", shell=True)
time.sleep(5)
success = record_video_segment(output_directory, video_filename, 1280, 720, 30, video_duration_seconds)
if not success:
    print("Warning: Video recording failed. Retrying...")
else:
    print("success")
