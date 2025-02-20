import cv2
import time
from datetime import datetime
import os

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

    start_time = time.time()
    assert camera.isOpened()
    i = 0
    while (time.time() - start_time) < duration_seconds:
        ret, frame = camera.read()
        
        if not ret:
            print("Error: Could not read frame from webcam.")
            break
        elapsed_time = int(time.time() - start_time)
        text = f"Frame {i} {elapsed_time}/{duration_seconds} seconds"
        cv2.putText(frame, text, (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        #video_writer.write(frame)
        cv2.imshow('Recording in progress', frame)
        cv2.imwrite('Images/opencv'+str(i)+'.jpg', frame)
        i= i+1
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
success = record_video_segment(output_directory, video_filename, 640, 480, 30, video_duration_seconds)
if not success:
    print("Warning: Video recording failed. Retrying...")
