import csv
import os
import numpy as np # Import numpy for interpolation
import matplotlib.pyplot as plt # Import matplotlib for plotting

# Define the number of decimal places for interpolated values
INTERPOLATED_DECIMAL_PLACES = 6

def update_fdr_with_x_normalized(fdr_file, csv_file, output_fdr_file):
    """
    Update specified columns of the .fdr file with x_normalized values from the CSV file,
    dynamically finding the header based on a 'DATA' marker, interpolating if necessary,
    plotting the comparison, preserving the header, and limiting decimal places.

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
    except ValueError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Error reading FDR file: {e}")
        return


    num_data_lines = len(data_lines)
    num_x_normalized = len(x_normalized_str)

    # Check if interpolation is needed
    if num_data_lines == 0:
        print("Warning: No data lines found after 'DATA' marker in the .fdr file. Output file will only contain the header.")
        x_normalized_final = [] # No data to update
    elif num_x_normalized == 0:
         print("Warning: No valid 'X_Position_Normalized' data found in the CSV. Cannot update target columns.")
         # If we proceed, the target columns won't be updated correctly unless padded later
         # Decide if you want to stop or proceed with empty values
         x_normalized_final = [''] * num_data_lines # Fill with empty strings for padding consistency
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

        # Convert interpolated values back to string with limited decimal places
        x_normalized_final = [f"{x:.{INTERPOLATED_DECIMAL_PLACES}f}" for x in interpolated_x_numeric]
    else:
        print("Row counts match. No interpolation needed.")
        # Optionally format original data too if consistency is needed
        try:
            x_normalized_final = [f"{float(x):.{INTERPOLATED_DECIMAL_PLACES}f}" for x in x_normalized_str]
        except ValueError:
             print("Warning: Could not format original X_Position_Normalized values to fixed decimals. Using original strings.")
             x_normalized_final = x_normalized_str


    # Update the specified columns (indices are 0-based)
    # Columns 8, 9, 10 (indices 7, 8, 9) and Column 29 (index 28)
    # Column 14 (index 13)
    target_indices_to_update = [7, 8, 9, 13, 28]
    max_target_index = max(target_indices_to_update) if target_indices_to_update else -1

    if not x_normalized_final:
         print("Warning: No final x_normalized data available to update columns.")
    else:
        print(f"Updating columns at indices: {target_indices_to_update}")
        for i, line in enumerate(data_lines):
            # Ensure line is long enough for the highest index we need to write to
            if len(line) <= max_target_index:
                line.extend([''] * (max_target_index - len(line) + 1))

            # Get the corresponding value (original or interpolated)
            # Use modulo in case x_normalized_final became shorter unexpectedly, though it shouldn't
            value_to_write = x_normalized_final[i % len(x_normalized_final)]

            # Write the value to all target columns for the current row
            for col_index in target_indices_to_update:
                line[col_index] = value_to_write


    # Write the updated .fdr file
    try:
        with open(output_fdr_file, 'w', newline='') as output_fdr:
            # Write the header (including the DATA line)
            output_fdr.writelines(header)
            # Write the updated data
            writer = csv.writer(output_fdr)
            writer.writerows(data_lines)
        print(f"Updated .fdr file saved to {output_fdr_file}")
    except Exception as e:
        print(f"Error writing output FDR file: {e}")


# --- set_column_value function remains the same ---
def set_column_value(fdr_file, output_fdr_file, column_index, new_value, increment=0):
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
        
        new_value = str(float(new_value) + increment*i)
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


# --- Example Usage ---
fdr_file = "C:/School/Senior_Desgin/FDR/Test_FDR_2.fdr"
csv_file = "C:/School/Senior_Desgin/FDR/tape_positions_normalized.csv"
# Output file from the first step
output_fdr_step1 = "C:/School/Senior_Desgin/FDR/Test_FDR_2_normalized_updated.fdr"
# Final output file after setting other columns
final_output_fdr = "C:/School/Senior_Desgin/FDR/Test_FDR_2_final_modified.fdr"

# Step 1: Update columns with normalized/interpolated data (limited decimals)
update_fdr_with_x_normalized(fdr_file, csv_file, output_fdr_step1)

# Step 2: Set fixed values for other columns using the output from Step 1 as input
# Note: We write the final output to 'final_output_fdr' in the last call.
# Intermediate calls overwrite the output_fdr_step1 file.
set_column_value(output_fdr_step1, output_fdr_step1, column_index=13, new_value='250') # Overwrites output_fdr_step1
set_column_value(output_fdr_step1, output_fdr_step1, column_index=15, new_value='20')  # Overwrites output_fdr_step1
set_column_value(output_fdr_step1, output_fdr_step1, column_index=69, new_value='7000') # Overwrites output_fdr_step1
set_column_value(output_fdr_step1, output_fdr_step1, column_index=68, new_value='7000') # Overwrites output_fdr_step1
set_column_value(output_fdr_step1, output_fdr_step1, column_index=5, new_value='200', increment=0.01) # Overwrites output_fdr_step1

# Last call writes to the final destination file
set_column_value(output_fdr_step1, final_output_fdr, column_index=67, new_value='0.8')

print(f"--- Processing complete. Final file saved to: {final_output_fdr} ---")