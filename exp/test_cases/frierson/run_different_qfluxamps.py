"""
This wrapper script automates the execution of the Frierson test case 
across multiple ocean heat transport amplitudes (qflux_amp). For each 
amplitude, it dynamically updates the model namelist, runs the 20-month 
Isca simulation, and safely archives the final month's output (run0020) 
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
target_base_dir = "/home/links/zs449/Test_Frierson/Results_From_Different_qfluxamp"

def main():
    # 1. Locate the Isca data directory from the environment
    gfdl_data = os.environ.get("GFDL_DATA")
    if not gfdl_data:
        raise EnvironmentError(
            "The GFDL_DATA environment variable is not set. "
            "Isca Environment has to be activated to run this script."
        )

    # The 20th run will always be placed here by your original script
    source_run20_dir = os.path.join(gfdl_data, "frierson_test_experiment", "run0020")

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
        # This matches "'qflux_amp':" followed by any spacing and numbers/decimals
        new_content = re.sub(
            r"('qflux_amp'\s*:\s*)[0-9.]+", 
            rf"\g<1>{amp}", 
            script_content
        )
        
        # Write the modified content to a temporary script
        with open(temp_script, 'w') as file:
            file.write(new_content)
            
        # 4. Execute the temporary script
        # subprocess.run blocks the loop until all 20 months finish running
        subprocess.run(["python", temp_script], check=True)
        
        # 5. Define destination and copy the 20th run
        dest_folder_name = f"Run20_amp{amp}"
        dest_dir = os.path.join(target_base_dir, dest_folder_name)
        
        # If the destination already exists (from a past run), remove it to prevent copy errors
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
            
        print(f"\n---> Extraction: Copying month 20 data to {dest_dir}")
        shutil.copytree(source_run20_dir, dest_dir)
        
    # 6. Clean up the temporary execution script
    if os.path.exists(temp_script):
        os.remove(temp_script)
        
    print("\nAll simulations are complete! Your data is archived in:")
    print(target_base_dir)

    # 7. Clean up the leftover Isca data directory
    source_experiment_dir = os.path.join(gfdl_data, "frierson_test_experiment")
    if os.path.exists(source_experiment_dir):
        print(f"\n---> Cleanup: Removing residual data in {source_experiment_dir}")
        shutil.rmtree(source_experiment_dir)

if __name__ == "__main__":
    main()