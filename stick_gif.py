import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

def create_control_stick_animation(csv_file_path, output_gif_path="control_stick_animation.gif", fps=30):
    """
    Generates an animated GIF from a CSV file, visualizing the movement of a
    control stick.

    Args:
        csv_file_path (str): Path to the CSV file. The CSV should have a header.
            The first column should be 'time' (in seconds), the second 'x'
            (horizontal position), and the third 'y' (vertical position).
            X and Y values should be between 0 and 1.
        output_gif_path (str, optional): Path to save the generated GIF.
            Defaults to "control_stick_animation.gif".
        fps (int, optional): Frames per second of the animation. Defaults to 30.
    """
    try:
        df = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {csv_file_path}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    if not all(col in df.columns for col in ['time', 'x', 'y']):
        print("Error: CSV file must contain columns named 'time', 'x', and 'y'.")
        return

    # Validate data
    if not pd.api.types.is_numeric_dtype(df['time']):
        print("Error: 'time' column must be numeric.")
        return
    if not pd.api.types.is_numeric_dtype(df['x']):
        print("Error: 'x' column must be numeric.")
        return
    if not pd.api.types.is_numeric_dtype(df['y']):
        print("Error: 'y' column must be numeric.")
        return
    if not ((df['x'] >= 0) & (df['x'] <= 1)).all():
        print("Error: 'x' column must contain values between 0 and 1.")
        return
    if not ((df['y'] >= 0) & (df['y'] <= 1)).all():
        print("Error: 'y' column must contain values between 0 and 1.")
        return

    time_values = df['time'].values
    x_values = df['x'].values
    y_values = df['y'].values

    fig, ax = plt.subplots(figsize=(6, 6))  # Square plot for control stick
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("X Position")
    ax.set_ylabel("Y Position")
    ax.set_title("Control Stick Movement")

    # Draw the circle representing the control stick's range of motion
    circle = plt.Circle((0.5, 0.5), 0.5, color='gray', fill=False, linestyle='--')
    ax.add_patch(circle)

    # Initial position of the control stick
    stick_position, = ax.plot([x_values[0]], [y_values[0]], 'ro', markersize=10)  # Red circle
    time_text = ax.text(0.05, 1.05, f"Time: {time_values[0]:.2f} s", transform=ax.transAxes)

    # Add this line:
    stick_line, = ax.plot([0.5, x_values[0]], [0.5, y_values[0]], 'k-')  # Black line from center

    def animate(i):
        x = x_values[i]
        y = y_values[i]
        stick_position.set_data([x], [y])  # Update control stick position
        time_text.set_text(f"Time: {time_values[i]:.2f} s")
        # Update the line's data:
        stick_line.set_data([0.5, x], [0.5, y])
        return stick_position, time_text, stick_line  # Add stick_line to the return

    ani = animation.FuncAnimation(fig, animate, frames=len(time_values),
                                  interval=1000 / fps, blit=True)

    try:
        ani.save(output_gif_path, writer='pillow', fps=fps)
        print(f"Successfully saved animation to {output_gif_path}")
    except Exception as e:
        print(f"Error saving GIF: {e}")
        return
    finally:
        plt.close(fig)

if __name__ == "__main__":
    # Example usage:
    csv_file = "stick_flip_data.csv"  # Replace with your CSV file
    # Create a dummy data.csv
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"File not found at {csv_file}. Creating dummy data.")
        time_data = np.arange(0, 5, 0.1)
        x_data = 0.5 + 0.5 * np.sin(2 * np.pi * time_data)  # Sine wave for x
        y_data = 0.5 + 0.5 * np.cos(2 * np.pi * time_data)  # Cosine wave for y
        dummy_data = {'time': time_data, 'x': x_data, 'y': y_data}
        dummy_df = pd.DataFrame(dummy_data)
        dummy_df.to_csv(csv_file, index=False)

    create_control_stick_animation(csv_file_path=csv_file, output_gif_path="control_stick_animation.gif", fps=30)
    print("Done!")
