import os
import xarray as xr
from dask.diagnostics import ProgressBar

def open_nc(nc,timechunk=1,chunksize=1000):
    dts=xr.open_dataset(nc)
    key=list(dts.keys())[0]
    if 'time' in list(dts.dims.keys()):
        var=dts[key].chunk({"time": timechunk, "latitude": chunksize, "longitude": chunksize}) #.ffill("time")
    else:
        var=dts[key].chunk({"latitude": chunksize, "longitude": chunksize}) #.ffill("time")        
    return var,key

if __name__ == '__main__':
    aet_path = r'/home/mansoor/WA_data/WAPORWA/data/nc_v2/Riftvalley_AET_Wapor.nc'
    ret_path = r'/home/mansoor/WA_data/WAPORWA/data/nc_v2/Riftvalley_RET_WaPOR.nc'
    watermask_path = r'/home/mansoor/WA_data/WAPORWA/data/nc_v2/Riftvalley_WaterMask_ET.nc'
    
    aet, _ = open_nc(aet_path)
    ret, _ = open_nc(ret_path)
    mask, _ = open_nc(watermask_path)
    nw_mask = mask.squeeze('time')
    nw_mask = nw_mask.drop('time')
    nw_mask = nw_mask.expand_dims(time=aet.time)
    
    corrected_et = xr.where(nw_mask==1,ret*0.75,aet)
    
    ### Write netCDF files
    root_f = os.path.dirname(aet_path)    
    attrs={'units': 'mm/month', 'source': 'AET', 'quantity':'ET'}
    
    corrected_et.attrs=attrs
    corrected_et.name = 'AET'
    chunks=[1,900,900]
    comp = dict(zlib=True, complevel=9, least_significant_digit=2, chunksizes=chunks)
    print("\n\nwriting the Monthly corrected ET netcdf file using water mask\n\n")
    et_correct_nc = os.path.join(root_f,'corrected','Riftvalley_AET_Wapor.nc')
    encoding = {"AET": comp}
    with ProgressBar():
        corrected_et.to_netcdf(et_correct_nc, encoding=encoding)
