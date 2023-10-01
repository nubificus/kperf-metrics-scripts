import pandas as pd

# Script responsible 
# for counting the zero responses
# per (count of services,
# concurrency-step and container-runtime 

# Load the CSV-like dataset into a pandas DataFrame
df = pd.read_csv('/home/plakic/playground/nubificus/kperf-metrics-scripts/csv-metrics/load-output.csv')  # Replace 'your_dataset.csv' with the actual filename

# Extract the number from the first field after "ksvcs_"
df['count_ksvcs'] = df['File'].str.extract(r'ksvcs_(\d+)')

# Group the DataFrame by 'conc_step', 'cont_runtime', and 'ksvcs_number',
# then count the occurrences of [200] responses equal to 0
zero_200_response_count = df[df['[200] responses'] == 0].groupby(['conc_step', 'cont_runtime', 'count_ksvcs']).size().reset_index(name='count_no_resp')

print(zero_200_response_count)
