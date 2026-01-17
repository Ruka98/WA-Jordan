# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 11:01:05 2020

@author: cmi001
"""

# %% netCDF files from
import os
import glob
import sys

sys.path.append(r'/efs/CWA/scripts')
import  createNC_cmi
import time

start = time.time()

basedir = r"/efs/CWA/rs_input_tifs"

pathP = os.path.join(basedir,'P', 'Monthly')
pathPday = os.path.join(basedir,'P', 'Daily')
pathET = os.path.join(basedir,'ET', 'MOD16')
# pathETref = os.path.join(basedir,'ETref')
pathLU = os.path.join(basedir,'luwa')
pathProbaV = os.path.join(basedir,'NDM')
pathLAI = os.path.join(basedir, 'LAI')
pathSMsat = os.path.join(basedir,'ThetaSat')
pathwatermask = os.path.join(basedir,'wofs_filter2')

template = r"/efs/CWA/static_datasets/template/L1_LCC_21_Resample_1km_correct_nodata.tif"

shp_path = r"/efs/CWA/static_datasets/shapefile/Africa_adm0_buffer.shp"
save_location = r"/efs/CWA/netcdf_files"


name = 'Africa'

datasets = {
                      # 'P'      :   [pathP, 
                      #            ('time','latitude', 'longitude'), 
                      #                  {'units': 'mm/month', 'source': 'CHIRPS', 'quantity':'P'}],
                    # 'dailyP' :   [pathPday,
                    #               ('time','latitude', 'longitude'), 
                    #               {'units': 'mm/d', 'source': 'CHIRPS', 'quantity':'dailyP'}],
                    #  'ET'     :   [pathET, 
                    #                ('time','latitude', 'longitude'), 
                    #                {'units': 'mm/month', 'source': 'MOD16', 'quantity':'ETa'}],                 
                    # 'LAI'    :   [pathLAI,
                    #               ('time','latitude', 'longitude'), 
                    #               {'units': 'None', 'source': 'MOD15', 'quantity':'LAI'}],                   
                    # 'SMsat'  :   [pathSMsat,
                    #               ('time','latitude', 'longitude'), 
                    #               {'units': 'None', 'source': 'HiHydroSoils', 'quantity':'SMsat'}],
                    #  'LU'     :   [pathLU,
                    #                ('time','latitude', 'longitude'), 
                    #                {'units': 'None', 'source': 'WA', 'quantity':'LU'}],
                    # 'ProbaV'  :   [pathProbaV,
                    #               ('time','latitude', 'longitude'), 
                    #               {'units': 'None', 'source': 'ProbaV', 'quantity':'DMP'}],
                    # 'ETref'  :   [pathETref,
                    #               ('time','latitude', 'longitude'), 
                    #               {'units': 'None', 'source': 'WA', 'quantity':'ETref'}],
                     'wofs'  :   [pathwatermask,
                                  ('time','latitude', 'longitude'), 
                                  {'units': 'None', 'source': 'DEA', 'quantity':'WOFS'}]
  
          }

nc_files = []

for d in datasets:
    filesAll = glob.glob(os.path.join(datasets[d][0],'*.tif'))
    dataset = {d: datasets[d]}
    fname = name+'_'+datasets[d][2]['quantity']+'_'+ datasets[d][2]['source']+'.nc'
    nc_file = os.path.join(save_location, fname)
    nc_files.append(nc_file)
    succes = createNC_cmi.make_netcdf(nc_file, dataset, shp_path, template, name)
    
end = time.time()
print('\n',end - start)

# %% prepare additional data for running SMBalance
# import os
# import glob

# os.chdir(r'/home/iwmi-wa/CWAPlus/scripts')

# import pre_proc_sm_balance

# nc_files = glob.glob(r'/home/iwmi-wa/CWAPlus/netcdf_files/*.nc')

# dailyp_nc = nc_files[3]
# p_nc = nc_files[1]
# n_nc = pre_proc_sm_balance.rainy_days(dailyp_nc, p_nc)

# lai_nc = nc_files[2]
# i_nc = pre_proc_sm_balance.interception(lai_nc, p_nc, n_nc)
