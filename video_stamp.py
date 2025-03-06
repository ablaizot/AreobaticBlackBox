from __future__ import print_function
import cv2
import time
from datetime import datetime
import os
import subprocess
import glob
from multiprocessing.pool import ThreadPool
from collections import deque
from queue import Queue
from threading import Thread

class VideoProcessor:
    def __init__(self, width=1280, height=720, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_count = 0
        self.start_time = time.time()

    def process_frame(self, frame, t0):
        """Process a single frame with GPS and timestamp overlay"""
        # Get the latest GNGLL sentence from the file
        gngll_sentence = self.get_latest_gngll_sentence('gps_logs')
        gps_time = ''
        latitude = ''
        longitude = ''
        if gngll_sentence:
            gps_time, latitude, longitude = self.parse_gngll(gngll_sentence)
        else:
            latitude, longitude = "No Lat", "No Lon"
        
        # Get current date and combine with GPS time
        current_date = datetime.now().strftime("%Y-%m-%d")
        if not gps_time:
            gps_time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
        timestamp = f"{current_date} {gps_time}"
        
        # Calculate display metrics
        self.frame_count += 1
        elapsed_time = int(time.time() - self.start_time)
        
        # Add text overlays
        texts = [
            (f"Frame {self.frame_count}", (10, 15), (0, 0, 255)),
            (f"Time: {timestamp}", (10, 40), (0, 255, 0)),
            (f"Lat: {latitude} Lon: {longitude}", (10, 65), (255, 0, 0)),
            (f"FPS: {self.frame_count / (time.time() - self.start_time):.2f}", (10, 90), (255, 255, 0))
        ]
        print(f"Frame {self.frame_count} processed in {time.time() - t0:.2f} seconds")
        #print gps_time, latitude, longitude
        print(f"Time: {timestamp}")
        print(f"Lat: {latitude} Lon: {longitude}")
        #print FPS
        print(f"FPS: {self.frame_count / (time.time() - self.start_time):.2f}")

        
        for text, pos, color in texts:
            cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame, t0

    @staticmethod
    def parse_gngll(gngll_sentence):
        """Parse UTC time and coordinates from GNGLL sentence"""
        try:
            parts = gngll_sentence.split(',')
            if len(parts) >= 6:
                time_str = parts[5]
                hours = int(time_str[0:2])
                minutes = int(time_str[2:4])
                seconds = int(time_str[4:6])
                gps_time = f"{hours}:{minutes}:{seconds}"
                latitude = parts[1] + ' ' + parts[2]
                longitude = parts[3] + ' ' + parts[4]
                return gps_time, latitude, longitude
        except (IndexError, ValueError):
            return "Time Error", "Lat Error", "Lon Error"
        return "No Time", "No Lat", "No Lon"

    @staticmethod
    def get_latest_gngll_sentence(directory):
        """Read the latest GNGLL sentence from a file"""
        list_of_files = glob.glob(os.path.join(directory, '*.log'))
        if not list_of_files:
            return None
        latest_file = max(list_of_files, key=os.path.getmtime)
        latest_gngll = None
        print(f"Reading from {latest_file}")
        with open(latest_file, 'r') as file:
            for line in file:
                if line.startswith('$GNGLL'):
                    latest_gngll = line.strip()
        print(f"Latest GNGLL: {latest_gngll}")
        return latest_gngll

class AsyncFrameWriter:
    def __init__(self, output_dir="Images", num_workers=4):
        self.output_dir = output_dir
        self.queue = Queue()
        self.workers = []
        
        # Create worker threads
        for _ in range(num_workers):
            worker = Thread(target=self._worker_thread, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def _worker_thread(self):
        while True:
            frame_data = self.queue.get()
            if frame_data is None:
                break
            frame, idx = frame_data
            cv2.imwrite(f'{self.output_dir}/opencv{str(idx)}.jpg', frame)
            print(f"Queue size {self.queue.qsize()}\n" )
            self.queue.task_done()
    
    def write_frame(self, frame, idx):
        self.queue.put((frame, idx))
    
    def stop(self):
        # Send stop signal to all workers
        for _ in self.workers:
            self.queue.put(None)
        # Wait for all workers to finish
        for worker in self.workers:
            worker.join()

def stamp_video(display=False):
    # Initialize video captures
    camera0 = cv2.VideoCapture(0, apiPreference=cv2.CAP_V4L2)
    camera1 = cv2.VideoCapture(2, apiPreference=cv2.CAP_V4L2)
    
    if not camera0.isOpened() or not camera1.isOpened():
        print("Error: Could not open one or both webcams.")
        return

    # Set up video parameters
    W, H = 1920, 1080
    processor0 = VideoProcessor(W, H, 120)
    processor1 = VideoProcessor(W, H, 30)

    # Configure both cameras
    for camera in [camera0, camera1]:
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, W)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
        camera.set(cv2.CAP_PROP_FPS, 120)
        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    
    # Initialize threading
    threadn = cv2.getNumberOfCPUs()
    pool = ThreadPool(processes=threadn)
    pending0 = deque()
    pending1 = deque()
    
    # Create output directories
    os.makedirs("Images/cam0", exist_ok=True)
    os.makedirs("Images/cam1", exist_ok=True)
    
    # Clear images in the directories
    for dir in ['Images/cam0/*', 'Images/cam1/*']:
        files = glob.glob(dir)
        for f in files: 
            os.remove(f)
    
    # Initialize async frame writers
    frame_writer0 = AsyncFrameWriter(output_dir="Images/cam0")
    frame_writer1 = AsyncFrameWriter(output_dir="Images/cam1")

    
    
    frame_idx = 0
    try:
        while True:
            # Process frames in parallel for both cameras
            if len(pending0) < threadn:
                ret0, frame0 = camera0.read()
                ret1, frame1 = camera1.read()
                if not ret0 or not ret1:
                    break
                
                task0 = pool.apply_async(processor0.process_frame, (frame0.copy(), time.time()))
                task1 = pool.apply_async(processor1.process_frame, (frame1.copy(), time.time()))
                pending0.append(task0)
                pending1.append(task1)

            # Get processed frames from both cameras
            while pending0 and pending0[0].ready() and pending1 and pending1[0].ready():
                processed_frame0, _ = pending0.popleft().get()
                processed_frame1, _ = pending1.popleft().get()
                
                try:
                    if display:
                        cv2.imshow('camera0', processed_frame0)
                        cv2.imshow('camera1', processed_frame1)
                except cv2.error as e:
                    display = False
                    print(f"Error displaying frames: {e}")

                
                frame_writer0.write_frame(processed_frame0, frame_idx)
                frame_writer1.write_frame(processed_frame1, frame_idx)
                frame_idx += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if frame_idx >= 1000:
                break

    finally:
        # Clean up
        camera0.release()
        camera1.release()
        cv2.destroyAllWindows()
        frame_writer0.stop()
        frame_writer1.stop()
        
        # Convert frames to video using ffmpeg for both cameras
        for cam_id in [0, 1]:
            subprocess.run([
                'ffmpeg', '-y', '-framerate', str(processor0.fps),
                '-i', f'Images/cam{cam_id}/opencv%d.jpg',
                '-c:v', 'avi',
                f'output_cam{cam_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.avi'
            ])

