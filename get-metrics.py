import yaml
import subprocess
import os
import time
import re
import csv
from collections import defaultdict
import pandas as pd


"""
A script that based on env
will update values of kperf/config
and service yaml...and
will run the kperf tests
accordingly for every container-runtime
"""

#The service file which knative-service will be based on
service_yaml_file = os.environ.get('SERVICE_YAML')
#The config file of kperf holding the values that testing is based
kperf_config_file = os.environ.get('KPERF_CONFIG')
#The dir to save outputs
output_dir = os.environ.get('OUTPUT_DIR')
#Bool to enable loading tests
load_env = os.environ.get('LOAD_TESTING_BOOL')
#Bool to enable scale tests
scale_env = os.environ.get('SCALE_TESTING_BOOL')
#Bool to enable find-average-num-of-services(FANS) respond tests
fans_env = os.environ.get('FANS_TESTING_BOOL')
#Get number of iterations for FANS-tests
fans_iterations_env = os.environ.get('FANS_ITERATIONS')
#Env responsible for setting the target
# (concurrency limit) of each pod
target_env = os.environ.get('KSERVICE_TARGET')
#Bool to get averge of averages of services in 
#fans-test
get_avg_env = os.environ.get('FANS_TESTING_GET_AVG_BOOL')

#Print envs
print("SERVICE_YAML:", service_yaml_file)
print("KPERF_CONFIG:", kperf_config_file)
print("OUTPUT_DIR:", output_dir)
print("LOAD_TESTING_BOOL:", load_env)
print("SCALE_TESTING_BOOL:", scale_env)
print("FMNP_TESTING_BOOL:", fans_env)
print("KSERVICE_TARGET:", target_env)
print("FANS_ITERATIONS:",fans_iterations_env)
print("FANS_TESTING_GET_AVG_BOOL:",get_avg_env)

#Check fans iterations
if fans_iterations_env is not None and fans_iterations_env.isdigit():
    fans_iterations = int(fans_iterations_env)

#A function to count average number of csv-lines per subfolder
def count_lines_in_csv_files(folder_path):
    subfolder_averages = defaultdict(list)

    # Loop through all the files and subfolders in the specified folder
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        if os.path.isfile(item_path) and item.endswith('.csv'):
            total_lines = 0
            num_files = 0
            with open(item_path, 'r', newline='') as csv_file:
                csv_reader = csv.reader(csv_file)
                num_lines = sum(1 for row in csv_reader)-1
                total_lines += num_lines
                num_files += 1
            if num_files > 0:
                subfolder_averages[folder_path].append(total_lines / num_files)
        elif os.path.isdir(item_path):
            subfolder_averages.update(count_lines_in_csv_files(item_path))

    return subfolder_averages


