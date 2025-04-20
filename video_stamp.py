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
import numpy as np

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
        sentence = self.get_latest_gps_sentence('gps_logs')
        gps_time = ''
        latitude = ''
        longitude = ''
        if sentence:
            if sentence.startswith('$GNGGA'):
                gps_time, latitude, longitude = self.parse_gngga(sentence)
            elif sentence.startswith('$GNGLL'):
                gps_time, latitude, longitude = self.parse_gngll(sentence)
        else:
            latitude, longitude = "No Lat", "No Lon"
        
        # Get current date and system time with milliseconds
        current_datetime = datetime.now()
        current_date = current_datetime.strftime("%Y-%m-%d")
        system_time = current_datetime.strftime("%H:%M:%S.%f")[:-3]  # Keep milliseconds
        
        # Use GPS time if available, otherwise fallback to system time
        if not gps_time or gps_time == "Time Error":
            gps_time = system_time
        
        # Create timestamps
        gps_timestamp = f"{current_date} {gps_time}"
        sys_timestamp = f"{current_date} {system_time}"
        
        # Calculate display metrics
        self.frame_count += 1
        elapsed_time = int(time.time() - self.start_time)
        
        # Add text overlays
        texts = [
            (f"Frame {self.frame_count}", (10, 15), (0, 0, 255)),
            (f"GPS Time: {gps_timestamp}", (10, 40), (0, 255, 0)),
            (f"Sys Time: {sys_timestamp}", (10, 65), (0, 200, 200)),
            (f"Lat: {latitude} Lon: {longitude}", (10, 90), (255, 0, 0)),
            (f"FPS: {self.frame_count / (time.time() - self.start_time):.2f}", (10, 115), (255, 255, 0))
        ]
        

        print(f"Frame {self.frame_count} processed in {time.time() - t0:.2f} seconds")
        print(f"GPS Time: {gps_timestamp}")
        print(f"Sys Time: {sys_timestamp}")
        print(f"Lat: {latitude} Lon: {longitude}")
        print(f"FPS: {self.frame_count / (time.time() - self.start_time):.2f}")
        
        for text, pos, color in texts:
            cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame, t0, (gps_time, latitude, longitude), system_time

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
            print(f"Error parsing GNGLL")
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
                print(f"Time string: {time_str}")
                hours = int(time_str[0:2])
                minutes = int(time_str[2:4])
                
                # Handle milliseconds properly
                sec_parts = time_str[4:].split('.')
                seconds = int(sec_parts[0])
                milliseconds = int(sec_parts[1][:3].ljust(3, '0')) if len(sec_parts) > 1 else 0
                
                # Format time with milliseconds
                gps_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
                print(f"Parsed GPS time: {gps_time}")
                
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
        """Read the latest GPS sentence from a file, with buffered reading"""
        list_of_files = glob.glob(os.path.join(directory, '*.log'))
        if not list_of_files:
            return None
        latest_file = max(list_of_files, key=os.path.getmtime)
        
        # Use a binary read and seek to the end, then read last few KB
        # This is much faster than reading the entire file
        try:
            with open(latest_file, 'rb') as file:
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(max(0, size - 4096), os.SEEK_SET)  # Read last 4KB
                data = file.read().decode('utf-8', errors='ignore')
                lines = data.splitlines()
                
                # Check the last few lines for GPS data
                for line in reversed(lines):
                    if line.startswith('$GNGGA'):
                        return line.strip()
                for line in reversed(lines):
                    if line.startswith('$GNGLL'):
                        return line.strip()
            return None
        except Exception as e:
            print(f"Error reading GPS file: {e}")
            return None

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
            frame, idx, gps_data, system_time = frame_data  # Updated to receive system_time
            
            # Save the image first
            image_path = f'{self.output_dir}/opencv{str(idx)}.jpg'
            cv2.imwrite(image_path, frame)
            
            # If GPS coordinates are available, add them as EXIF metadata
            if gps_data and gps_data[1] and gps_data[2]:  # Check if we have valid lat/lon
                try:
                    self._add_gps_tags(image_path, gps_data[1], gps_data[2], idx, system_time)
                except Exception as e:
                    print(f"Error adding GPS tags: {e}")
            
            print(f"Queue size {self.queue.qsize()}\n")
            self.queue.task_done()

    def _add_gps_tags(self, image_path, latitude_str, longitude_str, frame_idx=None, system_time=None):
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
            
            # Add system timestamp to EXIF
            if system_time:
                if "0th" not in exif_dict:
                    exif_dict["0th"] = {}
                exif_dict["0th"][piexif.ImageIFD.DateTime] = system_time
            
            # Insert the Exif tags
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, image_path)
            print(f"Added GPS tags and frame number to image: {image_path}")
        except Exception as e:
            print(f"Error parsing GPS coordinates: {e}")

    def write_frame(self, frame, idx, gps_data=None, system_time=None):
        self.queue.put((frame, idx, gps_data, system_time))
    
    def stop(self):
        # Send stop signal to all workers
        for _ in self.workers:
            self.queue.put(None)
        # Wait for all workers to finish
        for worker in self.workers:
            worker.join()

