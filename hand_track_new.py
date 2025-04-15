import cv2
import mediapipe as mp
import numpy as np
import time
import csv
import matplotlib.pyplot as plt
from datetime import timedelta
import os

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# Function to track hand landmarks on control stick
def track_hand_on_stick(image, results):
    # Make a copy of the image to draw on
    annotated_image = image.copy()
    h, w, c = image.shape

    # Define bottom left quadrant boundaries
    left_boundary = 3 * w // 4

    # Calculate the bottom boundary to exclude the bottom 15%
    bottom_boundary = int(0.8 * h)  # 80% of the height (100% - 15%)

    # Define the upper limit for analysis (top 25% exclusion)
    upper_limit = int(0.25 * h)

    # Initialize grip coordinates as None
    grip_coords = None

    # Find the hand closest to the bottom of the image
    bottom_most_hand = None
    bottom_most_y = 0

    if results.multi_hand_landmarks:
        # First pass: find the bottom-most hand in the tracking zone
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Get coordinates of wrist (base of hand, landmark 0) as reference point
            wrist = hand_landmarks.landmark[0]
            wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)

            # Check if hand is in left quadrant AND above the bottom boundary
            if wrist_x < left_boundary and wrist_y < bottom_boundary and wrist_y > upper_limit:
                # If this hand is lower (larger y value) than current bottom-most hand
                if wrist_y > bottom_most_y:
                    bottom_most_y = wrist_y
                    bottom_most_hand = i

        # Second pass: only process the bottom-most hand
        if bottom_most_hand is not None:
            hand_landmarks = results.multi_hand_landmarks[bottom_most_hand]

            # Draw all landmarks
            mp_drawing.draw_landmarks(
                annotated_image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

            # USE THIS ONE
            # Get coordinates of index fingertip (landmark 8)
            index_tip = hand_landmarks.landmark[8]
            cx, cy = int(index_tip.x * w), int(index_tip.y * h)

            # Draw circle at fingertip
            cv2.circle(annotated_image, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

            # Get coordinates of thumb tip (landmark 4)
            thumb_tip = hand_landmarks.landmark[4]
            tx, ty = int(thumb_tip.x * w), int(thumb_tip.y * h)

            # Draw circle at thumb tip
            cv2.circle(annotated_image, (tx, ty), 15, (255, 0, 0), cv2.FILLED)

            # Draw line between index and thumb (representing grip)
            cv2.line(annotated_image, (cx, cy), (tx, ty), (255, 255, 0), 3)

            # Calculate grip center (midpoint between index and thumb)
            grip_x, grip_y = (cx + tx) // 2, (cy + ty) // 2
            cv2.circle(annotated_image, (grip_x, grip_y), 10, (0, 0, 255), cv2.FILLED)

            # Save grip coordinates for CSV
            grip_coords = (grip_x, grip_y)

            # Display coordinates
            cv2.putText(annotated_image, f"Grip: ({grip_x}, {grip_y})",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Indicate that this is the bottom-most hand
            cv2.putText(annotated_image, "Bottom Hand", (cx, cy - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    # Draw quadrant boundary lines
    cv2.line(annotated_image, (left_boundary, 0), (left_boundary, h), (128, 128, 128), 1)
    cv2.line(annotated_image, (0, bottom_boundary), (w, bottom_boundary), (0, 0, 255), 2)  # draw bottom boundary line
    cv2.line(annotated_image, (0, upper_limit), (w, upper_limit), (0, 0, 255), 2)    # Draw upper limit line

    # Label the tracking quadrant
    cv2.putText(annotated_image, "Tracking Zone", (20, h-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    return annotated_image, grip_coords

def format_time(seconds):
    """Convert seconds to MM:SS format"""
    return str(timedelta(seconds=int(seconds)))[2:7]  # Skip hours, get MM:SS

def plot_grip_movements(grip_data):
    """Generate plots showing grip movement over time with normalized values (-1 to 1 range)"""
    if not grip_data:
        print("No grip data to plot")
        return

    times = [t for t, nx, ny in grip_data]
    x_coords_norm = [nx for t, nx, ny in grip_data]
    y_coords_norm = [ny for t, nx, ny in grip_data]

    # Create figure with 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))

    # Plot 1: Normalized X position over time (-1 to 1 range)
    ax1.plot(times, x_coords_norm, 'r-')
    ax1.set_title('Normalized X Position Over Time (-1 to 1)')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Normalized X Position (-1 to 1)')
    ax1.grid(True)
    ax1.set_ylim(-1.1, 1.1)  # Set y-axis limits for normalized values

    # Plot 2: Normalized Y position over time (-1 to 1 range)
    ax2.plot(times, y_coords_norm, 'b-')
    ax2.set_title('Normalized Y Position Over Time (-1 to 1)')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Normalized Y Position (-1 to 1)')
    ax2.grid(True)
    ax2.set_ylim(-1.1, 1.1)  # Set y-axis limits for normalized values

    # Plot 3: 2D trajectory (normalized -1 to 1 range)
    ax3.plot(x_coords_norm, y_coords_norm, 'g-o', alpha=0.5)
    ax3.set_title('Grip Position Trajectory (Normalized -1 to 1)')
    ax3.set_xlabel('Normalized X Position (-1 to 1)')
    ax3.set_ylabel('Normalized Y Position (-1 to 1)')
    ax3.grid(True)
    ax3.set_xlim(-1.1, 1.1)  # Set x-axis limits for normalized values
    ax3.set_ylim(-1.1, 1.1)  # Set y-axis limits for normalized values

    # Invert Y axis for more intuitive plotting (0 at top like screen coordinates)
    ax3.invert_yaxis()

    # Add timestamps to trajectory (using normalized coordinates for annotation)
    for i in range(0, len(times), max(1, len(times) // 10)):    # Add ~10 time labels
        ax3.annotate(format_time(times[i]), (x_coords_norm[i], y_coords_norm[i]))

    # Save the plot
    fig.tight_layout()
    fig.savefig('grip_movement_analysis_-1_1.png')
    print("Saved grip movement analysis (-1 to 1 normalized) to 'grip_movement_analysis_-1_1.png'")

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
    cap = cv2.VideoCapture('hand_track_new.mp4')    # Replace with your video file

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate frame positions for 16:00 and 25:00
    start_time = 0 * 60    # 16 minutes in seconds
    end_time = 16 * 60      # 25 minutes in seconds

    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)

    # Check if calculated end_frame exceeds total frames
    if end_frame > total_frames:
        end_frame = total_frames
        print(f"Warning: Video is shorter than 16:00. Will process until the end.")

    # Set the frame position to start_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame

    # Get incremented filenames for outputs
    video_output_path = get_incremented_filename('videos/tracked_output.mp4')
    csv_output_path = get_incremented_filename('videos/grip_positions_normalized_-1_1.csv')  # Changed filename
    plot_output_path = get_incremented_filename('videos/grip_movement_analysis_-1_1.png')  # Changed filename

    # Optional: save the processed video
    out = cv2.VideoWriter(video_output_path,
                            cv2.VideoWriter_fourcc(*'mp4v'),
                            fps, (width, height))

    print(f"Video will be saved to: {video_output_path}")

    # Track coordinates over time for analysis
    grip_positions_raw = []
    all_x_coords = []
    all_y_coords = []

    # CSV file for grip position data
    csv_file = open(csv_output_path, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Timestamp', 'Time_Seconds', 'X_Position_Normalized', 'Y_Position_Normalized', 'X_Position_Raw', 'Y_Position_Raw'])  # Added raw values

    print(f"Writing normalized (-1 to 1 range) grip positions to: {csv_output_path}")

    print(f"Processing frames from {start_time/60:.1f}:00 to {end_time/60:.1f}:00")
    print(f"Frame range: {start_frame} to {end_frame}")

    while cap.isOpened() and current_frame < end_frame:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame. Exiting...")
            break

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame and get hand landmarks
        results = hands.process(rgb_frame)

        # Track hand and draw visualizations
        annotated_frame, grip_coords = track_hand_on_stick(frame, results)

        # Calculate current video time
        video_time = (current_frame / fps)
        minutes = video_time // 60
        seconds = video_time % 60
        timestamp = f"{int(minutes):02d}:{int(seconds):02d}"

        # Add timestamp to the frame
        cv2.putText(annotated_frame, f"Time: {timestamp}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Record grip position with timestamp if grip was detected
        if grip_coords:
            grip_x, grip_y = grip_coords
            grip_positions_raw.append((video_time, grip_x, grip_y))
            all_x_coords.append(grip_x)
            all_y_coords.append(grip_y)

            # Write to CSV with raw values (normalized will be done later)
            csv_writer.writerow([timestamp, video_time, '', '', grip_x, grip_y])

        # Write frame to output video
        out.write(annotated_frame)

        # Increment the frame counter
        current_frame += 1

        # Show progress every 30 seconds of video
        if current_frame % (fps * 30) == 0:
            current_min = (current_frame / fps) // 60
            current_sec = (current_frame / fps) % 60
            print(f"Processed up to {int(current_min):02d}:{int(current_sec):02d}")

        if cv2.waitKey(5) & 0xFF == 27:    # ESC to exit
            break

    # Clean up
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    csv_file.close()

    if all_x_coords and all_y_coords:
        min_x = min(all_x_coords)
        max_x = max(all_x_coords)
        min_y = min(all_y_coords)
        max_y = max(all_y_coords)

        normalized_grip_positions = []
        with open(csv_output_path, 'w', newline='') as csvfile:
            csv_writer_normalized = csv.writer(csvfile)
            csv_writer_normalized.writerow(['Timestamp', 'Time_Seconds', 'X_Position_Normalized', 'Y_Position_Normalized', 'X_Position_Raw', 'Y_Position_Raw'])
            for time, x, y in grip_positions_raw:
                range_x = max_x - min_x
                range_y = max_y - min_y
                norm_x = 2 * (x - min_x) / range_x - 1 if range_x != 0 else 0
                norm_y = 2 * (y - min_y) / range_y - 1 if range_y != 0 else 0
                normalized_grip_positions.append((time, norm_x, norm_y))
                timestamp_norm = f"{int(time // 60):02d}:{int(time % 60):02d}"
                csv_writer_normalized.writerow([timestamp_norm, time, norm_x, norm_y, x, y])

        print(f"Saved {len(normalized_grip_positions)} normalized (-1 to 1 range) grip positions to '{csv_output_path}'")

        # Create plots of grip movement with normalized values (-1 to 1 range)
        if normalized_grip_positions:
            plot_grip_movements(normalized_grip_positions)
        else:
            print("No grip positions were detected in the tracking zone for plotting.")
    else:
        print("No grip positions were detected in the tracking zone.")

if __name__ == "__main__":
    main()
