import csv
import os
import numpy as np # Import numpy for interpolation
import matplotlib.pyplot as plt # Import matplotlib for plotting


# Analog Values
    # RPM
    # Altitude
    # Airspeed
    # ailn ratio	
    # aileron deflection in ratio –1.0 (left) to +1.0 (right)
    # elev ratio
    # elevator deflection in ratio –1.- (nose down) to +1.0 (noseup)
    # rudd ratio	
    # rudder deflection in ratio –1.- (left) to +1.0 (right)
# Digital Values
    # GPS coordinates
    # Latitude
    # Longitude
    # Speed KIAS
    # Vertical Speed
    # pitch deg
    # roll deg	
    # hdng TRUE



def update_fdr_with_x_normalized(fdr_file, csv_file, output_fdr_file):
    """
    Update the 9th column of the .fdr file with x_normalized values from the CSV file,
    dynamically finding the header based on a 'DATA' marker, interpolating if necessary,
    plotting the comparison, and preserving the header.

    Args:
        fdr_file (str): Path to the original .fdr file.
        csv_file (str): Path to the CSV file containing x_normalized values.
        output_fdr_file (str): Path to save the modified .fdr file.
    """
    # Load x_normalized values from the CSV file
    x_normalized_str = []
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        if 'X_Position_Normalized' not in reader.fieldnames:
            raise ValueError("CSV file must contain an 'X_Position_Normalized' column.")
        for row in reader:
            val = row['X_Position_Normalized']
            if val: # Only append if not empty
                x_normalized_str.append(val)
            else:
                print(f"Warning: Found empty 'X_Position_Normalized' value in CSV row: {row}. Skipping this value.")

    # Read the .fdr file and find the 'DATA' marker
    header = []
    data_lines_raw = []
    data_start_index = -1
    with open(fdr_file, 'r') as fdr:
        fdr_lines = fdr.readlines()
        for i, line in enumerate(fdr_lines):
            # Check if the line starts with the word "DATA" after stripping whitespace
            if line.strip().startswith("DATA"):
                data_start_index = i
                break # Stop searching once found

        if data_start_index == -1:
            raise ValueError(f"Could not find a line starting with 'DATA' in {fdr_file}.")

        # Header is everything *up to and including* the DATA line
        header = fdr_lines[:data_start_index + 1]
        # Data lines are everything *after* the DATA line
        data_lines_raw = fdr_lines[data_start_index + 1:]
        # Process data lines (split by comma, strip whitespace)
        data_lines = [line.strip().split(',') for line in data_lines_raw if line.strip()] # Skip empty lines after DATA

    num_data_lines = len(data_lines)
    num_x_normalized = len(x_normalized_str)

    # Check if interpolation is needed
    if num_data_lines == 0:
        print("Warning: No data lines found after 'DATA' marker in the .fdr file. Output file will only contain the header.")
        x_normalized_final = [] # No data to update
    elif num_x_normalized == 0:
         print("Warning: No valid 'X_Position_Normalized' data found in the CSV. Cannot update column 9.")
         x_normalized_final = [''] * num_data_lines # Fill with empty strings
    elif num_data_lines != num_x_normalized:
        print(f"Warning: Row count mismatch: .fdr data ({num_data_lines}) vs x_normalized ({num_x_normalized}). Interpolating x_normalized data.")

        try:
            x_normalized_numeric = np.array([float(x) for x in x_normalized_str])
        except ValueError as e:
            problematic_values = [x for x in x_normalized_str if not x.replace('.', '', 1).replace('-','',1).isdigit()] # Allow negative floats
            raise ValueError(f"Could not convert all 'X_Position_Normalized' values to numbers for interpolation. Problematic values might include: {problematic_values[:5]}... Error: {e}")

        original_indices = np.linspace(0, num_data_lines - 1, num=num_x_normalized)
        target_indices = np.arange(num_data_lines)
        interpolated_x_numeric = np.interp(target_indices, original_indices, x_normalized_numeric)

        # --- Plotting ---
        plt.figure(figsize=(12, 6))
        plt.plot(original_indices, x_normalized_numeric, 'o', label='Original X_Normalized Data', markersize=5)
        plt.plot(target_indices, interpolated_x_numeric, '-', label='Interpolated X_Normalized Data', linewidth=2)
        plt.title('Original vs. Interpolated X_Position_Normalized')
        plt.xlabel('Target Index (FDR Data Row Number after DATA)')
        plt.ylabel('X_Position_Normalized Value')
        plt.legend()
        plt.grid(True)
        print("Displaying interpolation plot...")
        plt.show()
        # --- End Plotting ---

        x_normalized_final = [str(x) for x in interpolated_x_numeric]
    else:
        print("Row counts match. No interpolation needed.")
        x_normalized_final = x_normalized_str

    # Update the 9th column (index 8)
    indices = [7 ,8 ,9, 28]
    for x_pos_col_index in indices:
        for i, line in enumerate(data_lines):
            if len(line) <= x_pos_col_index:
                line.extend([''] * (x_pos_col_index - len(line) + 1))

            if i < len(x_normalized_final):
                line[x_pos_col_index] = x_normalized_final[i]

    for x_pos_col_index in [13, ]:
        for i, line in enumerate(data_lines):
            if len(line) <= x_pos_col_index:
                line.extend([''] * (x_pos_col_index - len(line) + 1))

            if i < len(x_normalized_final):
                line[x_pos_col_index] = x_normalized_final[i]
    


    # Write the updated .fdr file
    with open(output_fdr_file, 'w', newline='') as output_fdr:
        # Write the header (including the DATA line)
        output_fdr.writelines(header)
        # Write the updated data
        writer = csv.writer(output_fdr)
        writer.writerows(data_lines)

    print(f"Updated .fdr file saved to {output_fdr_file}")


