"""
loopy.py: Automated Batch Interpolator for Isca Q-Flux Experiments

Description:
This script automates the vertical pressure-level interpolation of Isca output 
across multiple ocean q-flux amplitudes. It serves as a dynamic wrapper for 
'run_plevel.py'. 

It includes a live 'tqdm' progress bar that actively monitors the standard output 
of the subprocess to track exactly which file is being interpolated in real-time.

Author: Zexi, Mar 2026
"""

import os
import sys
import subprocess
try:
    from tqdm import tqdm
except ImportError:
    print("Error: The 'tqdm' library is required for the progress bar.")
    print("Please install it using: pip install tqdm")
    sys.exit(1)

# --- Configuration ---
amplitudes = [0, 0.8, 1.6, 2.5] # should match with run_different_qfluxamps.py
run_start = 25
run_end = 120

# Point input directly to the raw Isca data directory
input_root = "/home/links/zs449/IscaData"
output_root = "/home/links/zs449/Test_Frierson/interpolated_different_qfluxes"
plevel_script = "/home/links/zs449/Isca/postprocessing/plevel_interpolation/scripts/run_plevel.py"

def main():
    print("==================================================")
    print("Initiating Batch Interpolation (loopy.py)")
    print("==================================================\n")
    
    os.makedirs(output_root, exist_ok=True)
    
    # Calculate exactly how many files we are processing for the progress bar
    runs_per_amp = (run_end - run_start) + 1
    total_files = len(amplitudes) * runs_per_amp
    
    # Initialize the master progress bar
    with tqdm(total=total_files, desc="Overall Progress", unit="file", colour="green") as pbar:
        
        for amp in amplitudes:
            current_base_dir = f"{input_root}/Runs25_onwards_amp{amp}"
            current_out_dir = f"{output_root}/amp{amp}"
            
            if not os.path.isdir(current_base_dir):
                # If a directory is missing, update the progress bar to skip those files
                pbar.write(f"[WARNING] Missing directory: {current_base_dir}. Skipping amp {amp}.")
                pbar.update(runs_per_amp)
                continue
                
            os.makedirs(current_out_dir, exist_ok=True)
            exp_name = "" 
            
            command = ["python", plevel_script, current_base_dir, current_out_dir, exp_name]
            
            # Use Popen instead of run() so we can read the output line-by-line LIVE
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1 # Line buffered
            )
            
            # Listen to the output of run_plevel.py in real-time
            for line in process.stdout:
                # Every time the child script prints "Processing run:", tick the bar!
                if "Processing run:" in line:
                    pbar.update(1)
                    # Update the text next to the bar so you know exactly what it's doing
                    run_num = line.strip().split()[-1]
                    pbar.set_postfix_str(f"Amp: {amp} | Run: {run_num}")
                elif "execution time" in line.lower():
                    # Ignore the final timing printout from the sub-script
                    continue
            
            # Wait for the subprocess to formally close and check for crashes
            process.wait()
            if process.returncode != 0:
                pbar.write(f"\n[ERROR] run_plevel.py crashed during amplitude {amp}.")
                pbar.write("Halting batch process.")
                break 

    print("\n==================================================")
    print("Batch interpolation safely completed!")
    print("==================================================")

if __name__ == "__main__":
    main()