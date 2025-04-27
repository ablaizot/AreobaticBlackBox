import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.signal import butter, filtfilt

def create_throttle_animation_gif(csv_file_path, output_gif_path="throttle_animation.gif", filter_order=3, cutoff_frequency=2.0):
    """
    Generates an animated GIF from a CSV file, visualizing throttle values as a
    filling column.  The FPS is determined from the time data in the CSV file.

    Args:
        csv_file_path (str): Path to the CSV file.  The CSV should have a header.
            The first column should be 'time' (in seconds), and the second
            column should be 'throttle' with values between 0 and 1.
        output_gif_path (str, optional): Path to save the generated GIF.
            Defaults to "throttle_animation.gif".
        filter_order (int, optional): Order of the Butterworth filter.
            Higher values provide steeper roll-off. Defaults to 3.
        cutoff_frequency (float, optional): Cutoff frequency of the Butterworth
            filter in Hz.  Defaults to 2.0.
    """
    try:
        df = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {csv_file_path}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    if not all(col in df.columns for col in ['time', 'throttle']):
        print("Error: CSV file must contain columns named 'time' and 'throttle'.")
        return

    # Validate data
    if not pd.api.types.is_numeric_dtype(df['time']):
        print("Error: 'time' column must be numeric.")
        return
    if not pd.api.types.is_numeric_dtype(df['throttle']):
        print("Error: 'throttle' column must be numeric.")
        return
    if not ((df['throttle'] >= 0) & (df['throttle'] <= 1)).all():
        print("Error: 'throttle' column must contain values between 0 and 1.")
        return

    time_values = df['time'].values
    throttle_values = df['throttle'].values

    # Calculate FPS from the time data
    if len(time_values) > 1:
        fps = 1.0 / np.mean(np.diff(time_values))  # Average time difference
        print(f"Calculated FPS from time data: {fps:.2f}")
    else:
        fps = 30  # Default FPS if there's only one time value
        print("Warning: Only one time value found.  Using default FPS of 30.")

    # Apply Butterworth filter
    nyquist_freq = fps / 2.0
    if cutoff_frequency >= nyquist_freq:
        print("Error: Cutoff frequency must be less than Nyquist frequency (fps/2).")
        return
    normalized_cutoff = cutoff_frequency / nyquist_freq
    b, a = butter(filter_order, normalized_cutoff, btype='low')
    throttle_filtered = filtfilt(b, a, throttle_values)


    fig, ax = plt.subplots(figsize=(4, 6))  # Adjust figure size as needed
    ax.set_xlim(-0.5, 0.5)  # Set x-axis limits for the column
    ax.set_ylim(0, 1)      # Set y-axis limits (0 to 1 for percentage fill)
    ax.set_xticks([])       # Remove x-axis ticks
    ax.set_yticks([])       # Remove y-axis ticks
    ax.set_facecolor('lightgray')

    # Create the column (rectangle)
    throttle_column = plt.Rectangle((-0.25, 0), 0.5, 0, color='green', alpha=0.7)
    ax.add_patch(throttle_column)

    # Add labels
    throttle_label_text = ax.text(0, -0.05, 'Throttle', ha='center', va='top')
    max_throttle_label_text = ax.text(-0.7, 1.0, '% Max Throttle', ha='left', va='center', rotation=90)
    boundary_0_label_text = ax.text(-0.3, 0.0, '0', ha='right', va='center')
    boundary_1_label_text = ax.text(-0.3, 1.0, '1', ha='right', va='center')

    time_text = ax.text(0, 1.05, '', transform=ax.transAxes, ha='center', va='bottom') # Add time text


    def animate(i):
        throttle = throttle_filtered[i]
        time_value = time_values[i]
        throttle_column.set_height(throttle)
        time_text.set_text(f"Time: {time_value:.2f} s")
        return throttle_column, time_text

    ani = animation.FuncAnimation(fig, animate, frames=len(throttle_values),
                                  interval=1000 / fps, blit=True)

    try:
        ani.save(output_gif_path, writer='pillow', fps=fps)
        print(f"Successfully saved animation to {output_gif_path}")
        print(f"Note: The animation was saved with an FPS of {fps:.2f}.  If the animation appears to play in slow motion,\n"
              f"  please check the playback settings of your GIF viewer or web browser to ensure it is playing at the correct speed.")
    except Exception as e:
        print(f"Error saving GIF: {e}")
        return
    finally:
        plt.close(fig)

if __name__ == "__main__":
    # Example usage:
    csv_file = "throttle_flip_data.csv"  # Replace with your CSV file
    # Create dummy data
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"File not found at {csv_file}. Creating dummy data.")
        time_data = np.arange(0, 5, 0.01)
        throttle_data = np.linspace(0, 1, len(time_data)) # Linear throttle increase
        dummy_data = {'time': time_data, 'throttle': throttle_data}
        dummy_df = pd.DataFrame(dummy_data)
        dummy_df.to_csv(csv_file, index=False)

    create_throttle_animation_gif(csv_file_path=csv_file, output_gif_path="throttle_animation.gif", filter_order=3, cutoff_frequency=2.0)
    print("Done!")
