import yaml
import subprocess
import os
import time


"""
A script that based on env
will update values of kperf/config
and service yaml...and
will run the kperf tests
accordingly for every container-runtime
"""



#Get env

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
#Bool to enable find-max-num-of-pods tests
fmnp_env = os.environ.get('FMNP_TESTING_BOOL')
#Env responsible for setting the target(concurrency limit)
#of each pod
target_env = os.environ.get('KSERVICE_TARGET')

#Print envs
print("SERVICE_YAML:", service_yaml_file)
print("KPERF_CONFIG:", kperf_config_file)
print("OUTPUT_DIR:", output_dir)
print("LOAD_TESTING_BOOL:", load_env)
print("SCALE_TESTING_BOOL:", scale_env)
print("FMNP_TESTING_BOOL:", fmnp_env)
print("KSERVICE_TARGET:", target_env)


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

#Function to execute shell commands 
def execute_and_wait(command):
    try:
        completed_process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Print the command's exit status
        print(f"Command exit code: {completed_process.returncode}")

        # Print the command's standard output (stdout)
        print("Command output:")
        print(completed_process.stdout)

        # Print the command's standard error (stderr)
        print("Command error (if any):")
        print(completed_process.stderr)
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



#A function responsible for changing yaml value
#based on the list of "keys"
#e.g spec.template.spec.runtimeClassName="kata"
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

#List of concurrency step
concurrency_step_list = ["1","20","40","60","80","100"]

#List of container-runtimes
list_cont_runtime = ["","kata-qemu","kata-fc","kata-rs","kata-clh","urunc","gvisor"]

print(list_cont_runtime)

yaml_file = service_yaml_file
config_file = kperf_config_file
#print service yaml
read_and_print_yaml(yaml_file)

#keys for changing runtime in service yaml
key_list_service = ['spec','template','spec','runtimeClassName']
#keys for changing output dir in config yaml
key_list_config_output =['service','load','output']
#keys for changing concurrency output
key_list_config_concurrency =['service','load','load-concurrency']
#keys for changing the autoscaling-dev-target
key_list_config_target = ['spec', 'template', 'metadata','annotations','autoscaling.knative.dev/target']


#Change config  output_dir value
add_value_to_deeply_nested_yaml(kperf_config_file,key_list_config_output,output_dir)
time.sleep(2)
add_value_to_deeply_nested_yaml(yaml_file,key_list_config_target,target_env)


if(load_env and load_env.lower() == "true"):
    print("Start load phase")

    #For every concurrency step
    for conc in concurrency_step_list:
        print( "Set concurrency step to " +conc)
        add_value_to_deeply_nested_yaml(kperf_config_file,key_list_config_concurrency,conc)
        #export env for kperf-output-file nameing 
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
            command_to_run = "kubectl create ns ktest && kperf service generate"
            execute_and_wait(command_to_run)
            time.sleep(7)  # Wait for 7 seconds

            #Perform Load-teasting
            command_to_run = "kperf service load"
            execute_and_wait(command_to_run)
            time.sleep(7)  # Wait for 7 seconds

            #Delete ns
            command_to_run = "kubectl delete ns ktest"
            execute_and_wait(command_to_run)
            time.sleep(7)  # Wait for 7 seconds


if (scale_env and scale_env.lower() == "true"):
    print("Start scale phase")

    #for every runtime retrive metrics for loading
    for st in list_cont_runtime:
        print("Scale with "+st)

        #export env for kperf-output-file nameing 
        if(st == ""):
            os.environ['CONT_RUNTIME'] = "generic"
            delete_line_from_deeply_nested_yaml(yaml_file, key_list_service)
        else:
            os.environ['CONT_RUNTIME'] = st
            #Change service's yaml based on runtime
            add_value_to_deeply_nested_yaml(yaml_file, key_list_service, st)            



        #Create new ns and generate service
        command_to_run = "kubectl create ns ktest && kperf service generate"
        execute_and_wait(command_to_run)
        time.sleep(7)  # Wait for 7 seconds

        #Perform scale-teasting
        command_to_run = "GATEWAY_OVERRIDE=kourier-internal GATEWAY_NAMESPACE_OVERRIDE=kourier-system   kperf service scale --namespace ktest --svc-prefix ktest --range 0,1  --verbose --output "+ output_dir + " -i 35 -T 70s -s 10s"
        execute_and_wait(command_to_run)
        time.sleep(7)  # Wait for 7 seconds

        #Delete ns
        command_to_run = "kubectl delete ns ktest"
        execute_and_wait(command_to_run)
        time.sleep(7)  # Wait for 7 seconds

if (fmnp_env and fmnp_env.lower() == "true"):
    print("Start fmnp phase")

    #for every runtime retrive metrics for fnmp
    for st in list_cont_runtime:
        print("Find max-num-pods with "+st)

        #export env for kperf-output-file nameing 
        if(st == ""):
            os.environ['CONT_RUNTIME'] = "generic"
        else:
            os.environ['CONT_RUNTIME'] = st

        #Change service's yaml based on runtime
        add_value_to_deeply_nested_yaml(yaml_file, key_list_service, st)


        #Create new ns and generate service
        command_to_run = "kubectl create ns ktest && kperf service generate"
        execute_and_wait(command_to_run)
        time.sleep(7)  # Wait for 7 seconds

        #Perform fnmp-teasting
        command_to_run = "kperf service fnmp"
        execute_and_wait(command_to_run)
        time.sleep(7)  # Wait for 7 seconds

        #Delete ns
        command_to_run = "kubectl delete ns ktest"
        execute_and_wait(command_to_run)
        time.sleep(7)  # Wait for 7 seconds