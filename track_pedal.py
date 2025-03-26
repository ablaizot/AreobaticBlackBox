import cv2
import numpy as np
import time
import csv
import os
import matplotlib.pyplot as plt
from datetime import timedelta

def format_time(seconds):
    """Convert seconds to MM:SS format"""
    return str(timedelta(seconds=int(seconds)))[2:7]  # Skip hours, get MM:SS

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

def track_blue_tape(image):
    """Track blue tape on a cable - only in top right region"""
    # Make a copy of the image to draw on
    annotated_image = image.copy()
    h, w, c = image.shape
    
    # Define region of interest (top right quadrant)
    roi_width = w // 2
    roi_height = h // 2
    roi = image[0:roi_height, roi_width:w]  # Changed to use right half
    
    # Draw ROI boundary on annotated image
    cv2.rectangle(annotated_image, (roi_width, 0), (w, roi_height), (255, 0, 0), 2)
    cv2.putText(annotated_image, "Tracking Zone", (roi_width + 10, roi_height - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    
    # Convert ROI to HSV for better color filtering
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Define range of blue color in HSV
    lower_blue = np.array([90, 100, 100])
    upper_blue = np.array([130, 255, 255])
    
    # Create a mask for blue color
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Apply morphological operations to clean up the mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Initialize tape coordinates
    tape_coords = None
    
    # If contours are found, find the largest one
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Only process if contour is large enough (to avoid noise)
        if cv2.contourArea(largest_contour) > 100:
            # Calculate centroid of the contour
            M = cv2.moments(largest_contour)
            if M['m00'] != 0:
                # Coordinates in ROI space
                cx_roi = int(M['m10'] / M['m00'])
                cy_roi = int(M['m01'] / M['m00'])
                
                # Convert ROI coordinates to original image coordinates
                cx = cx_roi + roi_width  # Add offset for right side
                cy = cy_roi
                
                # Draw a circle at the centroid
                cv2.circle(annotated_image, (cx, cy), 10, (0, 255, 255), -1)
                
                # Draw contour outline (need to shift contour to original image coordinates)
                # Create a copy of the contour with adjusted coordinates
                shifted_contour = largest_contour.copy()
                shifted_contour[:,:,0] += roi_width  # Shift x-coordinates
                cv2.drawContours(annotated_image, [shifted_contour], 0, (0, 255, 0), 2)
                
                # Save coordinates
                tape_coords = (cx, cy)
                
                # Display coordinates
                cv2.putText(annotated_image, f"Tape: ({cx}, {cy})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Show the mask in small window (for debugging)
    small_mask = cv2.resize(mask, (w//4, h//4))
    annotated_image[0:h//4, 3*w//4:w] = cv2.cvtColor(small_mask, cv2.COLOR_GRAY2BGR)
    cv2.putText(annotated_image, "Mask", (3*w//4 + 10, 15), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return annotated_image, tape_coords

def track_rectangle(image):
    """Track rectangular shapes in the top right region"""
    # Make a copy of the image to draw on
    annotated_image = image.copy()
    h, w, c = image.shape
    
    # Define region of interest (top right quadrant)
    roi_width = w // 2
    roi_height = h // 2
    roi = image[0:roi_height, roi_width:w]
    
    # Draw ROI boundary on annotated image
    cv2.rectangle(annotated_image, (roi_width, 0), (w, roi_height), (255, 0, 0), 2)
    cv2.putText(annotated_image, "Tracking Zone", (roi_width + 10, roi_height - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    
    # Convert ROI to grayscale for edge detection
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Blur the image to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply edge detection
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find contours in the edge image
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Initialize rectangle coordinates
    rect_coords = None
    
    # Filter contours to find rectangles
    for contour in contours:
        # Approximate contour to simplify shape
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Check if shape has 4 corners (rectangle)
        if len(approx) == 4:
            # Check if area is large enough to filter out noise
            area = cv2.contourArea(contour)
            if area > 200:  # Adjust this threshold based on your needs
                # Create shifted contour for drawing on the main image
                shifted_approx = approx.copy()
                shifted_approx[:,:,0] += roi_width  # Shift x-coordinates
                
                # Draw the rectangle outline
                cv2.drawContours(annotated_image, [shifted_approx], 0, (0, 255, 0), 2)
                
                # Calculate centroid of the rectangle
                M = cv2.moments(contour)
                if M['m00'] != 0:
                    cx_roi = int(M['m10'] / M['m00'])
                    cy_roi = int(M['m01'] / M['m00'])
                    
                    # Convert to full image coordinates
                    cx = cx_roi + roi_width
                    cy = cy_roi
                    
                    # Draw centroid
                    cv2.circle(annotated_image, (cx, cy), 10, (0, 255, 255), -1)
                    
                    # Get rectangle dimensions
                    rect = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    
                    # Get width and height
                    width = int(rect[1][0])
                    height = int(rect[1][1])
                    
                    # Save rectangle coordinates and dimensions
                    rect_coords = (cx, cy, width, height)
                    
                    # Display rectangle info
                    cv2.putText(annotated_image, f"Rect: ({cx}, {cy})", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(annotated_image, f"Size: {width}x{height}", 
                              (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
                    # We found a rectangle, no need to check other contours
                    break
    
    # Show the edge map in small window (for debugging) - moved to bottom left
    small_edges = cv2.resize(edges, (w//4, h//4))
    small_edges_colored = cv2.cvtColor(small_edges, cv2.COLOR_GRAY2BGR)
    annotated_image[3*h//4:h, 0:w//4] = small_edges_colored
    cv2.putText(annotated_image, "Edges", (10, 3*h//4 + 15), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return annotated_image, rect_coords

def plot_tape_movements(position_data):
    """Generate plots showing tape movement over time"""
    if not position_data:
        print("No position data to plot")
        return
    
    times = [t for t, _, _ in position_data]
    x_coords = [x for _, x, _ in position_data]
    y_coords = [y for _, _, y in position_data]
    
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
    ax3.set_title('Tape Position Trajectory')
    ax3.set_xlabel('X Position')
    ax3.set_ylabel('Y Position')
    ax3.grid(True)
    
    # Invert Y axis for more intuitive plotting (0 at top like screen coordinates)
    ax3.invert_yaxis()
    
    # Add timestamps to trajectory
    for i in range(0, len(times), len(times)//10):  # Add ~10 time labels
        ax3.annotate(format_time(times[i]), (x_coords[i], y_coords[i]))
    
    # Save the plot
    plot_output_path = get_incremented_filename('videos/pedal_movement_analysis.png')
    fig.tight_layout()
    fig.savefig(plot_output_path)
    print(f"Saved pedal movement analysis to '{plot_output_path}'")
    
    # Show the plot
    plt.show()

def main():
    # Create output directories
    os.makedirs('videos', exist_ok=True)
    
    # For video file input
    video_path = 'videos/demo_track_1.mp4'
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video file. Try entering the full path.")
        return
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Ask user for time range to process
    start_time = input("Enter start time in minutes (default: 0): ")
    start_time = float(start_time) * 60 if start_time else 0
    
    end_time = input("Enter end time in minutes (default: end of video): ")
    if end_time:
        end_time = float(end_time) * 60
    else:
        end_time = total_frames / fps
    
    start_frame = int(start_time * fps)
    end_frame = min(int(end_time * fps), total_frames)
    
    # Set the frame position to start_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame
    
    # Get incremented filenames for outputs
    video_output_path = get_incremented_filename('videos/tracked_pedal.mp4')
    csv_output_path = get_incremented_filename('videos/pedal_positions.csv')
    
    # Optional: save the processed video
    out = cv2.VideoWriter(video_output_path, 
                          cv2.VideoWriter_fourcc(*'mp4v'), 
                          fps, (width, height))
    
    # Track coordinates over time for analysis
    tape_positions = []
    
    # CSV file for position data
    csv_file = open(csv_output_path, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Timestamp', 'Time_Seconds', 'X_Position', 'Y_Position', 'Width', 'Height'])
    
    print(f"Processing frames from {start_time/60:.1f}:00 to {end_time/60:.1f}:00")
    print(f"Frame range: {start_frame} to {end_frame}")
    print(f"Video will be saved to: {video_output_path}")
    print(f"Position data will be saved to: {csv_output_path}")
    
    while cap.isOpened() and current_frame < end_frame:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame. Exiting...")
            break
            
        # Track rectangular shapes
        annotated_frame, rect_data = track_rectangle(frame)
        
        # Calculate current video time
        video_time = (current_frame / fps)
        minutes = video_time // 60
        seconds = video_time % 60
        timestamp = f"{int(minutes):02d}:{int(seconds):02d}"
        
        # Add timestamp to the frame
        cv2.putText(annotated_frame, f"Time: {timestamp}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Record position with timestamp if rectangle was detected
        if rect_data:
            x, y, width, height = rect_data
            tape_positions.append((video_time, x, y))
            
            # Write to CSV
            csv_writer.writerow([timestamp, video_time, x, y, width, height])
        
        # Write frame to output video
        out.write(annotated_frame)
        
        # Display the resulting frame
        cv2.imshow('Pedal Tracking', annotated_frame)
        
        # Increment the frame counter
        current_frame += 1
        
        # Show progress every 30 seconds of video
        if current_frame % (fps * 30) == 0:
            current_min = (current_frame / fps) // 60
            current_sec = (current_frame / fps) % 60
            print(f"Processed up to {int(current_min):02d}:{int(current_sec):02d}")
        
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
            break
            
    # Clean up
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    csv_file.close()
    
    print(f"Saved {len(tape_positions)} tape positions to '{csv_output_path}'")
    
    # Create plots of tape movement
    if tape_positions:
        plot_tape_movements(tape_positions)
    else:
        print("No tape positions were detected")

if __name__ == "__main__":
    main()