class AutoExposureController:
    def __init__(self, target_brightness=125, step_size=1, min_exposure=-10, max_exposure=10,
                 update_interval=10, stability_threshold=5):
        """
        Controller for auto-exposure based on a specific region of the frame
        
        Args:
            target_brightness: Target average brightness (0-255)
            step_size: How much to adjust exposure per step
            min_exposure: Minimum exposure value
            max_exposure: Maximum exposure value
            update_interval: Only update exposure every N frames
            stability_threshold: Don't adjust if within this range of target
        """
        self.target_brightness = target_brightness
        self.step_size = step_size
        self.min_exposure = min_exposure
        self.max_exposure = max_exposure
        self.current_exposure = 0  # Will be read from camera
        self.frame_count = 0
        self.update_interval = update_interval
        self.stability_threshold = stability_threshold
        
    def calculate_brightness(self, frame, region="bottom_half"):
        """Calculate the average brightness of a region in the frame"""
        if frame is None:
            return None
            
        if region == "bottom_half":
            height, width = frame.shape[:2]
            roi = frame[height//2:, :]  # Bottom half of the frame
        else:
            roi = frame  # Use full frame
            
        # Convert to grayscale if needed
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi
            
        # Calculate average brightness
        avg_brightness = np.mean(gray)
        return avg_brightness
        
    def update_exposure(self, frame, camera):
        """Update camera exposure based on bottom half brightness"""
        self.frame_count += 1
        
        # Only update every update_interval frames
        if self.frame_count % self.update_interval != 0:
            return
            
        # Read current camera exposure
        self.current_exposure = camera.get(cv2.CAP_PROP_EXPOSURE)
        
        # Calculate brightness of bottom half
        brightness = self.calculate_brightness(frame, "bottom_half")
        if brightness is None:
            return
            
        # Determine if adjustment is needed
        brightness_diff = self.target_brightness - brightness
        
        # Only adjust if difference exceeds the stability threshold
        if abs(brightness_diff) < self.stability_threshold:
            return
            
        # Calculate new exposure value
        adjustment = np.sign(brightness_diff) * self.step_size
        new_exposure = self.current_exposure + adjustment
        
        # Clamp to valid range
        new_exposure = max(self.min_exposure, min(new_exposure, self.max_exposure))
        
        # Apply new exposure if different
        if new_exposure != self.current_exposure:
            print(f"Adjusting exposure: {self.current_exposure} -> {new_exposure} (brightness: {brightness:.1f})")
            camera.set(cv2.CAP_PROP_EXPOSURE, new_exposure)
            self.current_exposure = new_exposure

def stamp_video(display=False):
    # Initialize video captures
    camera0 = cv2.VideoCapture(0, apiPreference=cv2.CAP_V4L2)
    camera1 = cv2.VideoCapture(2, apiPreference=cv2.CAP_V4L2)
    
    if not camera0.isOpened():
        print("Error: Could not open camera0.")
    if not camera1.isOpened():
        print("Error: Could not open camera1 .")
    
    if not camera0.isOpened() or not camera1.isOpened():
        print("Exiting...")
        return

    # Set up video parameters
    W, H = 1920, 1080
    processor0 = VideoProcessor(W, H, 20)
    processor1 = VideoProcessor(W, H, 20)

    # Configure both cameras
    camera0.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    camera0.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    camera0.set(cv2.CAP_PROP_FPS, 20)
    camera0.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    
    # Initial exposure setting for camera0 (will be adjusted by auto-exposure)
    initial_exposure = camera0.get(cv2.CAP_PROP_EXPOSURE)
    print(f"Initial camera0 exposure: {initial_exposure}")
    
    # Initialize auto exposure controller for camera0
    auto_exposure = AutoExposureController(
        target_brightness=130,  # Target brightness (0-255)
        step_size=0.5,          # Adjust by 0.5 each time 
        min_exposure=-7,        # Minimum exposure value
        max_exposure=7,         # Maximum exposure git value
        update_interval=15,     # Only update every 15 frames
        stability_threshold=5   # Don't adjust if within 5 units of target
    )

    camera1.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    camera1.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    camera1.set(cv2.CAP_PROP_FPS, 20)
    camera1.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    camera1.set(cv2.CAP_PROP_EXPOSURE, 3) 

    # Initialize threading
    threadn = cv2.getNumberOfCPUs()
    pool = ThreadPool(processes=threadn)
    pending0 = deque()
    pending1 = deque()
    
    # Create output directories with date and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir0 = f"Images/cam0_{timestamp}"
    output_dir1 = f"Images/cam1_{timestamp}"
    os.makedirs(output_dir0, exist_ok=True)
    os.makedirs(output_dir1, exist_ok=True)

    # Initialize async frame writers
    frame_writer0 = AsyncFrameWriter(output_dir=output_dir0)
    frame_writer1 = AsyncFrameWriter(output_dir=output_dir1)

    time.sleep(10)
    frame_idx = 0
    try:
        while True:
            # Process frames in parallel for both cameras
            if len(pending0) < threadn:
                ret0, frame0 = camera0.read()
                ret1, frame1 = camera1.read()
                if not ret0 or not ret1:
                    break
                
                # Update auto-exposure for camera0 based on bottom half of the image
                if ret0:
                    auto_exposure.update_exposure(frame0, camera0)
                
                task0 = pool.apply_async(processor0.process_frame, (frame0.copy(), time.time()))
                task1 = pool.apply_async(processor1.process_frame, (frame1.copy(), time.time()))
                pending0.append(task0)
                pending1.append(task1)

            # Get processed frames from both cameras
            while pending0 and pending0[0].ready() and pending1 and pending1[0].ready():
                processed_frame0, _, gps_data0, system_time0 = pending0.popleft().get()
                processed_frame1, _, gps_data1, system_time1 = pending1.popleft().get()
                
                try:
                    if display:
                        cv2.imshow('camera0', processed_frame0)
                        cv2.imshow('camera1', processed_frame1)
                except cv2.error as e:
                    display = False
                    print(f"Error displaying frames: {e}")

                
                frame_writer0.write_frame(processed_frame0, frame_idx, gps_data0, system_time0)
                frame_writer1.write_frame(processed_frame1, frame_idx, gps_data1, system_time1)
                frame_idx += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if frame_idx >= 100000:
                break

    finally:
        # Clean up
        camera0.release()
        camera1.release()
        cv2.destroyAllWindows()
        frame_writer0.stop()
        frame_writer1.stop()    

        # make mp4s out of images in the image folder
        print("Creating mp4s from images...")
        for output_dir in [output_dir0, output_dir1]:
            image_files = sorted(glob.glob(os.path.join(output_dir, '*.jpg')))
            image_files = [(img, os.path.getctime(img)) for img in image_files]
            image_files.sort(key=lambda x: x[1])
            if image_files:
                output_file = os.path.join(output_dir, 'output.mp4')
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(output_file, fourcc, 30.0, (W, H))
                
                for image_path, creation_time in image_files:
                    img = cv2.imread(image_path)
                    out.write(img)
                
                out.release()
                print(f"Created {output_file} from images in {output_dir}")
            else:
                print(f"No images found in {output_dir}")
``` 