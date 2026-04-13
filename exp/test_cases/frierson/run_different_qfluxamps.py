"""
This wrapper script automates the execution of the Frierson test case 
across multiple ocean heat transport amplitudes (qflux_amp). For each 
amplitude, it dynamically updates the model namelist, runs the Isca simulation, 
and safely archives all monthly output starting from run 25 onwards 
to a distinct directory before the next iteration overwrites the data.
"""

import os
import re
import shutil
import subprocess

# --- Configuration ---
amplitudes = [0, 0.3, 0.7, 1.1, 1.5, 1.9, 2.3, 2.7]
original_script = "frierson_test_case.py"
temp_script = "temp_runner.py"
target_base_dir = "/home/links/zs449/Test_Frierson/Results_From_Different_qfluxamp/ALL"

def main():
    # 1. Locate the Isca data directory from the environment
    gfdl_data = os.environ.get("GFDL_DATA")
    if not gfdl_data:
        raise EnvironmentError(
            "The GFDL_DATA environment variable is not set. "
            "Isca Environment has to be activated to run this script."
        )

    # The master directory where Isca dumps the output for this experiment
    source_experiment_dir = os.path.join(gfdl_data, "frierson_test_experiment")

    # Ensure the master target directory exists
    os.makedirs(target_base_dir, exist_ok=True)

    # 2. Read your original script to act as a template
    with open(original_script, 'r') as file:
        script_content = file.read()

    # 3. Iterate through each required amplitude
    for amp in amplitudes:
        print(f"\n{'='*50}")
        print(f"Starting Isca sequence for qflux_amp = {amp}")
        print(f"{'='*50}")
        
        # Use regex to find the qflux_amp line and replace the number
        new_content = re.sub(
            r"('qflux_amp'\s*:\s*)[0-9.]+", 
            rf"\g<1>{amp}", 
            script_content
        )
        
        # Write the modified content to a temporary script
        with open(temp_script, 'w') as file:
            file.write(new_content)
            
        # 4. Execute the temporary script
        # subprocess.run blocks the loop until all months finish running
        subprocess.run(["python", temp_script], check=True)
        
        # 5. Define destination directory for this amplitude
        dest_folder_name = f"Runs25_onwards_amp{amp}"
        dest_dir = os.path.join(target_base_dir, dest_folder_name)
        
        # Clean destination if it exists from a previous aborted run
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        os.makedirs(dest_dir, exist_ok=True)
            
        print(f"\n---> Extraction: Scanning for data from run 25 onwards...")
        
        # Iterate through the Isca output directory
        found_data = False
        if os.path.exists(source_experiment_dir):
            for item in os.listdir(source_experiment_dir):
                # Look for directories named "run" followed by numbers
                if item.startswith("run") and item[3:].isdigit():
                    run_num = int(item[3:])
                    
                    # If the run number is 25 or greater, copy it
                    if run_num >= 25:
                        found_data = True
                        src_path = os.path.join(source_experiment_dir, item)
                        dst_path = os.path.join(dest_dir, item)
                        print(f"     Copying {item}...")
                        shutil.copytree(src_path, dst_path)
        
        if not found_data:
            print("     WARNING: No runs >= 25 were found to copy!")
            
    # 6. Clean up the temporary execution script
    if os.path.exists(temp_script):
        os.remove(temp_script)
        
    print("\nAll simulations are complete! Data is archived in:")
    print(target_base_dir)

    # 7. Clean up the leftover Isca data directory
    if os.path.exists(source_experiment_dir):
        print(f"\n---> Cleanup: Removing residual data in {source_experiment_dir}")
        shutil.rmtree(source_experiment_dir)

if __name__ == "__main__":
    main()