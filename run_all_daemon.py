import subprocess
import os
import signal
import sys
from multiprocess import Process
import datetime
import time
from video_stamp import stamp_video
from run_all import see_cam, web_cam, mavproxy, gps_logger

def main():
    def start_process(target):
        """Start a process and return it."""
        process = Process(target=target)
        process.daemon = True  # Run as a daemon process
        process.start()
        return process

    # Start the processes
    processes = {
        "stamp_video": start_process(stamp_video),
        "mavproxy": start_process(mavproxy),
        "gps_logger": start_process(gps_logger),
    }

    try:
        while True:
            # Monitor processes and restart if any of them exit
            for name, process in processes.items():
                if not process.is_alive():
                    print(f"Process {name} has stopped. Restarting...")
                    processes[name] = start_process(globals()[name])  # Restart the process

            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        print("Main program interrupted. Exiting...")
        for process in processes.values():
            process.terminate()

if __name__ == '__main__':
    main()