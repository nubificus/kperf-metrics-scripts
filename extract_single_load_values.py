import re
import os
import csv

#A script responsible for collecting and re-representing
#the output of kperf's load test.
#The resault csv will contain metrics such as 
#Slowest,Fastest and averge response times as well
#as the error response number

def extract_values_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            script_text = file.read()
            # Define regular expression patterns to match the values
            slowest_pattern = r"Slowest:\s+(\d+\.\d+)\s+secs"
            fastest_pattern = r"Fastest:\s+(\d+\.\d+)\s+secs"
            average_pattern = r"Average:\s+(\d+\.\d+)\s+secs"
            requests_pattern = r"Requests/sec:\s+(\d+\.\d+)"
            status_code_200_pattern = r"\[200\]\s+(\d+) responses"
            status_code_404_pattern = r"\[404\]\s+(\d+) responses"

            # Search for the patterns in the file contents
            slowest_match = re.search(slowest_pattern, script_text)
            fastest_match = re.search(fastest_pattern, script_text)
            average_match = re.search(average_pattern, script_text)
            requests_match = re.search(requests_pattern, script_text)
            status_code_200_match = re.search(status_code_200_pattern, script_text)
            status_code_404_match = re.search(status_code_404_pattern, script_text)

            values = {}

            if slowest_match:
                values["Slowest"] = slowest_match.group(1)
            if fastest_match:
                values["Fastest"] = fastest_match.group(1)
            if average_match:
                values["Average"] = average_match.group(1)
            if requests_match:
                values["Requests/sec"] = requests_match.group(1)
            
            # Extract "[200]" responses or set to 0 if not found
            values["[200] responses"] = status_code_200_match.group(1) if status_code_200_match else 0
            
            # Extract "[404]" responses or set to 0 if not found
            values["[404] responses"] = status_code_404_match.group(1) if status_code_404_match else 0

            return values
    except FileNotFoundError:
        return None

# Read the directory path and CSV path from environment variables
directory_path = "/home/plakic/playground/nubificus/kperf-metrics-scripts/load-txts"
output_csv_path = "/home/plakic/playground/nubificus/kperf-metrics-scripts/csv-metrics/load-output.csv"

if not directory_path or not output_csv_path:
    print("Please set the DIRECTORY_PATH and OUTPUT_CSV_PATH environment variables.")
else:
    # Create a CSV file and write the header
    with open(output_csv_path, 'w', newline='') as csv_file:
        fieldnames = [ "File", "conc_step", "cont_runtime", "Slowest", "Fastest", "Average", "Requests/sec","[200] responses", "[404] responses"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        # Iterate through each file in the directory
        for filename in os.listdir(directory_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(directory_path, filename)
                extracted_values = extract_values_from_file(file_path)

                # Extract "conc_step" and "cont_runtime" from the file name
                conc_step_match = re.search(r"conc_step_(\d+)_", filename)
                cont_runtime_match = re.search(r"_([^_]+)_ksvc_loading", filename)

                if extracted_values and conc_step_match and cont_runtime_match:
                    row = {
                        "File": filename,
                        "conc_step": conc_step_match.group(1),
                        "cont_runtime": cont_runtime_match.group(1),
                        **extracted_values
                    }
                    writer.writerow(row)
                else:
                    print(f"Values not found in {filename} or the file does not exist.")

    print(f"Values have been written to {output_csv_path}.")
