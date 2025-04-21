import os
import shutil
import time
import glob
import logging
from datetime import datetime
from threading import Thread, Event
from queue import Queue, Empty

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("transfer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ram_to_sd")

class RamDiskTransfer:
    def __init__(self, ramdisk_base="/mnt/ramdisk", sd_base="Images", 
                 max_files_per_batch=50, sleep_interval=2, max_workers=4):
        """
        Background process that transfers files from RAM disk to SD card
        
        Args:
            ramdisk_base: Base directory of the RAM disk
            sd_base: Base directory on the SD card
            max_files_per_batch: Maximum number of files to transfer in one batch
            sleep_interval: Time to sleep between checks (seconds)
            max_workers: Number of worker threads for file transfers
        """
        self.ramdisk_base = ramdisk_base
        self.sd_base = sd_base
        self.max_files_per_batch = max_files_per_batch
        self.sleep_interval = sleep_interval
        self.transfer_queue = Queue()
        self.stop_event = Event()
        self.workers = []
        self.max_workers = max_workers
        
        # Track transferred files to avoid duplicates
        self.transferred_files = set()
        
        # Create a list to store subdirectories that need monitoring
        self.monitored_dirs = []
        self.scan_for_directories()
        
        # Start worker threads
        self._start_workers()
        
        logger.info(f"RAM disk transfer initialized. RAM: {ramdisk_base}, SD: {sd_base}")

    def scan_for_directories(self):
        """Scan RAM disk for camera directories to monitor"""
        try:
            subdirs = [d for d in os.listdir(self.ramdisk_base) 
                      if os.path.isdir(os.path.join(self.ramdisk_base, d))]
            
            for subdir in subdirs:
                if subdir not in self.monitored_dirs:
                    self.monitored_dirs.append(subdir)
                    logger.info(f"Added new directory to monitor: {subdir}")
                    
                    # Make sure the corresponding SD card directory exists
                    sd_dir = os.path.join(self.sd_base, subdir)
                    os.makedirs(sd_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Error scanning directories: {e}")

    def _start_workers(self):
        """Start worker threads for file transfer"""
        for i in range(self.max_workers):
            worker = Thread(target=self._transfer_worker, daemon=True)
            worker.start()
            self.workers.append(worker)
            logger.info(f"Started transfer worker {i+1}")

    def _transfer_worker(self):
        """Worker thread that processes file transfers"""
        while not self.stop_event.is_set():
            try:
                file_info = self.transfer_queue.get(timeout=1)
                if file_info is None:
                    break
                    
                src_path, dest_path = file_info
                
                # Transfer the file
                try:
                    shutil.copy2(src_path, dest_path)
                    # Only remove from RAM disk if successfully copied
                    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                        os.remove(src_path)
                        self.transferred_files.add(os.path.basename(src_path))
                        logger.debug(f"Transferred: {os.path.basename(src_path)}")
                    else:
                        logger.warning(f"Transfer failed, file will be retried: {src_path}")
                except Exception as e:
                    logger.error(f"Error transferring {src_path}: {e}")
                
                self.transfer_queue.task_done()
            except Empty:
                pass
            except Exception as e:
                logger.error(f"Worker error: {e}")

    def check_and_transfer(self):
        """Check RAM disk for new files and queue them for transfer"""
        try:
            # Refresh directory list first
            self.scan_for_directories()
            
            files_found = False
            for subdir in self.monitored_dirs:
                ram_dir = os.path.join(self.ramdisk_base, subdir)
                sd_dir = os.path.join(self.sd_base, subdir)
                
                if not os.path.exists(ram_dir):
                    continue
                
                # Get all jpg files in the RAM disk directory
                files = glob.glob(os.path.join(ram_dir, "*.jpg"))
                files.sort(key=os.path.getctime)  # Sort by creation time
                
                # Limit batch size
                files = files[:self.max_files_per_batch]
                
                if files:
                    files_found = True
                    logger.info(f"Found {len(files)} files in {subdir} to transfer")
                    
                for src_path in files:
                    filename = os.path.basename(src_path)
                    dest_path = os.path.join(sd_dir, filename)
                    
                    # Skip if already transferred
                    if filename in self.transferred_files:
                        continue
                        
                    self.transfer_queue.put((src_path, dest_path))
            
            # Keep checking even if no files are found
            if not files_found:
                logger.debug("No files to transfer at this time")
                
        except Exception as e:
            logger.error(f"Error in check_and_transfer: {e}")
            # Continue despite errors

    def start(self):
        """Start the transfer process in a loop"""
        logger.info("Starting RAM disk to SD card transfer process")
        try:
            while not self.stop_event.is_set():
                self.check_and_transfer()
                time.sleep(self.sleep_interval)
        except KeyboardInterrupt:
            logger.info("Stopping due to keyboard interrupt")
            self.stop()
        except Exception as e:
            logger.error(f"Error in transfer loop: {e}")
            self.stop()

    def stop(self):
        """Stop the transfer process"""
        logger.info("Stopping transfer process")
        self.stop_event.set()
        
        # Signal all workers to stop
        for _ in self.workers:
            self.transfer_queue.put(None)
            
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=2)
            
        logger.info("Transfer process stopped")

# Main entry point when script is run directly
if __name__ == "__main__":
    # Configure RAM disk path based on system
    if os.name == 'nt':  # Windows
        ramdisk_path = "R:"  # Adjust if your RAM disk has a different letter
    else:  # Linux/macOS
        ramdisk_path = "/mnt/ramdisk"
    
    # Create a transfer instance and start it
    transfer = RamDiskTransfer(
        ramdisk_base=ramdisk_path,
        sd_base="Images",
        max_files_per_batch=50,
        sleep_interval=1
    )
    
    # Start the transfer process
    transfer.start()