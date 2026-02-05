# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 09:27:54 2020

Process LAI to monthly 
Get n rainy days from daily rainfall
Calculate vegetation cover
Calculate interception

𝑉𝑒𝑔_𝑐𝑜𝑣𝑒𝑟(𝑖,𝑡)=1−𝑒^((−0.5∗𝐿𝐴𝐼(𝑖,𝑡)))
𝐼(𝑖,𝑡)=𝐿𝐴𝐼(𝑖,𝑡)*n∗(1−1/(1+𝑃(𝑖,𝑡)⁄𝑛∗𝑉𝑒𝑔_𝑐𝑜𝑣𝑒𝑟(𝑖,𝑡)*1 ⁄𝐿𝐴𝐼(𝑖,𝑡) ) )


@author: cmi001
"""

import numpy as np
import os
import glob
import pandas as pd
try:
    import gdal
except:
    from osgeo import gdal
import calendar
from createNC_cmi import make_netcdf
import netCDF4 as nc
from dask.diagnostics import ProgressBar
import xarray as xr
import warnings
import dask
dask.config.set(scheduler='synchronous')


def open_nc(nc_file, chunksize="auto"):
    dts=xr.open_dataset(nc_file)
    key=list(dts.keys())[0]
    # print(key)
    var=dts[key].chunk({"time": 1, "latitude": chunksize, "longitude": chunksize}) #.ffill("time")
    return var,key


def open_nct(nc_file):
    dts=xr.open_dataset(nc_file)
    key=list(dts.keys())[0]
    # print(key)
    var=dts[key].chunk({"time": 100, "latitude": 100, "longitude": 100}) #.ffill("time")
    return var,key

def rainy_days(dailyp_nc, monthlyp_nc):
    
    p, _ = open_nc(dailyp_nc)
    p_m, _ = open_nc(monthlyp_nc)
    
    # Create a binary array indicating rainy days (1) and non-rainy days (0)
    pbinary = xr.where(p > 0, 1, 0)  # Consider any precipitation above 0 as a rainy day
    
    # Resample the binary array to monthly frequency and sum to get the number of rainy days per month
    # Using groupby instead of resample to avoid pandas 2.2 incompatibility with older xarray
    # nrainy = pbinary.resample(time='1M').sum(dim='time', skipna=False)

    # Create a monthly identifier (YYYY-MM)
    month_year = pbinary['time'].dt.strftime('%Y-%m')
    # Assign it as a coordinate
    pbinary = pbinary.assign_coords(month_year=month_year)
    # Group by this new coordinate and sum
    nrainy = pbinary.groupby('month_year').sum(dim='time', skipna=False)

    # The result has 'month_year' as dimension. We need to restore 'time' dimension matching p_m
    # We can assume the order aligns if sorted, or use reindexing logic more carefully.
    # p_m is monthly precipitation. We want nrainy to have the same time coords.

    # Map the 'month_year' strings back to the timestamps in p_m
    # This assumes p_m has one entry per month and covers the same period

    # Let's verify overlap
    common_times = []

    # If p_m.time is proper datetime, we can format it too
    pm_months = p_m['time'].dt.strftime('%Y-%m')

    # Reindex nrainy to align with p_m's months
    nrainy = nrainy.rename({'month_year': 'time'}) # Temporary rename for alignment logic if needed, but indices are strings vs dates

    # Actually, easiest is to assign the values of nrainy to a new DataArray shaped like p_m
    # Create a mapping from month_year string to nrainy value

    # Better approach: Reconstruct the time coordinate
    # nrainy currently indexed by strings '2020-01', '2020-02'...

    # Convert nrainy (indexed by string YYYY-MM) to use the timestamps from p_m that match

    # Filter p_m to those present in nrainy
    pm_valid = p_m.sel(time=p_m['time'].dt.strftime('%Y-%m').isin(nrainy['month_year']))

    # We can try to just swap the coordinate if lengths match exactly, but safer to reindex
    # However, since we are doing `nrainy.reindex(time = p_m.time, method = 'nearest')` later,
    # we just need nrainy to have a time dimension with compatible timestamps.

    # Let's build a new time index for nrainy based on the first day of the month string?
    # Or simpler:
    # 1. Group pbinary by YYYY-MM
    # 2. Sum
    # 3. Assign the time coordinate of the first occurrence in that group? Or just use p_m's time if aligned?

    # Workaround: xarray resample failure is due to '1M'. '1MS' (Month Start) might work if supported, or 'ME'.
    # But usually 'base' arg error is deep.

    # Let's try '1MS' first? No, likely same code path.
    # Manual groupby is safest.

    # Recover timestamps: parse YYYY-MM string to datetime (1st of month)
    # nrainy.month_year is the coordinate.

    dates = pd.to_datetime(nrainy['month_year'].values)
    nrainy = nrainy.assign_coords(time=dates).swap_dims({'month_year': 'time'}).drop('month_year')

    # Ensure the time coordinates of 'nrainy' and 'p_monthly' match
    nrainy = nrainy.reindex(time = p_m.time, method = 'nearest')  # or method='ffill', 'bfill', etc. as needed
    p_one = p_m * 0 + 1
    nrainy_correct = p_one.where((nrainy == 0) & (p_m>0),nrainy)
   
    ### Write netCDF files
    root_f = os.path.dirname(dailyp_nc)
    attrs={"units":"None", "source": "GPM", "quantity":"n rainy days"}
#    nrainy.attrs=attrs
    nrainy_correct.attrs=attrs
#    nrainy.name = 'nRD'
    nrainy_correct.name = 'nRD'
    chunks = [1,300,300]
    comp = dict(zlib=True, chunksizes=chunks, dtype = 'int16')
    # comp = dict(zlib=True, complevel=9, dtype = 'int16')
    
    print("\n\nwriting the Monthly RD netcdf file\n\n")
    nrainy_nc = os.path.join(root_f,'nRD_monthly.nc')
    encoding = {"nRD": comp}
    with ProgressBar():
        nrainy_correct.to_netcdf(nrainy_nc, encoding=encoding)
#        nrainy.to_netcdf(nrainy_nc, encoding=encoding)
    return nrainy_nc    
    

def lai_to_monthly(lai_nc, lu_nc):
    """
    

    Parameters
    ----------
    lai_nc : TYPE
        DESCRIPTION.

    Returns
    -------
    lai_mo_nc : TYPE
        DESCRIPTION.

    """
    lai_8d, _ = open_nct(lai_nc)
    
    # lai_mo = lai_8d.resample(time='1M', label='left',loffset='D').median()
    # Manual groupby to avoid compatibility issues
    month_year = lai_8d['time'].dt.strftime('%Y-%m')
    lai_8d = lai_8d.assign_coords(month_year=month_year)
    lai_mo = lai_8d.groupby('month_year').median(dim='time')

    # Recover time coordinate
    dates = pd.to_datetime(lai_mo['month_year'].values)
    lai_mo = lai_mo.assign_coords(time=dates).swap_dims({'month_year': 'time'}).drop('month_year')
    
    ### Write netCDF files
    root_f = os.path.dirname(lai_nc)
    attrs={"units":"None", "source": "MODIS", "quantity":"LAI"}
    lai_mo.attrs=attrs
    lai_mo.name = 'LAI'

    comp = dict(zlib=True, complevel=9, dtype = 'f8')
    print("\n\nwriting the Monthly LAI netcdf file\n\n")
    lai_mo_nc = os.path.join(root_f,'lai_monthly.nc')
    encoding = {"LAI": comp}
    with ProgressBar():
        lai_mo.to_netcdf(lai_mo_nc, encoding=encoding)        
    return lai_mo_nc

def interception(lai_nc, p_nc, n_nc):
    """
    

    Parameters
    ----------
    lai_nc : TYPE
        DESCRIPTION.
    p_nc : TYPE
        DESCRIPTION.
    n_nc : TYPE
        DESCRIPTION.

    Returns
    -------
    i_nc : TYPE
        DESCRIPTION.

    """
    
    lai, _ = open_nc(lai_nc)
    p, _ = open_nc(p_nc)
    n, _ = open_nc(n_nc)
    
    veg_cov = 1 - np.exp(-lai/2)
    
    interception = lai * (1 - 1/(1 + p/n*veg_cov/lai)) * n
    interception = interception.where(lai>0, 0)
    interception = interception.where(n>0, 0)
    interception = interception.where(p>0, 0)
    ### Write netCDF files
    root_f = os.path.dirname(lai_nc)
    attrs={"units":"mm/month", "source": "Calculation", "quantity":"I"}
    interception.attrs=attrs
    interception.name = 'I'
    
    chunks = [1,300,300]
    comp = dict(zlib=True, chunksizes=chunks, dtype = 'f8')
    # comp = dict(zlib=True, complevel=9, dtype = 'f8')
    print("\n\nwriting the Monthly I netcdf file\n\n")
    i_nc = os.path.join(root_f,'i_monthly.nc')
    encoding = {"I": comp}
    with ProgressBar():
        interception.to_netcdf(i_nc, encoding=encoding)        
    return i_nc    
    
    
    