def set_column_value(fdr_file, output_fdr_file, column_index, new_value):
    """
    Reads an .fdr file, finds the 'DATA' marker, and sets a specific
    value for all rows in a specified column index within the data section.

    Args:
        fdr_file (str): Path to the original .fdr file.
        output_fdr_file (str): Path to save the modified .fdr file.
        column_index (int): The 0-based index of the column to modify.
        new_value (str): The string value to set in the specified column.
    """
    # Read the .fdr file and find the 'DATA' marker
    header = []
    data_lines_raw = []
    data_start_index = -1
    try:
        with open(fdr_file, 'r') as fdr:
            fdr_lines = fdr.readlines()
            for i, line in enumerate(fdr_lines):
                # Check if the line starts with the word "DATA" after stripping whitespace
                if line.strip().startswith("DATA"):
                    data_start_index = i
                    break # Stop searching once found

            if data_start_index == -1:
                raise ValueError(f"Could not find a line starting with 'DATA' in {fdr_file}.")

            # Header is everything *up to and including* the DATA line
            header = fdr_lines[:data_start_index + 1]
            # Data lines are everything *after* the DATA line
            data_lines_raw = fdr_lines[data_start_index + 1:]
            # Process data lines (split by comma, strip whitespace)
            data_lines = [line.strip().split(',') for line in data_lines_raw if line.strip()] # Skip empty lines after DATA

    except FileNotFoundError:
        print(f"Error: Input FDR file not found at {fdr_file}")
        return
    except ValueError as e: # Catch the specific error for DATA marker
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Error reading FDR file: {e}")
        return

    num_data_lines = len(data_lines)

    if num_data_lines == 0:
        print("Warning: No data lines found after 'DATA' marker in the .fdr file. Output file will only contain the header.")
    else:
        print(f"Found {num_data_lines} data lines. Setting column {column_index + 1} (index {column_index}) to '{new_value}'.")

    # Update the target column
    for i, line in enumerate(data_lines):
        # Ensure the line has enough columns before trying to update
        if len(line) <= column_index:
            # Pad with empty strings up to the required index
            line.extend([''] * (column_index - len(line) + 1))

        # Assign the new value
        line[column_index] = str(new_value) # Ensure value is a string

    # Write the updated .fdr file
    try:
        with open(output_fdr_file, 'w', newline='') as output_fdr:
            # Write the header (including the DATA line)
            output_fdr.writelines(header)
            # Write the updated data
            writer = csv.writer(output_fdr)
            writer.writerows(data_lines)
        print(f"Updated .fdr file with column {column_index + 1} set to '{new_value}' saved to {output_fdr_file}")
    except Exception as e:
        print(f"Error writing output FDR file: {e}")


# Example usage
fdr_file = "C:/School/Senior_Desgin/FDR/Test_FDR_2.fdr"
csv_file = "C:/School/Senior_Desgin/FDR/tape_positions_normalized.csv"
output_fdr_file = "C:/School/Senior_Desgin/FDR/Test_FDR_2_test.fdr" # Updated output filename

update_fdr_with_x_normalized(fdr_file, csv_file, output_fdr_file)

# Example 1: Set column 7 (index 6, aileron ratio) to '0'
output_aileron_fixed = "C:/School/Senior_Desgin/FDR/Test_FDR_2_aileron_0.fdr"
set_column_value(output_fdr_file, output_fdr_file, column_index=13, new_value='250')

# Example 2: Set column 9 (index 8, rudder ratio) to '0.5'
output_rudder_fixed = "C:/School/Senior_Desgin/FDR/Test_FDR_2_rudder_0.5.fdr"
set_column_value(output_fdr_file, output_fdr_file, column_index=14, new_value='20')

# Example 3: Set column 1 (index 0, time secon) to 'RESET' (just as an example)
output_time_reset = "C:/School/Senior_Desgin/FDR/Test_FDR_2_time_reset.fdr"
set_column_value(output_fdr_file, output_fdr_file, column_index=69, new_value='7000')

set_column_value(output_fdr_file, output_fdr_file, column_index=70, new_value='7000')
set_column_value(output_fdr_file, output_fdr_file, column_index=67, new_value='0.8')

# time secon	time in seconds from the beginning of the recording	1.0
# temp deg C	temp in degrees celsius of the ambient air near the airplane at current altitude	45
# lon degre	longitude in degrees	–117.20
# lat degre	latitude in degrees	34.000
# h msl ft	height above mean sea level in TRUE feet, regardless of any barometric pressure setting or other errors	4010
# radio altft	radio altimeter indication	0
# ailn ratio	aileron deflection in ratio –1.0 (left) to +1.0 (right)	0
# elev ratio	elevator deflection in ratio –1.- (nose down) to +1.0 (nose up)	0
# rudd ratio	rudder deflection in ratio –1.- (left) to +1.0 (right)	0