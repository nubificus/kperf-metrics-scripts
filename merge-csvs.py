import os
import glob
import pandas as pd

"""
A pyhton script to merge *.csv files
based on the different outputs of kperf.

For every cont_runtime  and "testing" process
(load,scale,find-max-num-pods) there is a 
unique csv holding the results.

Using regex will merge all container-runtimes output
of one testing process.

e.g
  
kata_qemu_ksvc_loading_time-1.csv  
kata_clh_ksvc_loading_time-1.csv ---> merged-load-metrics.csv
gvisor_ksvc_loading_time_3.csv


kata_qemu_ksvc_scaling_time-1.csv  
kata_clh_ksvc_scaling_time-1.csv ---> merged-scale-metrics.csv
gvisor_ksvc_scaling_time_3.csv

"""


# Define a function to merge CSV files and add the "cont_runtime" column
def merge_and_add_cont_runtime(files, substrings):
    # Initialize an empty DataFrame to store the merged data
    merged_data = pd.DataFrame()

    # Iterate through the list of CSV files and concatenate them into the merged_data DataFrame
    for file in files:
        df = pd.read_csv(file)
        # Check if any of the substrings are present in the file name
        matching_substring = next((substring for substring in substrings if substring in file), None)
        
        if matching_substring:
            # If a matching substring is found, add the "cont_runtime" column with the matching substring value
            df['cont_runtime'] = matching_substring
        else:
            # If no matching substring is found, set "cont_runtime" to None or any desired default value
            df['cont_runtime'] = None
        
        merged_data = pd.concat([df, merged_data], ignore_index=True)
    #Add cont_runtime column
    merged_data = merged_data[['cont_runtime'] + [col for col in merged_data.columns if col != 'cont_runtime']]


    return merged_data

# Define the list of substrings
substrings_to_search = ["kata-qemu", "kata-clh","kata-rs","kata-fc", "urunc"]

# Specify the directory and file pattern
directory =  os.environ.get("CSV_RES_DIR")

pattern_scale = '*ksvc_scaling_time*.csv'
pattern_fmnp = '*ksvc*max_pods*.csv'
pattern_load = '*ksvc_loading_time*.csv'
patterns = [pattern_scale,pattern_load]

##For scale

csv_files = glob.glob(os.path.join(directory, pattern_scale))

# Call the merge_and_add_cont_runtime function with the list of CSV files and substrings
# for the scaling metrics
merged_data = merge_and_add_cont_runtime(csv_files, substrings_to_search)

# Optionally, save the merged data to a new CSV file
merged_data.to_csv(directory +'/'+'merged-scale-metrics.csv', index=False)


##For load 

csv_files = glob.glob(os.path.join(directory, pattern_load))

# Call the merge_and_add_cont_runtime function with the list of CSV files and substrings
# for the scaling metrics
merged_data = merge_and_add_cont_runtime(csv_files, substrings_to_search)

# Optionally, save the merged data to a new CSV file
merged_data.to_csv(directory +'/'+'merged-load-metrics.csv', index=False)


##For load 

csv_files = glob.glob(os.path.join(directory, pattern_load))

# Call the merge_and_add_cont_runtime function with the list of CSV files and substrings
# for the scaling metrics
merged_data = merge_and_add_cont_runtime(csv_files, substrings_to_search)

# Optionally, save the merged data to a new CSV file
merged_data.to_csv(directory +'/'+'merged-load-metrics.csv', index=False)


##For fmnp

csv_files = glob.glob(os.path.join(directory, pattern_fmnp))

# Call the merge_and_add_cont_runtime function with the list of CSV files and substrings
# for the scaling metrics
merged_data = merge_and_add_cont_runtime(csv_files, substrings_to_search)

# Optionally, save the merged data to a new CSV file
merged_data.to_csv(directory +'/'+'merged-fmnp-metrics.csv', index=False)