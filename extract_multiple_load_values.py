import re
import os
import csv

#Same as the single value...but for
#many services under a namespce...
#In that case kperf...produce a 
#hey output per service...

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
            slowest_matches = re.findall(slowest_pattern, script_text)
            fastest_matches = re.findall(fastest_pattern, script_text)
            average_matches = re.findall(average_pattern, script_text)
            requests_matches = re.findall(requests_pattern, script_text)
            status_code_200_matches = re.findall(status_code_200_pattern, script_text)
            status_code_404_matches = re.findall(status_code_404_pattern, script_text)

            values = {}

            if slowest_matches:
                values["Slowest"] = slowest_matches
            if fastest_matches:
                values["Fastest"] = fastest_matches
            if average_matches:
                values["Average"] = average_matches
            if requests_matches:
                values["Requests/sec"] = requests_matches
            
            # Extract "[200]" responses or set to 0 if not found
            values["[200] responses"] = status_code_200_matches if status_code_200_matches else [0]
            
            # Extract "[404]" responses or set to 0 if not found
            values["[404] responses"] = status_code_404_matches if status_code_404_matches else [0]

            return values
    except FileNotFoundError:
        return None

# Rest of your code remains the same...
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
        writer.writerows

            # Inside the loop that iterates through each file in the directory
        for filename in os.listdir(directory_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(directory_path, filename)
                extracted_values = extract_values_from_file(file_path)

                # Extract "conc_step" and "cont_runtime" from the file name
                conc_step_match = re.search(r"conc_step_(\d+)_", filename)
                cont_runtime_match = re.search(r"_([^_]+)_ksvc_loading", filename)

                if extracted_values and conc_step_match and cont_runtime_match:
                    # Iterate through the lists of values and write each set of values in a separate row
                    num_values = max(len(extracted_values["Slowest"]), len(extracted_values["Fastest"]), len(extracted_values["Average"]), len(extracted_values["Requests/sec"]))
                    
                    for i in range(num_values):
                        row = {
                            "File": filename,
                            "conc_step": conc_step_match.group(1),
                            "cont_runtime": cont_runtime_match.group(1),
                            "Slowest": extracted_values["Slowest"][i] if i < len(extracted_values["Slowest"]) else "",
                            "Fastest": extracted_values["Fastest"][i] if i < len(extracted_values["Fastest"]) else "",
                            "Average": extracted_values["Average"][i] if i < len(extracted_values["Average"]) else "",
                            "Requests/sec": extracted_values["Requests/sec"][i] if i < len(extracted_values["Requests/sec"]) else "",
                            "[200] responses": extracted_values["[200] responses"][i] if i < len(extracted_values["[200] responses"]) else 0,
                            "[404] responses": extracted_values["[404] responses"][i] if i < len(extracted_values["[404] responses"]) else 0,
                        }
                        writer.writerow(row)
                else:
                    print(f"Values not found in {filename} or the file does not exist.")

        print(f"Values have been written to {output_csv_path}.")
