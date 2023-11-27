### Overview
This script is designed to facilitate Knative performance testing by updating configurations and executing tests based on specified environmental variables. It works with Knative YAML files and performs various actions such as updating configurations, running tests, and collecting metrics.

### Usage
1. **Environmental Variables:**
    - `SERVICE_YAML`: Path to the service YAML file.
    - `KPERF_CONFIG`: Path to the configuration file for kperf.
    - `OUTPUT_DIR`: Directory to save output files.
    - `LOAD_TESTING_BOOL`, `SCALE_TESTING_BOOL`, `FANS_TESTING_BOOL`: Boolean flags to enable specific types of testing.
    - `FANS_ITERATIONS`: Number of iterations for FANS (Find Average Number of Services) tests.
    - `KSERVICE_TARGET`: Concurrency limit for each pod.
    - `FANS_TESTING_GET_AVG_BOOL`: Boolean flag to get the average of averages of services in FANS tests.
    - `ENDPOINT_URL`: The Knative ingress-endpoint to sent HTTP requests

> You can set and configure those via `set-env.sh`

2. **Functions:**
    - `read_and_print_yaml(yaml_file)`: Reads and prints YAML files.
    - `execute_and_wait(command)`: Executes shell commands and logs output.
    - `add_value_to_deeply_nested_yaml(yaml_file, keys, value)`: Updates YAML values based on yaml-keys.
    - `delete_line_from_deeply_nested_yaml(yaml_file, keys)`: Deletes lines in deeply nested YAML based on yaml-keys.
    - `get_avg_of_svc_lat_per_subfolder(parent_dir)`: Calculates average service latencies per subfolder.

3. **Testing Phases:**
    - **Load Phase**: Tests service loads with various configurations.
    - **Scale Phase**: Performs scaling tests on services.
    - **FANS Phase**: Finds the average number of services responding.

4. **Execution:**
    - Ensure required environmental variables are set.
    - Run the script, specifying the desired testing phases using the boolean environmental variables.

### Important Notes
- Modify environmental variables and functions' parameters before executing to suit the testing requirements.
- Be cautious with file paths and configurations.
- Check the generated output files and directories as the script performs various operations that may create new files or directories.