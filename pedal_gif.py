import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import io
import base64
from PIL import Image
from scipy.signal import butter, filtfilt

def create_animated_columns_gif(csv_file_path, output_gif_path="animated_columns.gif", filter_order=3, cutoff_frequency=2.0):
    """
    Generates an animated GIF from a CSV file, visualizing positive and negative
    decimal values as filling columns.  Applies a Butterworth filter to smooth
    the data and calculates FPS from the time data in the CSV file.

    Args:
        csv_file_path (str): Path to the CSV file.  The CSV should have a header.
            The first column should be 'time' (in seconds), and the second
            column should contain decimal values between -1 and 1.
        output_gif_path (str, optional): Path to save the generated GIF.
            Defaults to "animated_columns.gif".
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

    if not all(col in df.columns for col in ['time', 'value']):
        print("Error: CSV file must contain columns named 'time' and 'value'.")
        return

    # Validate data
    if not pd.api.types.is_numeric_dtype(df['time']):
        print("Error: 'time' column must be numeric.")
        return
    if not pd.api.types.is_numeric_dtype(df['value']):
        print("Error: 'value' column must be numeric.")
        return
    if not ((df['value'] >= -1) & (df['value'] <= 1)).all():
        print("Error: 'value' column must contain values between -1 and 1.")
        return

    time_values = df['time'].values
    decimal_values = df['value'].values

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
    decimal_filtered = filtfilt(b, a, decimal_values)

    fig, ax = plt.subplots(figsize=(8, 6))  # Adjust figure size as needed
    ax.set_xlim(-1.5, 1.5)  # Set x-axis limits for the two columns
    ax.set_ylim(0, 1)      # Set y-axis limits (0 to 1 for percentage fill)
    ax.set_xticks([])       # Remove x-axis ticks
    ax.set_yticks([])       # Remove y-axis ticks
    ax.set_facecolor('lightgray')  # Set background color

    # Create the two columns (rectangles)
    left_column = plt.Rectangle((-1, 0), 0.5, 0, color='red', alpha=0.7)
    right_column = plt.Rectangle((0.5, 0), 0.5, 0, color='blue', alpha=0.7)
    ax.add_patch(left_column)
    ax.add_patch(right_column)

    time_text = ax.text(0, 1.05, '', transform=ax.transAxes, ha='center', va='bottom') # Add time text

    # Add labels below the columns
    left_label_text = ax.text(-1, -0.05, 'Left Pedal', ha='center', va='top')
    right_label_text = ax.text(1, -0.05, 'Right Pedal', ha='center', va='top')


    def animate(i):
        decimal = decimal_filtered[i]
        time_value = time_values[i]

        time_text.set_text(f"Time: {time_value:.2f} s")  # Update time text

        if decimal > 0:
            left_column.set_height(0)  # Reset left column
            right_column.set_height(decimal)
        else:
            left_column.set_height(abs(decimal))
            right_column.set_height(0)  # Reset right column
        return left_column, right_column, time_text  # Include time_text in the return

    ani = animation.FuncAnimation(fig, animate, frames=len(decimal_values),
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
        plt.close(fig)  # Close the figure to free memory

if __name__ == "__main__":
    # Example usage:
    csv_file = "pedal_flip_data.csv" # Replace with your CSV file
    # Create a dummy data.csv if it does not exist
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"File not found at {csv_file}. Creating dummy data.")
        time_data = np.arange(0, 5, 0.01)
        throttle_data = np.linspace(0, 1, len(time_data)) # Linear throttle increase
        dummy_data = {'time': time_data, 'throttle': throttle_data}
        dummy_df = pd.DataFrame(dummy_data)
        dummy_df.to_csv(csv_file, index=False)

    create_animated_columns_gif(csv_file_path=csv_file, output_gif_path="animated_columns.gif",  filter_order=3, cutoff_frequency=2.0)
    print("Done!")
