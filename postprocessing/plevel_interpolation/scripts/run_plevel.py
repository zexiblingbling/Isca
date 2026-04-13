from netCDF4 import Dataset  
from plevel_fn import plevel_call, daily_average, join_files, two_daily_average, monthly_average
import sys
import os
import time
import pdb
import subprocess

start_time=time.time()

# =================================================================

# --- CATCH ARGUMENTS FROM LOOPY.PY ---
if len(sys.argv) == 4:
    base_dir = sys.argv[1]
    out_dir = sys.argv[2]
    exp_name_list = [sys.argv[3]]
else:
    # Fallback if you run it manually
    base_dir = '/home/links/zs449/IscaData'
    out_dir = '/home/links/zs449/Test_Frierson/interpolated_data_redo'
    exp_name_list = ['frierson_test_experiment']

avg_or_daily_list=['daily'] 
start_file=25 
end_file=120 
nfiles=(end_file-start_file)+1

# ========================================================================
do_extra_averaging=False 
group_months_into_one_file=False 

# Restoring your golden setting
level_set='native25' 
mask_below_surface_set='-x ' #Default is to mask values that lie below the surface pressure when interpolated. 

plevs={}
var_names={}

if level_set=='standard':
    # Keeping original monthly/timestep/pentad/6hourly for reference
    plevs['monthly']=' -p "3 16 51 138 324 676 1000 1266 2162 3407 5014 6957 9185 10000 11627 14210 16864 19534 20000 22181 24783 27331 29830 32290 34731 37173 39637 42147 44725 47391 50164 53061 56100 59295 62661 66211 70000 73915 78095 82510 85000 87175 92104 97312"'
    plevs['timestep']=' -p "3 16 51 138 324 676 1000 1266 2162 3407 5014 6957 9185 10000 11627 14210 16864 19534 20000 22181 24783 27331 29830 32290 34731 37173 39637 42147 44725 47391 50164 53061 56100 59295 62661 66211 70000 73915 78095 82510 85000 87175 92104 97312"'
    plevs['pentad']=' -p "3 16 51 138 324 676 1000 1266 2162 3407 5014 6957 9185 10000 11627 14210 16864 19534 20000 22181 24783 27331 29830 32290 34731 37173 39637 42147 44725 47391 50164 53061 56100 59295 62661 66211 70000 73915 78095 82510 85000 87175 92104 97312"'
    plevs['6hourly']=' -p "1000 10000 25000 50000 85000 92500"'
    
    # CMIP-style 17 pressure levels for daily data
    plevs['daily']  =' -p "1000 2000 3000 5000 7000 10000 15000 20000 25000 30000 40000 50000 60000 70000 85000 92500 100000"'
    
    var_names['monthly']='-a slp height'
    var_names['pentad']='-a slp height'    
    var_names['timestep']='-a'
    var_names['6hourly']='ucomp slp height vor t_surf vcomp omega'
    var_names['daily']='ucomp slp height vor t_surf vcomp omega temp sphum'
    file_suffix='_interp_new_height_temp_not_below_ground'

elif level_set=='native25':
    var_names['daily']='ucomp slp height vor t_surf vcomp omega temp sphum'
    plevs['daily']=' -p "588 1572 2560 4003 6024 8736 12232 16566 21739 27692 34301 41389 48739 56111 63268 69995 76116 81506 86100 89884 92902 95239 97017 98378 99487 100000"'
    mask_below_surface_set='-x '
    file_suffix='_interp_native25'

elif level_set=='ssw_diagnostics':
    plevs['6hourly']=' -p "1000 10000"'
    var_names['monthly']='ucomp temp height'
    var_names['6hourly']='ucomp vcomp temp'
    file_suffix='_bl'
    
elif level_set=='tom_diagnostics':
    var_names['daily']='height temp'
    plevs['daily']=' -p "10 30 100 300 500 700 1000 3000 5000 7000 10000 15000 20000 25000 30000 40000 50000 60000 70000 75000 80000 85000 90000 95000 100000"'
    mask_below_surface_set=' '
    file_suffix='_tom_mk2'

for exp_name in exp_name_list:
    for n in range(nfiles):
        for avg_or_daily in avg_or_daily_list:
            print(f"\nProcessing run: {n+start_file}")

            number_prefix=''
            if n+start_file < 1000:
                number_prefix='0'
            if n+start_file < 100:
                number_prefix='00'
            if n+start_file < 10:
                number_prefix = '000'

            nc_file_in = base_dir+'/'+exp_name+'/run'+number_prefix+str(n+start_file)+'/atmos_'+avg_or_daily+'.nc'
            nc_file_out = out_dir+'/'+exp_name+'/run'+number_prefix+str(n+start_file)+'/atmos_'+avg_or_daily+file_suffix+'.nc'

            # Ensure the nested directory exists in your new out_dir before saving
            os.makedirs(os.path.dirname(nc_file_out), exist_ok=True)
            
            # ---> THE TRUE OVERWRITE ENFORCER <---
            if os.path.exists(nc_file_out):
                print(f"  [OVERWRITE] Deleting old file: {nc_file_out}")
                os.remove(nc_file_out)
            
            print(f"  [INTERPOLATING] Generating fresh data from {nc_file_in}...")
            plevel_call(nc_file_in, nc_file_out, var_names = var_names[avg_or_daily], p_levels = plevs[avg_or_daily], mask_below_surface_option=mask_below_surface_set)

            if do_extra_averaging and avg_or_daily=='6hourly':
                nc_file_out_daily = base_dir+'/'+exp_name+'/run'+str(n+start_file)+'/atmos_daily'+file_suffix+'.nc'
                daily_average(nc_file_out, nc_file_out_daily)
            
            if do_extra_averaging and avg_or_daily=='pentad':
                nc_file_out_daily = base_dir+'/'+exp_name+'/run'+str(n+start_file)+'/atmos_monthly'+file_suffix+'.nc'
                monthly_average(nc_file_out, nc_file_out_daily, adjust_time = True)                

if group_months_into_one_file:
    avg_or_daily_list_together=['daily']

    for exp_name in exp_name_list:
        for avg_or_daily in avg_or_daily_list_together:
            nc_file_string=''
            for n in range(nfiles):
                nc_file_in = out_dir+'/'+exp_name+'/run'+number_prefix+str(n+start_file)+'/atmos_'+avg_or_daily+file_suffix+'.nc'
                nc_file_string=nc_file_string+' '+nc_file_in
            
            # Join files into the out_dir instead of base_dir to keep raw data clean
            nc_file_out_joined = out_dir+'/'+exp_name+'/atmos_'+avg_or_daily+'_together'+file_suffix+'.nc'
            
            os.makedirs(os.path.dirname(nc_file_out_joined), exist_ok=True)
            
            if os.path.exists(nc_file_out_joined):
                os.remove(nc_file_out_joined)
                
            if not os.path.isfile(nc_file_out_joined):
                join_files(nc_file_string, nc_file_out_joined)

print('\nExecution time:', time.time()-start_time)