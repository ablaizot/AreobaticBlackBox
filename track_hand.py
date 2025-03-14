import cv2
import mediapipe as mp
import numpy as np
import time
import csv
import matplotlib.pyplot as plt
from datetime import timedelta

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
    left_boundary = w // 2
    bottom_boundary = h // 2
    
    # Initialize grip coordinates as None
    grip_coords = None
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get coordinates of wrist (base of hand, landmark 0) as reference point
            wrist = hand_landmarks.landmark[0]
            wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)
            
            # Check if hand is in bottom left quadrant
            if wrist_x < left_boundary and wrist_y > bottom_boundary:
                # Draw all landmarks
                mp_drawing.draw_landmarks(
                    annotated_image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())
                
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
            
    # Draw quadrant boundary lines (optional)
    cv2.line(annotated_image, (left_boundary, 0), (left_boundary, h), (128, 128, 128), 1)
    cv2.line(annotated_image, (0, bottom_boundary), (w, bottom_boundary), (128, 128, 128), 1)
    
    # Label the tracking quadrant
    cv2.putText(annotated_image, "Tracking Zone", (20, h-20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
    return annotated_image, grip_coords

def format_time(seconds):
    """Convert seconds to MM:SS format"""
    return str(timedelta(seconds=int(seconds)))[2:7]  # Skip hours, get MM:SS

def plot_grip_movements(grip_data):
    """Generate plots showing grip movement over time"""
    if not grip_data:
        print("No grip data to plot")
        return
    
    times = [t for t, _, _ in grip_data]
    x_coords = [x for _, x, _ in grip_data]
    y_coords = [y for _, _, y in grip_data]
    
    # Create figure with 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))
    
    # Plot 1: X position over time
    ax1.plot(times, x_coords, 'r-')
    ax1.set_title('X Position Over Time')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('X Position')
    ax1.grid(True)
    
    # Plot 2: Y position over time
    ax2.plot(times, y_coords, 'b-')
    ax2.set_title('Y Position Over Time')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Y Position')
    ax2.grid(True)
    
    # Plot 3: 2D trajectory
    ax3.plot(x_coords, y_coords, 'g-o', alpha=0.5)
    ax3.set_title('Grip Position Trajectory')
    ax3.set_xlabel('X Position')
    ax3.set_ylabel('Y Position')
    ax3.grid(True)
    
    # Invert Y axis for more intuitive plotting (0 at top like screen coordinates)
    ax3.invert_yaxis()
    
    # Add timestamps to trajectory
    for i in range(0, len(times), len(times)//10):  # Add ~10 time labels
        ax3.annotate(format_time(times[i]), (x_coords[i], y_coords[i]))
    
    # Save the plot
    fig.tight_layout()
    fig.savefig('grip_movement_analysis.png')
    print("Saved grip movement analysis to 'grip_movement_analysis.png'")
    
    # Show the plot
    plt.show()

def main():
    # For video file input
    cap = cv2.VideoCapture('videos/see_cam_hands.mp4')  # Replace with your video file
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate frame positions for 16:00 and 25:00
    start_time = 16 * 60  # 16 minutes in seconds
    end_time = 25 * 60    # 25 minutes in seconds
    
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    
    # Check if calculated end_frame exceeds total frames
    if end_frame > total_frames:
        end_frame = total_frames
        print(f"Warning: Video is shorter than 25:00. Will process until the end.")
    
    # Set the frame position to start_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame
    
    # Optional: save the processed video
    out = cv2.VideoWriter('videos/tracked_output.mp4', 
                         cv2.VideoWriter_fourcc(*'mp4v'), 
                         fps, (width, height))
    
    # Track coordinates over time for analysis
    grip_positions = []
    
    # CSV file for grip position data
    csv_file = open('grip_positions.csv', 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Timestamp', 'Time_Seconds', 'X_Position', 'Y_Position'])

    #print writing to grip positions.csv
    print("Writing grip positions to 'grip_positions.csv'")
    
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
            grip_positions.append((video_time, grip_x, grip_y))
            
            # Write to CSV
            csv_writer.writerow([timestamp, video_time, grip_x, grip_y])
        
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
    csv_file.close()
    
    print(f"Saved {len(grip_positions)} grip positions to 'grip_positions.csv'")
    
    # Create plots of grip movement
    if grip_positions:
        plot_grip_movements(grip_positions)
    else:
        print("No grip positions were detected in the tracking zone")

if __name__ == "__main__":
    main()