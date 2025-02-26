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
        if gngll_sentence:
            gps_time, latitude, longitude = self.parse_gngll(gngll_sentence)
        else:
            gps_time, latitude, longitude = "No GPS Time", "No Lat", "No Lon"
        
        # Get current date and combine with GPS time
        current_date = datetime.now().strftime("%Y-%m-%d")
        if gps_time == "No GPS Time":
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
        with open(latest_file, 'r') as file:
            for line in file:
                if line.startswith('$GNGLL'):
                    latest_gngll = line.strip()
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

def main():
    # Initialize video capture
    camera = cv2.VideoCapture(0, apiPreference=cv2.CAP_V4L2)
    if not camera.isOpened():
        print("Error: Could not open webcam.")
        return

    # Set up video parameters
    processor = VideoProcessor(1280, 720, 30)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, processor.width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, processor.height)
    
    # Initialize threading
    threadn = cv2.getNumberOfCPUs()
    pool = ThreadPool(processes=threadn)
    pending = deque()
    
    # Create output directory
    os.makedirs("Images", exist_ok=True)
    #clear images in the directory
    files = glob.glob('Images/*')
    for f in files: 
        os.remove(f)
    
    
    # Initialize async frame writer
    frame_writer = AsyncFrameWriter()
    
    frame_idx = 0
    try:
        while True:
            # Process frames in parallel
            if len(pending) < threadn:
                ret, frame = camera.read()
                if not ret:
                    break
                task = pool.apply_async(processor.process_frame, (frame.copy(), time.time()))
                pending.append(task)

            # Get processed frames
            while pending and pending[0].ready():
                processed_frame, _ = pending.popleft().get()
                frame_writer.write_frame(processed_frame, frame_idx)
                frame_idx += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if frame_idx >= 150:
                break

    finally:
        # Clean up
        camera.release()
        cv2.destroyAllWindows()
        frame_writer.stop()
        
        # Convert frames to video using ffmpeg
        subprocess.run([
            'ffmpeg', '-y', '-framerate', str(processor.fps),
            '-i', 'Images/opencv%d.jpg',
            '-c:v', 'mjpeg',
            f'output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mjpeg'
        ])

if __name__ == '__main__':
    main()
