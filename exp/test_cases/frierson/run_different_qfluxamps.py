import os
import subprocess

amplitudes = [0.3, 0.8, 1.6, 2.5]
runner_script = "frierson_test_case.py"

def main():
    print("Initiating Batch Job Submission via OS Environment...")
    
    for amp in amplitudes:
        print(f"\n--> Setting OS Environment ISCA_QFLUX_AMP = {amp}")
        
        # Inject the amplitude directly into the OS environment
        os.environ["ISCA_QFLUX_AMP"] = str(amp)
        
        # Execute the script (it will now securely read the OS environment)
        subprocess.run(["python", runner_script], check=True)
        
    print("\n==================================================")
    print("All simulations have been successfully queued!")
    print("Check your HPC queue to monitor their progress.")
    print("Output will appear in your Isca data directory under 'frierson_amp_X' folders.")

if __name__ == "__main__":
    main()