import cv2
import os
import time

def crop_video(input_video_path, output_video_path):
    """
    Crops a video to its leftmost 80%.

    Args:
        input_video_path (str): Path to the input video file.
        output_video_path (str): Path to save the cropped video.
    """
    try:
        # Open the input video
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file: {input_video_path}")
            return

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Calculate the crop dimensions for the leftmost 70%
        x_start = 0
        y_start = 0
        crop_width = int(width * 0.7)
        crop_height = height

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
        

    except Exception as e:  # Added except block to catch the error
        print(f"An error occurred: {e}")
        return  # Added return to handle the error

if __name__ == "__main__":
    import time
    
    input_video = "leftright.mp4"  # Replace with your input video file
    output_video = "croppedleft.mp4"  # Replace with your desired output video file name
    
    if not os.path.exists(input_video):
        print(f"Error: Input video file not found at {input_video}")
    else:
        crop_video(input_video, output_video)
