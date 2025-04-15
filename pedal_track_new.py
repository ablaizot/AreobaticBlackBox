import cv2
import numpy as np
import time
import csv
import matplotlib.pyplot as plt
import os
from datetime import timedelta # Import timedelta

# Function to track the blue square tape
def track_blue_tape(image):
    """
    Tracks a blue rectangular piece of tape in a video frame, focusing on the right half.

    Args:
        image (numpy.ndarray): The video frame (BGR format).

    Returns:
        tuple: (annotated_image, tape_coords)
            - annotated_image (numpy.ndarray): The frame with tracking visualizations.
            - tape_coords (tuple): (cx, cy) coordinates of the tape's center, or None if not found.
    """
    annotated_image = image.copy()
    h, w, c = image.shape

    # Define the region of interest (right half)
    roi_x_start = int(0.5 * w)
    roi_y_start = 0
    roi_width = int(0.5 * w)
    roi_height = h

    # Check if ROI coordinates are valid
    if roi_x_start < 0 or roi_y_start < 0 or roi_x_start + roi_width > w or roi_y_start + roi_height > h:
        print("ROI coordinates are invalid. Skipping frame.")
        return annotated_image, None

    # Define the color range for the blue tape (in HSV)
    # **CRITICAL:  Adjust these values to match YOUR tape's blue!**
    lower_blue = np.array([100, 100, 100])  # Example: Narrowed blue range
    upper_blue = np.array([140, 255, 255])  # Example: Narrowed blue range

    # Convert the image to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Create a mask for the blue color, applied to the ROI
    mask = cv2.inRange(hsv[roi_y_start:roi_y_start + roi_height, roi_x_start:roi_x_start + roi_width], lower_blue, upper_blue)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize tape coordinates as None
    tape_coords = None

    # Find the largest contour (assuming it's the tape)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)

        # Get the bounding rectangle of the contour
        x, y, width, height = cv2.boundingRect(largest_contour)

        # Adjust x, y to be relative to the whole image
        x += roi_x_start
        y += roi_y_start

        # Calculate the center of the rectangle
        cx, cy = x + width // 2, y + height // 2

        # Filter by size.  Adjust min_size and max_size as needed.
        min_size = 10  # Minimum area in pixels
        max_size = 5000  # Maximum area in pixels
        if min_size < area < max_size:
            # Draw a rectangle around the tape
            cv2.rectangle(annotated_image, (x, y), (x + width, y + height), (0, 255, 0), 2)

            # Draw a circle at the center
            cv2.circle(annotated_image, (cx, cy), 5, (0, 0, 255), cv2.FILLED)

            # Save tape coordinates for CSV
            tape_coords = (cx, cy)

            # Display coordinates
            cv2.putText(annotated_image, f"Tape: ({cx}, {cy})",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Draw a rectangle showing the ROI
    cv2.rectangle(annotated_image, (roi_x_start, roi_y_start),
                    (roi_x_start + roi_width, roi_y_start + roi_height), (255, 0, 0), 2)

    return annotated_image, tape_coords


def format_time(seconds):
    """Convert seconds to MM:SS format"""
    return str(timedelta(seconds=int(seconds)))[2:7]  # Skip hours, get MM:SS

def plot_tape_movements(tape_data):
    """Generate plots showing tape movement over time with normalized values (-1 to 1 range)"""
    if not tape_data:
        print("No tape data to plot")
        return

    times = [t for t, nx, ny in tape_data]
    x_coords_norm = [nx for t, nx, ny in tape_data]
    y_coords_norm = [ny for t, nx, ny in tape_data]

    # Create figure with 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))

    # Plot 1: Normalized X position over time (-1 to 1 range)
    ax1.plot(times, x_coords_norm, 'r-')
    ax1.set_title('Normalized X Position Over Time (-1 to 1)')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Normalized X Position (-1 to 1)')
    ax1.grid(True)
    ax1.set_ylim(-1.1, 1.1) # Set y-axis limits for normalized values

    # Plot 2: Normalized Y position over time (-1 to 1 range)
    ax2.plot(times, y_coords_norm, 'b-')
    ax2.set_title('Normalized Y Position Over Time (-1 to 1)')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Normalized Y Position (-1 to 1)')
    ax2.grid(True)
    ax2.set_ylim(-1.1, 1.1) # Set y-axis limits for normalized values

    # Plot 3: 2D trajectory (normalized -1 to 1 range)
    ax3.plot(x_coords_norm, y_coords_norm, 'g-o', alpha=0.5)
    ax3.set_title('Tape Position Trajectory (Normalized -1 to 1)')
    ax3.set_xlabel('Normalized X Position (-1 to 1)')
    ax3.set_ylabel('Normalized Y Position (-1 to 1)')
    ax3.grid(True)
    ax3.set_xlim(-1.1, 1.1) # Set x-axis limits for normalized values
    ax3.set_ylim(-1.1, 1.1) # Set y-axis limits for normalized values

    # Invert Y axis for more intuitive plotting (0 at top like screen coordinates)
    ax3.invert_yaxis()

    # Add timestamps to trajectory (using normalized coordinates for annotation)
    for i in range(0, len(times), max(1, len(times) // 10)):  # Add ~10 time labels
        ax3.annotate(format_time(times[i]), (x_coords_norm[i], y_coords_norm[i]))

    # Save the plot
    fig.tight_layout()
    fig.savefig('tape_movement_analysis_-1_1.png')
    print("Saved grip movement analysis (-1 to 1 normalized) to 'tape_movement_analysis_-1_1.png'")

    # Show the plot
    plt.show()


def get_incremented_filename(base_filepath):
    """Generate a filename that doesn't override existing files by adding a counter."""
    if not os.path.exists(base_filepath):
        return base_filepath

    directory, filename = os.path.split(base_filepath)
    name, extension = os.path.splitext(filename)
    counter = 1

    while True:
        new_filename = f"{name}_{counter}{extension}"
        new_filepath = os.path.join(directory, new_filename)
        if not os.path.exists(new_filepath):
            return new_filepath
        counter += 1


def main():
    # Create videos directory if it doesn't exist
    os.makedirs('videos', exist_ok=True)

    # For video file input
    cap = cv2.VideoCapture('cropped_video.mp4')  # Replace with your video file

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"FPS: {fps}, Width: {width}, Height: {height}, Total Frames: {total_frames}")  # ADDED

    # Calculate frame positions
    start_time = 0
    duration = 30  # Track for 30 seconds, for example
    duration_type = 'seconds'  # Can be 'seconds' or 'frames'

    if duration_type == 'seconds':
        end_frame = int(start_time * fps) + int(duration * fps)
    elif duration_type == 'frames':
        end_frame = int(start_time) + int(duration)
    else:
        print("Error: duration_type must be 'seconds' or 'frames'.  Defaulting to full video.")
        end_frame = total_frames

    start_frame = int(start_time * fps)

    # Check if calculated end_frame exceeds total frames
    if end_frame > total_frames:
        end_frame = total_frames
        print(f"Warning: Video is shorter than specified duration. Will process until the end. end_frame is now: {end_frame}")

    # Set the frame position to start_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame

    # Get incremented filenames for outputs
    video_output_path = get_incremented_filename('videos/tracked_output_tape.mp4')
    csv_output_path = get_incremented_filename('videos/tape_positions_normalized_-1_1.csv') # Changed filename
    plot_output_path = get_incremented_filename('videos/tape_movement_analysis_-1_1.png') # Changed filename

    # Optional: save the processed video
    out = cv2.VideoWriter(video_output_path,
                            cv2.VideoWriter_fourcc(*'mp4v'),
                            fps, (width, height))
    print(f"Video will be saved to: {video_output_path}")

    # Track coordinates over time for analysis
    tape_positions_raw = []
    all_x_coords = []
    all_y_coords = []

    # CSV file for tape position data
    csv_file = open(csv_output_path, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Timestamp', 'Time_Seconds', 'X_Position_Normalized', 'Y_Position_Normalized', 'X_Position_Raw', 'Y_Position_Raw']) # Added raw values

    print(f"Writing normalized (-1 to 1 range) tape positions to: {csv_output_path}")

    print(f"Processing frames from {start_time / 60:.1f}:00 to {(start_time + duration) / 60:.1f}:00")
    print(f"Frame range: start_frame: {start_frame}, end_frame: {end_frame}, total_frames: {total_frames}")

    while cap.isOpened() and current_frame < end_frame:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame. Exiting...")
            break

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Track tape and draw visualizations
        annotated_frame, tape_coords = track_blue_tape(frame)

        # Calculate current video time
        video_time = (current_frame / fps)
        minutes = video_time // 60
        seconds = video_time % 60
        timestamp = f"{int(minutes):02d}:{int(seconds):02d}"

        # Add timestamp to the frame
        cv2.putText(frame, f"Time: {timestamp}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Record tape position with timestamp if grip was detected
        if tape_coords:
            tape_x, tape_y = tape_coords
            tape_positions_raw.append((video_time, tape_x, tape_y))
            all_x_coords.append(tape_x)
            all_y_coords.append(tape_y)

        # Write frame to output video
        out.write(annotated_frame)

        # Increment the frame counter
        current_frame += 1

        # Show progress every 30 seconds of video
        if current_frame % (fps * 30) == 0:
            current_min = (current_frame / fps) // 60
            current_sec = (current_frame / fps) % 60
            print(f"Processed up to {int(current_min):02d}:{int(current_sec):02d}")

        if cv2.waitKey(5) & 0xFF == 27:  # ESC to exit
            break

    # Clean up
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    if all_x_coords and all_y_coords:
        min_x = min(all_x_coords)
        max_x = max(all_x_coords)
        min_y = min(all_y_coords)
        max_y = max(all_y_coords)

        normalized_tape_positions = []
        for time, x, y in tape_positions_raw:
            range_x = max_x - min_x
            range_y = max_y - min_y
            norm_x = 2 * (x - min_x) / range_x - 1 if range_x != 0 else 0
            norm_y = 2 * (y - min_y) / range_y - 1 if range_y != 0 else 0
            normalized_tape_positions.append((time, norm_x, norm_y, x, y)) # Store normalized and raw

            # Write to CSV with normalized values
            csv_writer.writerow([f"{int(time // 60):02d}:{int(time % 60):02d}", time, norm_x, norm_y, x, y])

        csv_file.close()
        print(f"Saved {len(normalized_tape_positions)} normalized (-1 to 1 range) tape positions to '{csv_output_path}'")

        # Create plots of tape movement with normalized values (-1 to 1 range)
        if normalized_tape_positions:
            # Extract only the time and normalized x, y for plotting
            plot_data = [(t, nx, ny) for t, nx, ny, _, _ in normalized_tape_positions]
            plot_tape_movements(plot_data)
        else:
            print("No tape positions were detected for plotting.")
    else:
        csv_file.close()
        print("No tape positions were detected.")


if __name__ == "__main__":
    main()