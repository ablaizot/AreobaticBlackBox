import cv2
import os

def crop_video(input_video_path, output_video_path, x_start, y_start, crop_width, crop_height):
    """
    Crops a video to a specified rectangular region.

    Args:
        input_video_path (str): pedal_track1.mp4.
        output_video_path (str): Path to save the cropped video.
        x_start (int): Starting x-coordinate of the crop rectangle.
        y_start (int): Starting y-coordinate of the crop rectangle.
        crop_width (int): Width of the crop rectangle.
        crop_height (int): Height of the crop rectangle.
    """

    x_start = 1200
    y_start = 0
    crop_width = 400
    crop_height = 400

    # Open the input video
    cap = cv2.VideoCapture('pedal_track1.mp4')
    if not cap.isOpened():
        print(f"Error: Could not open video file: {'pedal_track1.mp4'}")
        return

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Validate crop region
    if x_start + crop_width > width or y_start + crop_height > height:
        print("Error: Crop region exceeds video boundaries.")
        cap.release()
        return

    # Define the codec and create a VideoWriter object for the output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' for .mp4 output
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (crop_width, crop_height))
    if not out.isOpened():
        print(f"Error: Could not create output video file: {output_video_path}")
        cap.release()
        return

    frame_count = 0
    start_time = time.time()
    print(f"Processing frames...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("End of video or error reading frame.")
            break

        # Crop the frame
        cropped_frame = frame[y_start:y_start + crop_height, x_start:x_start + crop_width]

        # Write the cropped frame to the output video
        out.write(cropped_frame)
        frame_count += 1
        
        if frame_count % 30 == 0:
            elapsed_time = time.time() - start_time
            print(f"Processed {frame_count} frames in {elapsed_time:.2f} seconds")

    # Release video capture and writer
    cap.release()
    out.release()

    print(f"Finished processing.  {frame_count} frames written to {output_video_path}")
    

if __name__ == "__main__":
    import time
    
    input_video = "pedal_track1.mp4"  # Replace with your input video file
    output_video = "cropped_video.mp4"  # Replace with your desired output video file name
    
    # Define the crop region.  These values should be integers.
    x_start = int(600)  # Starting x-coordinate
    y_start = int(0)  # Starting y-coordinate
    crop_width = int(300)  # Width of the cropped region
    crop_height = int(200) # Height of the cropped region
    
    if not os.path.exists(input_video):
        print(f"Error: Input video file not found at {input_video}")
    else:
        crop_video(input_video, output_video, x_start, y_start, crop_width, crop_height)
