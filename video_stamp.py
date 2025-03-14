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
import piexif
from fractions import Fraction

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
        
        return frame, t0, (gps_time, latitude, longitude)

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
    def parse_gngga(gngga_sentence):
        """Parse UTC time and coordinates from GNGGA sentence"""
        try:
            parts = gngga_sentence.split(',')
            if len(parts) >= 10:  # GNGGA has at least 14 fields + checksum
                # Get time
                time_str = parts[1]
                hours = int(time_str[0:2])
                minutes = int(time_str[2:4])
                seconds = int(float(time_str[4:]))
                gps_time = f"{hours}:{minutes}:{seconds}"
                
                # Get latitude
                latitude = parts[2] + ' ' + parts[3]
                
                # Get longitude
                longitude = parts[4] + ' ' + parts[5]
                
                # Additional data you might want to use
                fix_quality = parts[6]  # 0=invalid, 1=GPS fix, 2=DGPS fix
                num_satellites = parts[7]
                altitude = parts[9] + ' ' + parts[10]  # e.g., "30.6 M"
                
                return gps_time, latitude, longitude
        except (IndexError, ValueError) as e:
            print(f"Error parsing GNGGA: {e}")
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
                if line.startswith('$GNGLL') or line.startswith('$GNRMC') or line.startswith('$GNGGA'):
                    latest_gngll = line.strip()
        print(f"Latest GNGLL: {latest_gngll}")
        return latest_gngll

    @staticmethod
    def get_latest_gps_sentence(directory):
        """Read the latest GPS sentence from a file"""
        list_of_files = glob.glob(os.path.join(directory, '*.log'))
        if not list_of_files:
            return None
        latest_file = max(list_of_files, key=os.path.getmtime)
        latest_gps = None
        print(f"Reading from {latest_file}")
        with open(latest_file, 'r') as file:
            for line in file:
                if line.startswith('$GNGGA'):
                    latest_gps = line.strip()
                elif line.startswith('$GNGLL') and not latest_gps:
                    latest_gps = line.strip()
        print(f"Latest GPS: {latest_gps}")
        return latest_gps

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
            frame, idx, gps_data = frame_data  # Updated to receive GPS data
            
            # Save the image first
            image_path = f'{self.output_dir}/opencv{str(idx)}.jpg'
            cv2.imwrite(image_path, frame)
            
            # If GPS coordinates are available, add them as EXIF metadata
            if gps_data and gps_data[1] and gps_data[2]:  # Check if we have valid lat/lon
                try:
                    self._add_gps_tags(image_path, gps_data[1], gps_data[2], idx)
                except Exception as e:
                    print(f"Error adding GPS tags: {e}")
            
            print(f"Queue size {self.queue.qsize()}\n")
            self.queue.task_done()

    def _add_gps_tags(self, image_path, latitude_str, longitude_str, frame_idx=None):
        """Add GPS EXIF metadata to an image"""
        # Parse latitude and longitude strings into decimal values
        try:
            # Initialize variables with default values
            latitude = 0.0
            longitude = 0.0
            
            # Example format: "3724.7669 N" -> 37.412782 (decimal degrees)
            # First we need to parse our NMEA format to decimal degrees
            lat_parts = latitude_str.split()
            if len(lat_parts) == 2:
                lat_value = float(lat_parts[0])
                lat_deg = int(lat_value / 100)
                lat_min = lat_value - (lat_deg * 100)
                latitude = lat_deg + (lat_min / 60)
                if lat_parts[1] == 'S':
                    latitude = -latitude
                    
            lon_parts = longitude_str.split()
            if len(lon_parts) == 2:
                lon_value = float(lon_parts[0])
                lon_deg = int(lon_value / 100)
                lon_min = lon_value - (lon_deg * 100)
                longitude = lon_deg + (lon_min / 60)
                if lon_parts[1] == 'W':
                    longitude = -longitude
            
            # Convert to EXIF format (degrees, minutes, seconds as rationals)
            def to_deg(value, loc):
                """Convert decimal coordinates to degrees, minutes, seconds"""
                if value < 0:
                    loc_value = loc[0]
                else:
                    loc_value = loc[1]
                
                abs_value = abs(value)
                deg = int(abs_value)
                min = int((abs_value - deg) * 60)
                sec = int(((abs_value - deg) * 60 - min) * 60 * 100)
                
                return deg, min, sec, loc_value
            
            lat_deg, lat_min, lat_sec, lat_ref = to_deg(latitude, ["S", "N"])
            lon_deg, lon_min, lon_sec, lon_ref = to_deg(longitude, ["W", "E"])
            
            # Create Exif dictionary
            exif_dict = {"GPS": {
                piexif.GPSIFD.GPSLatitudeRef: lat_ref,
                piexif.GPSIFD.GPSLatitude: [(lat_deg, 1), (lat_min, 1), (lat_sec, 100)],
                piexif.GPSIFD.GPSLongitudeRef: lon_ref,
                piexif.GPSIFD.GPSLongitude: [(lon_deg, 1), (lon_min, 1), (lon_sec, 100)]
            }}
            
            # Add frame number to EXIF data
            if frame_idx is not None:
                # Add to 0th IFD (main image information)
                if "0th" not in exif_dict:
                    exif_dict["0th"] = {}
                    
                # Store frame number in ImageDescription
                exif_dict["0th"][piexif.ImageIFD.ImageDescription] = f"Frame {frame_idx}"
            
            # Insert the Exif tags
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, image_path)
            print(f"Added GPS tags and frame number to image: {image_path}")
        except Exception as e:
            print(f"Error parsing GPS coordinates: {e}")

    def write_frame(self, frame, idx, gps_data=None):
        self.queue.put((frame, idx, gps_data))
    
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
                processed_frame0, _, gps_data0 = pending0.popleft().get()
                processed_frame1, _, gps_data1 = pending1.popleft().get()
                
                try:
                    if display:
                        cv2.imshow('camera0', processed_frame0)
                        cv2.imshow('camera1', processed_frame1)
                except cv2.error as e:
                    display = False
                    print(f"Error displaying frames: {e}")

                
                frame_writer0.write_frame(processed_frame0, frame_idx, gps_data0)
                frame_writer1.write_frame(processed_frame1, frame_idx, gps_data1)
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


