import yaml

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

# Example usage:
yaml_file = "/home/plakic/playground/nubificus/kperf-metrics-scripts/service-example.yaml"  # Replace with the path to your YAML file
keys_to_delete = ["spec", "template", "spec", "runtimeClassName"]
delete_line_from_deeply_nested_yaml(yaml_file, keys_to_delete)