#A function that reads and print yaml files
def read_and_print_yaml(yaml_file):
    try:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
            print(yaml.dump(data, default_flow_style=False))
    except FileNotFoundError:
        print(f"The file '{yaml_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def sanitize_filename(filename):
    # Remove characters that are not safe for filenames
    return re.sub(r'[^\w-]', '_', filename)

#Function to execute commands
def execute_and_wait(command):
    # Sanitize the command to create a safe filename
    sanitized_command = sanitize_filename(command)

    # Create a timestamp to make the file name unique
    timestamp = int(time.time())

    # Combine the sanitized command and timestamp to create a unique file name
    output_filename = f'/tmp/output_{sanitized_command}_{timestamp}.log'
    try:
        with open(output_filename, 'w') as log_file:
            completed_process = subprocess.run(command, shell=True, check=True, stdout=log_file, stderr=log_file, text=True)

        # Print the standard output and standard error to the console (stdout)
        print("Standard Output and Standard Error:")
        with open(output_filename, 'r') as log_file:
            for line in log_file:
                print(line, end='')

    except subprocess.CalledProcessError as e:
        print(f"Error executing the command: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


#A function to delete yaml lines 
def delete_line_from_deeply_nested_yaml(yaml_file, keys):
    try:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        # Create a function to recursively delete the line based on keys
        def delete_recursive(current_level, keys_to_delete):
            key = keys_to_delete[0]
            if key in current_level:
                if len(keys_to_delete) == 1:
                    del current_level[key]
                else:
                    delete_recursive(current_level[key], keys_to_delete[1:])

        delete_recursive(data, keys)

        with open(yaml_file, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)

        print(f"Deleted the line with keys: {keys} in '{yaml_file}'.")
    except FileNotFoundError:
        print(f"The file '{yaml_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")



# A function responsible for changing yaml value
# based on the list of "keys"
# e.g spec.template.spec.runtimeClassName="kata"
def add_value_to_deeply_nested_yaml(yaml_file, keys, value):
    try:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
        
        current_level = data
        for key in keys[:-1]:
            if key not in current_level:
                current_level[key] = {}
            current_level = current_level[key]

        current_level[keys[-1]] = value

        with open(yaml_file, 'w') as file:
            if(value==""):
                print("Probaly you should fix this stupid quick-fix, meant to force no")
            else:
                yaml.dump(data, file, default_flow_style=False)

        print(f"Added/Updated '{keys[-1]}' with value '{value}' in '{yaml_file}' under keys: {keys[:-1]}.")
    except FileNotFoundError:
        print(f"The file '{yaml_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Get avgerage os svc latencies per
# subfolder ... e.g subfolder cont_runtime_kata-fc_num_of_services_20
# containes mutiple csvs, one for each iteration,
# for each csv get average latency of services and
# then the average of average latencies
def get_avg_of_svc_lat_per_subfolder(parent_dir):
# Parent directory where subdirectories are located
    parent_directory = parent_dir

    # Define the pattern to match subdirectory names
    # Define the regex pattern to match subdirectory names
    pattern = r"cont_runtime_.*_num_of_services_.*"

    # Initialize variables to store the averages
    service_averages = {}
    subfolder_averages = []

    # List subdirectories matching the regex pattern
    matching_subdirectories = [d for d in os.listdir(parent_directory) if os.path.isdir(os.path.join(parent_directory, d)) and re.match(pattern, d)]

    print(matching_subdirectories)
    # Iterate through matching subdirectories
    for subfolder in matching_subdirectories:
        subfolder_path = os.path.join(parent_directory, subfolder)
        
        # Collect and calculate the averages for each subfolder
        subfolder_averages_temp = []
        
        for filename in os.listdir(subfolder_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(subfolder_path, filename)
                df = pd.read_csv(file_path)
                svc_avg = df['svc_latency_avg'].mean()
                subfolder_averages_temp.append(svc_avg)
        
        if subfolder_averages_temp:
            subfolder_average = sum(subfolder_averages_temp) / len(subfolder_averages_temp)
            str_num = str(len(subfolder_averages_temp))
            print("Subfolder "+subfolder+" has average "+ str(subfolder_average) + " for "+str_num+" subfolders")
            subfolder_averages.append(subfolder_average)

            # Write subfolder_average to a file
            output_file = os.path.join(subfolder_path, subfolder + "_average.txt")
            with open(output_file, "w") as f:
                f.write("Subfolder " + subfolder + " has average " + str(subfolder_average))

#List of concurrency step
#concurrency_step_list = ["1","20","40","60","80","100"]
concurrency_step_list = ["1"]

#List of number of services
#services_num_list =["1","20","40","60","80","100"]
#services_num_list =["25","50","75","100","125"]
#services_num_list =["100"]
#services_num_list =["500"]
services_num_list =["25","50","75","100","125"]

#List of container-runtimes
#list_cont_runtime = ["","kata-qemu","kata-fc","kata-rs","kata-clh","urunc","gvisor"]
#list_cont_runtime = ["","kata-qemu","kata-fc","gvisor"]
#list_cont_runtime=["","kata-qemu","gvisor","kata-fc"]

#list_cont_runtime = ["urunc"]
list_cont_runtime = ["kata-rs","kata-clh"]

print(list_cont_runtime)

yaml_file = service_yaml_file
config_file = kperf_config_file
#print service yaml
read_and_print_yaml(yaml_file)

#keys for changing runtime in service yaml
key_list_service = ['spec','template','spec','runtimeClassName']
#keys for changing load-output dir in config yaml
key_list_load_config_output =['service','load','output']
#keys for changing scale-output dir in config yaml
key_list_scale_config_output =['service','scale','output']
#keys for changing concurrency output
key_list_config_concurrency =['service','load','load-concurrency']
#keys for changing the autoscaling-dev-target
key_list_config_target = ['spec', 'template', 'metadata','annotations','autoscaling.knative.dev/target']
#keys for changing the number of services 
key_list_ksvc_num = ['service','generate','number']
#keys for changing the load-range of affected services
key_list_load_ksvc_range = ['service','load','range']
#keys for changing the scale-range of affected services
key_list_scale_ksvc_range = ['service','scale','range']


#Change config output_dir  value for load
add_value_to_deeply_nested_yaml(kperf_config_file,key_list_load_config_output,output_dir)
time.sleep(2)
add_value_to_deeply_nested_yaml(kperf_config_file,key_list_scale_config_output,output_dir)
time.sleep(2)
#Change target value in config
add_value_to_deeply_nested_yaml(yaml_file,key_list_config_target,target_env)



if(load_env and load_env.lower() == "true"):
    print("Start load phase")

    #For every number of services to be generated:
    for ksvc_num in services_num_list:
        print("Set service num step to "+ksvc_num)
        add_value_to_deeply_nested_yaml(kperf_config_file,key_list_ksvc_num,ksvc_num)
        #export env for number of ksvc-s
        os.environ['NUM_OF_KSVCs']= ksvc_num
        time.sleep(4)

        if(len(services_num_list)>= 1 ):
            largest_num_of_range = ksvc_num
            if(int(ksvc_num)!=1): 
                print("Set range in load section ..load range 0,"+str(int(largest_num_of_range)-1))
                add_value_to_deeply_nested_yaml(kperf_config_file,key_list_load_ksvc_range,"0,"+str(int(largest_num_of_range)-1))
                time.sleep(4)
            else:
                print("Set range in load section ..load range 0,1)")
                add_value_to_deeply_nested_yaml(kperf_config_file,key_list_load_ksvc_range,"0,1")
                time.sleep(4)
        
        

        #For every concurrency step
        for conc in concurrency_step_list:
            print( "Set concurrency step to " +conc)
            add_value_to_deeply_nested_yaml(kperf_config_file,key_list_config_concurrency,conc)
            #export env for kperf-output-file naming 
            os.environ['CONCURRENCY_STEP']=conc
            time.sleep(4)


            #For every runtime retrive metrics for loading
            for st in list_cont_runtime:
                print("Load with "+st)
                #export env for kperf-output-file nameing 
                if(st == ""):
                    os.environ['CONT_RUNTIME'] = "generic"
                    #Change service's yaml based on runtime
                    delete_line_from_deeply_nested_yaml(yaml_file, key_list_service)

                else:
                    os.environ['CONT_RUNTIME'] = st
                    #Change service's yaml based on runtime
                    add_value_to_deeply_nested_yaml(yaml_file, key_list_service, st)


                #Create new ns and generate service
                command_to_run = "kubectl create ns ktest &&  taskset -c 0,32,1,33,2,34,3,35 kperf service generate"
                execute_and_wait(command_to_run)
                print("Executeted \"create ns and kperf service generation\" ")
                time.sleep(7)  # Wait for 7 seconds

                #Perform Load-teasting
                command_to_run = "taskset -c  0,32,1,33,2,34,3,35 kperf service load"
                execute_and_wait(command_to_run)
                print("Executeted \"kperf service load\" ")
                time.sleep(7)  # Wait for 7 seconds

                #Delete ns
                command_to_run = "kubectl delete ns ktest"
                execute_and_wait(command_to_run)
                print("Executeted \"delete ns\" ")
                time.sleep(7)  # Wait for 7 seconds


if (scale_env and scale_env.lower() == "true"):
    print("Start scale phase")


    #For every number of services to be generated:
    for ksvc_num in services_num_list:
        print("Set service num step to "+ksvc_num)
        add_value_to_deeply_nested_yaml(kperf_config_file,key_list_ksvc_num,ksvc_num)
        #export env for number of ksvc-s
        os.environ['NUM_OF_KSVCs']= ksvc_num
        time.sleep(4)

        if(len(services_num_list)>= 1 ):
            largest_num_of_range = ksvc_num
            if(int(ksvc_num)!=1): 
                print("Set range in scale section ..scale range 0,"+str(int(largest_num_of_range)-1))
                add_value_to_deeply_nested_yaml(kperf_config_file,key_list_scale_ksvc_range,"0,"+str(int(largest_num_of_range)-1))
                time.sleep(4)
            else:
                print("Set range in scale section ..scale range 0,1)")
                add_value_to_deeply_nested_yaml(kperf_config_file,key_list_scale_ksvc_range,"0,1")
                time.sleep(4)
        


        #for every runtime retrieve metrics for loading
        for st in list_cont_runtime:
            print("Scale with "+st)

            #export env for kperf-output-file naming 
            if(st == ""):
                os.environ['CONT_RUNTIME'] = "generic"
                delete_line_from_deeply_nested_yaml(yaml_file, key_list_service)
            else:
                os.environ['CONT_RUNTIME'] = st
                #Change service's yaml based on runtime
                add_value_to_deeply_nested_yaml(yaml_file, key_list_service, st)            


            #Create new ns and generate service
            command_to_run = "kubectl create ns ktest && taskset -c 0,32,1,33,2,34,3,35 kperf service generate"
            execute_and_wait(command_to_run)
            print("Executeted \"create ns and kperf service generation\" ")
            time.sleep(7)  # Wait for 7 seconds

            #Perform scale-testing
            command_to_run = "GATEWAY_OVERRIDE=kourier-internal GATEWAY_NAMESPACE_OVERRIDE=kourier-system  taskset -c 0,32,1,33,2,34,3,35 kperf service scale"
            execute_and_wait(command_to_run)
            print("Executeted \"kperf service scale\" ")
            time.sleep(7)  # Wait for 7 seconds

            #Delete ns
            command_to_run = "kubectl delete ns ktest"
            execute_and_wait(command_to_run)
            print("Executeted \"kperf delete ns ktest\" ")
            time.sleep(7)  # Wait for 7 seconds


# Find the average number of services respond
if (fans_env and fans_env.lower() == "true"):
    print("Find average-number-of-services-respond phase")

    # Define the parent directory path
    parent_dir = output_dir

    # Define the name of the new directory you want to create
    new_dir_name = "fans-test"

    # Create the full path for the new directory
    fans_tests_path = os.path.join(parent_dir, new_dir_name)

    # Check if the parent directory exists, and create the new directory if it doesn't
    if not os.path.exists(fans_tests_path):
        os.makedirs(fans_tests_path)
        print(f"Directory '{new_dir_name}' created inside '{parent_dir}'.")
    else:
        print(f"Directory '{new_dir_name}' already exists inside '{parent_dir}'.")
    

    #Start iterating
    for i in range(fans_iterations):
        print(f"Iteration {i + 1}")

        #For every number of services to be generated:
        for ksvc_num in services_num_list:
            print("Set service num step to "+ksvc_num)
            add_value_to_deeply_nested_yaml(kperf_config_file,key_list_ksvc_num,ksvc_num)
            #export env for number of ksvc-s
            os.environ['NUM_OF_KSVCs']= ksvc_num
            time.sleep(4)

            if(len(services_num_list)>= 1 ):
                largest_num_of_range = ksvc_num
                if(int(ksvc_num)!=1): 
                    print("Set range in scale section ..scale range 0,"+str(int(largest_num_of_range)-1))
                    add_value_to_deeply_nested_yaml(kperf_config_file,key_list_scale_ksvc_range,"0,"+str(int(largest_num_of_range)-1))
                    time.sleep(4)
                else:
                    print("Set range in scale section ..scale range 0,1)")
                    add_value_to_deeply_nested_yaml(kperf_config_file,key_list_scale_ksvc_range,"0,1")
                    time.sleep(4)
            
            #for every runtime retrieve metrics for loading
            for st in list_cont_runtime:
                print("Scale with "+st)

                #export env for kperf-output-file naming 
                if(st == ""):
                    os.environ['CONT_RUNTIME'] = "generic"
                    delete_line_from_deeply_nested_yaml(yaml_file, key_list_service)
                else:
                    os.environ['CONT_RUNTIME'] = st
                    #Change service's yaml based on runtime
                    add_value_to_deeply_nested_yaml(yaml_file, key_list_service, st)            

                #Create new-subdir for every ...
                # Define the parent directory path
                parent_dir = fans_tests_path

                # Defin the name of the new directory you want to create
                new_dir_name = "cont_runtime_"+st+"_num_of_services_"+ksvc_num

                # Create the full path for the new directory
                fans_cont_range_sub_path = os.path.join(parent_dir, new_dir_name)

                # Check if the parent directory exists, and create the new directory if it doesn't
                if not os.path.exists(fans_cont_range_sub_path):
                    os.makedirs(fans_cont_range_sub_path)
                    print(f"Directory '{new_dir_name}' created inside '{parent_dir}'.")
                else:
                    print(f"Directory '{new_dir_name}' already exists inside '{parent_dir}'.")


                #Change config output_dir value
                add_value_to_deeply_nested_yaml(kperf_config_file,key_list_scale_config_output,fans_cont_range_sub_path)
                time.sleep(2)            

                #Create new ns and generate service
                command_to_run = "kubectl create ns ktest &&  taskset -c 0,32,1,33,2,34,3,35 kperf service generate"
                execute_and_wait(command_to_run)
                print("Executeted \"create ns and kperf service generation\" ")
                time.sleep(7)  # Wait for 7 seconds

                #Perform scale-testing
                command_to_run = "GATEWAY_OVERRIDE=kourier-internal GATEWAY_NAMESPACE_OVERRIDE=kourier-system  taskset  -c 0,32,1,33,2,34,3,35 kperf service scale"
                execute_and_wait(command_to_run)
                print("Executeted \"kperf service scale\" ")
                time.sleep(7)  # Wait for 7 seconds

                #Delete ns
                command_to_run = "kubectl delete ns ktest"
                execute_and_wait(command_to_run)
                print("Executeted \"kperf delete ns ktest\" ")
                time.sleep(7)  # Wait for 7 seconds


    parent_folder = fans_tests_path
    output_file = fans_tests_path+"/"+'output.txt'  

    subfolder_averages = count_lines_in_csv_files(parent_folder)

    # Calculate the average for each subfolder
    # Write the output to a file
    with open(output_file, 'w') as output:
        for folder, averages in subfolder_averages.items():
            output.write(f"Subfolder: {folder}\n")
            if averages:
                average_lines = sum(averages) / len(averages)
                output.write(f"Total lines across {len(averages)} CSV files: {sum(averages)}\n")
                output.write(f"Average lines per CSV file: {average_lines:.2f}\n\n")
                print(f"Subfolder: {folder}")
                print(f"Total lines across {len(averages)} CSV files: {sum(averages)}")
                print(f"Average lines per CSV file: {average_lines:.2f}\n")
            else:
                output.write(f"No CSV files found in subfolder: {folder}\n\n")
                print(f"No CSV files found in subfolder: {folder}\n")        

        print("Output has been written to", output_file)

    if (get_avg_env):
        get_avg_of_svc_lat_per_subfolder(fans_tests_path)