import pandas as pd
import os

#A scrpit to "groupby"
#the output csv's 
#of the extact load-values 
# scipts.


# Read the CSV file
input_csv_path = '/home/plakic/playground/nubificus/kperf-metrics-scripts/csv-metrics/load-output.csv'  # Specify the path to your input CSV file
output_dir = '/home/plakic/playground/nubificus/kperf-metrics-scripts/csv-metrics'  # Specify the directory where grouped CSV files will be saved


if not os.path.exists(output_dir):
    os.makedirs(output_dir)

if not os.path.isfile(input_csv_path):
    print(f"Input CSV file not found at {input_csv_path}.")
else:
    # Read the CSV into a pandas DataFrame
    df = pd.read_csv(input_csv_path)

    # Group the data by the 'cont_runtime' column and concatenate the rows for each group
    grouped = df.groupby('conc_step').apply(lambda x: x.reset_index(drop=True))

    # Save the grouped data as a single CSV file
    output_csv_path = os.path.join(output_dir, 'grouped_output_conc_step.csv')
    grouped.to_csv(output_csv_path, index=False)
    print(f"Grouped data saved to {output_csv_path}.")