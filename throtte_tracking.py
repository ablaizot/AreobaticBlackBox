import cv2
import numpy as np
import os
import time

def track_tape(video_path, output_path="tracked_video.mp4", csv_output_path="tracked_data.csv"):
    """
    Tracks the center of a rectangular piece of red tape in a video, calculates its normalized
    x, y coordinates, and outputs a video with the tracking.
    Only the bottom 80% of the image and the right 40% of the screen is considered for tracking.
    The output file name is incremented if a file with the same name already exists.
    Also outputs the tracking data to a CSV file, including a timestamp.
    Interpolates missing coordinates.

    Args:
        video_path (str): Path to the input video file.
        output_path (str, optional): Path to the output video file.
            Defaults to "tracked_video.mp4".
        csv_output_path (str, optional): Path to the output CSV file.
            Defaults to "tracked_data.csv".

    Returns:
        list: A list of dictionaries, where each dictionary contains the frame number,
            timestamp, and the corresponding x, and y coordinates of the tape center.
            Returns an empty list if no tape is found in the frame. Returns None if the
            video cannot be opened.

    Raises:
        cv2.error: If OpenCV encounters an error during video processing.
        Exception: For general errors like file not found.
    """
    try:
        # Open the video file
        cap = cv2.VideoCapture('acropedalroll.mp4')        # INSERT NAME OF VIDEO FILE HERE
        if not cap.isOpened():
            print(f"Error: Could not open video file: {video_path}")
            return None

        # Get video properties for output
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Check if the output video file already exists and increment the name if necessary
        output_dir = os.path.dirname(output_path)
        output_filename, output_ext = os.path.splitext(os.path.basename(output_path))
        file_index = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{output_filename}_{file_index}{output_ext}")
            file_index += 1

        # Check if the output CSV file already exists and increment the name if necessary
        csv_output_dir = os.path.dirname(csv_output_path)
        csv_output_filename, csv_output_ext = os.path.splitext(os.path.basename(csv_output_path))
        csv_file_index = 1
        while os.path.exists(csv_output_path):
            csv_output_path = os.path.join(csv_output_dir, f"{csv_output_filename}_{csv_file_index}{csv_output_ext}")
            csv_file_index += 1

        # Define the codec and create a VideoWriter object for output
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not out.isOpened():
            cap.release()
            raise Exception(f"Error: Could not open output video file for writing: {output_path}")

        tracked_data = []
        start_time = time.time()  # Record the starting time of the video processing
        last_valid_frame = -1
        last_valid_x = 0
        last_valid_y = 0

        # Define red color range for tape detection (in HSV color space)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        print(f"Processing video: {video_path}")
        print(f"Output video saved to: {output_path}")
        print(f"Tracking data saved to: {csv_output_path}")
        frame_number = 0
        while True:
            # Read a frame from the video
            ret, frame = cap.read()
            if not ret:
                break

            frame_number += 1
            # Convert the frame to the HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Calculate the ROI (Region of Interest)
            roi_height = int(height * 0.8)  # Bottom 80%
            roi_y_start = height - roi_height  # Start y-coordinate of the ROI
            roi_width = int(width * 0.32)    # Right 32%
            roi_x_start = int(width * 0.68)                # Start x-coordinate of the ROI

            # Create a mask for the bottom 80% of the image and right 32%
            mask = np.zeros_like(hsv[:, :, 0])
            mask[roi_y_start:height, roi_x_start:width] = 255

            # Apply the red color mask within the ROI mask
            red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)  # Combine the two red masks
            mask = cv2.bitwise_and(red_mask, mask)

            # Find contours in the combined mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            largest_contour = None
            center = None

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    center = (cX, cY)

            if center:
                x_normalized = (center[0] / width) * 2 - 1
                y_normalized = (center[1] / height) * 2 - 1
                timestamp = time.time() - start_time
                last_valid_frame = frame_number
                last_valid_x = x_normalized
                last_valid_y = y_normalized

                tracked_data.append({
                    "frame_number": frame_number,
                    "timestamp": timestamp,
                    "x": x_normalized,
                    "y": y_normalized,
                })

                # Increased precision to 3 decimal places
                cv2.putText(frame, f"({x_normalized:.3f}, {y_normalized:.3f})",
                            (center[0] + 10, center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0), 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)  # Draw circle only if center found

            else:
                timestamp = time.time() - start_time
                if last_valid_frame != -1:
                    tracked_data.append({
                        "frame_number": frame_number,
                        "timestamp": timestamp,
                        "x": last_valid_x,  # Use last valid x
                        "y": last_valid_y,  # Use last valid y
                    })
            out.write(frame)
            print(f"Processed frame {frame_number}/{frame_count}", end="\r")

        print(f"\nFinished processing video. Output saved to: {output_path}")
        print(f"Tracking data saved to: {csv_output_path}")
        cap.release()
        out.release()

        # Interpolate missing frames
        interpolated_data = []
        first_valid_index = -1
        last_valid_index = -1
        for i in range(len(tracked_data)):
            if last_valid_index == -1:
                interpolated_data.append(tracked_data[i])
                continue
            if i > last_valid_index + 1:
                start_frame = interpolated_data[last_valid_index]['frame_number']
                end_frame = tracked_data[i]['frame_number']
                start_x = interpolated_data[last_valid_index]['x']
                end_x = tracked_data[i]['x']
                start_y = interpolated_data[last_valid_index]['y']
                end_y = tracked_data[i]['y']
                
                for j in range(start_frame + 1, end_frame):
                    frame_delta = end_frame - start_frame
                    x_delta = end_x - start_x
                    y_delta = end_y - start_y
                    
                    interp_x = start_x + (x_delta / frame_delta) * (j - start_frame)
                    interp_y = start_y + (y_delta / frame_delta) * (j - start_frame)
                    
                    interpolated_data.append({
                        "frame_number": j,
                        "timestamp": tracked_data[i-1]['timestamp'] + (tracked_data[i]['timestamp'] - tracked_data[i-1]['timestamp']) / frame_delta,
                        "x": interp_x,
                        "y": interp_y,
                    })
                interpolated_data.append(tracked_data[i])
            else:
                interpolated_data.append(tracked_data[i])
            last_valid_index = i
        
        # Handle first frame if it is invalid
        if interpolated_data[0]['frame_number'] != 1:
            for i in range(1, interpolated_data[0]['frame_number']):
                interpolated_data.insert(0,{'frame_number': i, "timestamp": tracked_data[0]['timestamp'] / tracked_data[0]['frame_number'] * i, 'x': interpolated_data[0]['x'], 'y': interpolated_data[0]['y']})
        
        # Handle last frame if it is invalid
        if interpolated_data[-1]['frame_number'] != frame_count:
            last_valid_x = interpolated_data[-1]['x']
            last_valid_y = interpolated_data[-1]['y']
            last_valid_frame = interpolated_data[-1]['frame_number']
            time_between_frames = (tracked_data[-1]['timestamp'] - tracked_data[-2]['timestamp']) / (tracked_data[-1]['frame_number'] - tracked_data[-2]['frame_number'])
            for i in range(last_valid_frame + 1, frame_count + 1):
                interpolated_data.append({
                    "frame_number": i,
                    "timestamp": interpolated_data[-1]['timestamp'] + time_between_frames * (i - last_valid_frame),
                    "x": last_valid_x,
                    "y": last_valid_y,
                })
        
        # Write the interpolated tracking data to a CSV file
        with open(csv_output_path, 'w', newline='') as csvfile:
            import csv
            writer = csv.writer(csvfile)
            writer.writerow(["frame_number", "timestamp", "x", "y"])
            for data in interpolated_data:
                writer.writerow([data["frame_number"], data["timestamp"], data["x"], data["y"]])
        return interpolated_data

    except cv2.error as e:
        print(f"OpenCV error occurred: {e}")
        return None
    except FileNotFoundError:
        print(f"Error: Video file not found at {video_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
if __name__ == "__main__":
    # Example usage:
    input_video_path = "your_video.mp4"
    output_video_path = "tracked_tape_video.mp4"
    csv_output_path = "tracked_data.csv"
    tracked_positions = track_tape(input_video_path, output_video_path, csv_output_path)

    if tracked_positions is not None:
        if tracked_positions:
            print("\nTracking data (frame number, timestamp, x, y):")
            for data in tracked_positions:
                print(f"Frame: {data['frame_number']:.0f}, Timestamp: {data['timestamp']:.2f}, x: {data['x']:.3f}, y: {data['y']:.3f}")
        else:
            print("No red tape found in the video.")
    else:
        print("Error processing video (see error messages above).")
