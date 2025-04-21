import serial
import threading
import pynmea2  # pip install pynmea2
import os
import time

class GPSReader:
    """Read GPS data directly from serial port in background thread"""
    def __init__(self, device_paths=["/dev/ttyACM0"], baud_rate=115200):
        self.device_paths = device_paths
        self.baud_rate = baud_rate
        self.serial_port = None
        self.running = False
        self.thread = None
        self.device_path = None
        self.connection_attempts = 0
        self.last_reconnect_time = 0
        
        # Latest parsed GPS data
        self.latest_data = {
            "gps_time": None,
            "latitude": None,
            "longitude": None,
            "altitude": None,
            "speed": None,
            "course": None,
            "satellites": None,
            "quality": None,
            "hdop": None,
            "raw_gngga": None,
            "raw_gngll": None,
            "raw_gnrmc": None,
            "last_update": 0
        }
        
        # Try to open the first available GPS device
        self._open_gps_device()
        
        if self.serial_port:
            # Start background reading thread
            self.running = True
            self.thread = threading.Thread(target=self._read_gps_data, daemon=True)
            self.thread.start()
            print(f"GPS reader started on {self.device_path}")
        else:
            print("Failed to open any GPS device")
    
    def _open_gps_device(self):
        """Try to open the first available GPS device"""
        # Close any existing connection first
        if self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None
            
        # Try all configured devices in order
        for device in self.device_paths:
            if os.path.exists(device):
                try:
                    print(f"Attempting to open GPS device at {device}")
                    self.serial_port = serial.Serial(device, self.baud_rate, timeout=1)
                    self.device_path = device
                    print(f"GPS device opened at {device}")
                    self.connection_attempts = 0
                    return True
                except (serial.SerialException, PermissionError) as e:
                    print(f"Error opening {device}: {e}")
                    continue
        
        # If we get here, we've tried all devices and failed
        if "/dev/ttyACM0" not in self.device_paths:
            # Add the fallback device explicitly
            print("Adding fallback device /dev/ttyACM0")
            if os.path.exists("/dev/ttyACM0"):
                try:
                    self.serial_port = serial.Serial("/dev/ttyACM0", self.baud_rate, timeout=1)
                    self.device_path = "/dev/ttyACM0"
                    print(f"GPS device opened at fallback /dev/ttyACM0")
                    self.connection_attempts = 0
                    return True
                except (serial.SerialException, PermissionError) as e:
                    print(f"Error opening fallback device: {e}")
        
        self.connection_attempts += 1
        print(f"Failed to open any GPS device (attempt {self.connection_attempts})")
        return False
    
    def _read_gps_data(self):
        """Background thread to continuously read GPS data"""
        read_errors = 0
        max_read_errors = 10  # Maximum consecutive read errors before trying to reconnect
        
        while self.running:
            if not self.serial_port:
                # No connection, try to reconnect after a delay
                current_time = time.time()
                if current_time - self.last_reconnect_time > 5:  # Wait at least 5 seconds between reconnect attempts
                    self.last_reconnect_time = current_time
                    if self._open_gps_device():
                        read_errors = 0
                    else:
                        time.sleep(1)  # Avoid busy-waiting
                continue
                
            try:
                # Read one line from the GPS device
                line = self.serial_port.readline().decode('ascii', errors='replace').strip()
                
                if line:
                    # Reset error counter on successful read
                    read_errors = 0
                    
                    # Store the raw sentence by type
                    if line.startswith('$GNGGA'):
                        self.latest_data["raw_gngga"] = line
                        self._parse_gngga(line)
                    elif line.startswith('$GNGLL'):
                        self.latest_data["raw_gngll"] = line
                        self._parse_gngll(line)
                    elif line.startswith('$GNRMC'):
                        self.latest_data["raw_gnrmc"] = line
                        self._parse_gnrmc(line)
                else:
                    # Empty line might indicate a connection issue
                    read_errors += 1
                    
            except (UnicodeDecodeError, serial.SerialException) as e:
                read_errors += 1
                print(f"Error reading from GPS: {e}")
                
                # If we have too many consecutive errors, try to reconnect
                if read_errors >= max_read_errors:
                    print(f"Too many read errors ({read_errors}), trying to reconnect...")
                    try:
                        self.serial_port.close()
                    except:
                        pass
                    self.serial_port = None
                    # Force next iteration to attempt reconnection
                    self.last_reconnect_time = 0
                else:
                    time.sleep(0.5)  # Avoid busy-waiting on errors
    
    def _parse_gngga(self, sentence):
        """Parse GGA sentence for position, altitude, etc."""
        try:
            msg = pynmea2.parse(sentence)
            self.latest_data["gps_time"] = self._format_gps_time(msg.timestamp)
            self.latest_data["latitude"] = f"{msg.latitude:.6f} {msg.lat_dir}"
            self.latest_data["longitude"] = f"{msg.longitude:.6f} {msg.lon_dir}"
            self.latest_data["altitude"] = msg.altitude
            self.latest_data["satellites"] = msg.num_sats
            self.latest_data["quality"] = msg.gps_qual
            self.latest_data["hdop"] = msg.horizontal_dil
            self.latest_data["last_update"] = time.time()
        except Exception as e:
            print(f"Error parsing GNGGA: {e}")
    
    def _parse_gngll(self, sentence):
        """Parse GLL sentence for position"""
        try:
            msg = pynmea2.parse(sentence)
            self.latest_data["gps_time"] = self._format_gps_time(msg.timestamp)
            self.latest_data["latitude"] = f"{msg.latitude:.6f} {msg.lat_dir}"
            self.latest_data["longitude"] = f"{msg.longitude:.6f} {msg.lon_dir}"
            self.latest_data["last_update"] = time.time()
        except Exception as e:
            print(f"Error parsing GNGLL: {e}")
    
    def _parse_gnrmc(self, sentence):
        """Parse RMC sentence for speed and course"""
        try:
            msg = pynmea2.parse(sentence)
            if msg.status == 'A':  # 'A' means valid
                self.latest_data["gps_time"] = self._format_gps_time(msg.timestamp)
                self.latest_data["speed"] = msg.spd_over_grnd
                self.latest_data["course"] = msg.true_course
                self.latest_data["last_update"] = time.time()
        except Exception as e:
            print(f"Error parsing GNRMC: {e}")
    
    def _format_gps_time(self, timestamp):
        """Format GPS timestamp to HH:MM:SS.sss format"""
        if timestamp:
            return f"{timestamp.hour:02d}:{timestamp.minute:02d}:{timestamp.second:02d}.{timestamp.microsecond//1000:03d}"
        return None
    
    def get_latest_data(self):
        """Get the latest GPS data"""
        return self.latest_data
    
    def get_latest_raw_sentence(self, sentence_type='GNGGA'):
        """Get the latest raw NMEA sentence of specified type"""
        if sentence_type == 'GNGGA':
            return self.latest_data["raw_gngga"]
        elif sentence_type == 'GNGLL':
            return self.latest_data["raw_gngll"]
        elif sentence_type == 'GNRMC':
            return self.latest_data["raw_gnrmc"]
        return None
    
    def close(self):
        """Stop the GPS reader thread and close the serial port"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.serial_port:
            self.serial_port.close()
            print("GPS serial port closed")