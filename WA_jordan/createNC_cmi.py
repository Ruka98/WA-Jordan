# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 09:18:47 2019

@author: bec
"""
import netCDF4
try:
    import gdal
    import ogr
    import osr
except:
    from osgeo import ogr
    from osgeo import gdal
    from osgeo import osr
import numpy as np
import glob
import os
import datetime
import itertools
import csv
import tempfile
import gzip
import shutil
import zipfile
import calendar
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
#from find_possible_dates import find_possible_dates
#from find_possible_dates import find_possible_dates_full

# os.environ['PROJ_LIB'] = 'C:\Anaconda3\\envs\\wa_collect_env\\Library\\share\\proj'
# os.environ['GDAL_DATA'] = 'C:\Anaconda3\\envs\\wa_collect_env\\Library\\share'

def check_projection(old_path):
    
    ds=gdal.Open(old_path)
    prj=ds.GetProjection()
    ds = None
    
    if len(prj) == 0:
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        path = tempfile.NamedTemporaryFile(suffix='.vrt').name
        gdal.Translate(path, old_path, outputSRS = srs)
    else:
        path = old_path

    return path
    
def select_files(folder, possible_formats = ['.tif', '.zip', '.gz', '.nc']):
    """
    Search a folder for files with extensions defined by 'possible_formats'
    and return a list of files with the most frequent occuring extension. If
    multiple extensions are present inside the folder with equal frequency, the
    returned extension is chosen arbitraraly (and a message is printed).
    """
    search = os.path.join(folder, "*")
    formats = np.unique([os.path.splitext(x)[1] for x in glob.glob(search)], return_counts = True)
    
    maxi = np.max([y for x, y in zip(formats[0], formats[1]) if x in possible_formats])
    
    form = formats[0][formats[1] == maxi]
    if form.size > 1:
        print("Multiple valid file-formats in folder ('{0}'), selecting {1}-files only.".format(folder, form[0]))
    form = "*" + form[0]

    return glob.glob(os.path.join(folder, form)), form[1:]
            
def ungz(path):
    with gzip.open(path, 'rb') as f_in:
        temp_file = tempfile.NamedTemporaryFile(suffix='.tif').name
        with open(temp_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return temp_file

def unzip(path):
    zip_ref = zipfile.ZipFile(path, 'r')
    tif_files = [x for x in zip_ref.namelist() if x[-3:] == 'tif']
    assert len(tif_files) == 1, "zip-file ({0}) contains multiple tif-files".format(path)
    folder = tempfile.tempdir
    temp_file = zip_ref.extract(tif_files[0], path = folder)
    return temp_file

def fill_data_to_nc(nc_file, overview, optionsProj, optionsClip, shape):

    # Save the time-invariant data to nc-file.
    if "invariant" in overview.keys():
        invar = overview.pop("invariant")
        var = dict()
        for fh in [x for x in invar if x is not None]:
            temp_file = tempfile.NamedTemporaryFile(suffix='.tif').name
            temp_fileP = tempfile.NamedTemporaryFile(suffix='.tif').name
#            sourceds = gdal.Warp(temp_file, fh[1], options = options)
            gdal.Warp(temp_fileP, fh[1], options = optionsProj)
            sourceds = gdal.Warp(temp_file, temp_fileP, options = optionsClip)
            var[fh[0]] = sourceds.ReadAsArray()
            sourceds = None
            os.remove(temp_file)
            os.remove(temp_fileP)
        fill_nc_one_timestep(nc_file, var, shape)
    
    # Save time-variant data to nc-file.
    for date in tqdm(sorted(overview.keys())):
        var = dict()
        for fh in [x for x in overview[date] if x is not None]:
            # Reproject and open tif-file for a specific date.
            if isinstance(fh[1], str):
                ext = fh[1].split('.')[-1].split(":")[0]
                
                if ext == 'gz':
                    path = ungz(fh[1])
                elif ext == 'zip':
                    path = unzip(fh[1])
                else:
                    path = fh[1]
                    
                assert "GDAL_DATA" in os.environ
                
                path = check_projection(path)
                temp_file = tempfile.NamedTemporaryFile(suffix='.tif').name
                temp_fileP = tempfile.NamedTemporaryFile(suffix='.tif').name       
                
                gdal.Warp(temp_fileP, path, options = optionsProj)
                sourceds = gdal.Warp(temp_file, temp_fileP, options = optionsClip)
                var[fh[0]] = sourceds.ReadAsArray().astype(np.float32)
                
                if ext == 'nc':
                    var_name = fh[0]
                    scale = sourceds.GetMetadataItem("{0}#scale_factor".format(var_name))
                    offset = sourceds.GetMetadataItem("{0}#add_offset".format(var_name))
                    if scale is not None and offset is not None:
                        var[fh[0]][var[fh[0]] != -9999] *= float(scale)
                        var[fh[0]][var[fh[0]] != -9999] += float(offset)

                sourceds = None
                os.remove(temp_file)
                os.remove(temp_fileP)
                if ext in ['gz', 'zip']:
                    os.remove(path)

            # Open non-spatial data for a specific date.
            elif isinstance(fh[1], float):
                var[fh[0]] = fh[1]
            else:
                continue
        #fill_nc_one_timestep(nc_file, var, shape, date.toordinal())
        fill_nc_one_timestep(nc_file, var, shape, np.datetime64(date))
        
    return True
        
def make_overview(datasets, start = None, end = None):
    # Loop over the folders with tif-files and extract the date from the filenames.
    data_inventory = dict()
    
    for name1, ds in datasets.items():
        name = datasets[name1][2]['quantity']
        ds = ds[0]

        inventory = dict()
        
        # Make inventory of data from csv-files.
        if np.all([os.path.isfile(ds), os.path.splitext(ds)[1] == ".csv"]):
            with open(ds) as csv_file:
                csv_reader = csv.reader(csv_file)
                header_rows = 12
                [next(csv_reader) for x in range(header_rows)] # skip header rows
                for row in csv_reader:
                    yr, dc = row[0].split('.')
                    year = int(yr)
                    dec = float('0.' + dc)
                    year_length = {True: 366, False:365}[calendar.isleap(int(year))]
                    date = datetime.date(year, 1, 1) + relativedelta(days = dec * year_length)
                    value = float(row[1]) * 10 #cm to mm
                    inventory[date] = (name, value)

        # Make inventory of invariant spatial data.
        elif np.all([os.path.isfile(ds), os.path.splitext(ds)[1] == ".tif"]):
            inventory["invariant"] = (name, ds)
        
        # Make inventory of variant spatial data.
        elif os.path.isdir(ds):
            
            fhs, form = select_files(ds, possible_formats = ['.tif', '.zip', '.gz', '.nc'])
            
            for fh in fhs:
                try:
                    date_string = os.path.splitext(os.path.split(fh)[-1])[0].split('_')[-1]
                    date = datetime.datetime.strptime(date_string, '%Y.%m.%d').date()
                except:
                    print("skipping dates for {0}".format(fh))
#                date , _, _ = find_possible_dates_full(fh)
#                date = datetime.datetime.strptime(date_string, '%Y%m').date()
                
                if form == '.nc':
                    fh = "NETCDF:{0}:{1}".format(fh, name)


                inventory[date] = (name, fh)

        
        # Skip data that does match above criteria.
        else:
            print("skipping {0}".format(ds))
            continue
        
        data_inventory[name] = inventory
    
    # Create dictionary with list of availables tif-files as values for each date (key).
    overview = {}
    for k in itertools.chain(*[x.keys() for x in data_inventory.values()]):
        if isinstance(k, str) or ((start is None or start <= k) and (end is None or end >= k)):
            overview[k] = [x.get(k, None) for x in data_inventory.values()]
        
    return overview

def init_nc(nc_file, dim, var, fill = -9999., attr = None):
    # Create new nc-file. Existing nc-file is overwritten.
    out_nc = netCDF4.Dataset(nc_file, 'w', format='NETCDF4')
    
    # Add dimensions to nc-file.
    for name, values in dim.items():
        # Create limited dimensions.
#         print(name)
        if values is not None:
            out_nc.createDimension(name, values.size)
            vals = out_nc.createVariable(name, 'f4', (name,), fill_value = fill)
            vals[:] = values
        # Create unlimited dimensions.
        else:
            out_nc.createDimension(name, None)
            vals = out_nc.createVariable(name, 'f4', (name,), fill_value = fill)
            vals.calendar = 'standard'
            vals.units = 'days since 1970-01-01 00:00'
    
    # Create variables.
    for name, props in var.items():
        vals = out_nc.createVariable(props[2]['quantity'], 'f4', props[1], zlib = True, 
                                     fill_value = fill, complevel = 9, 
                                     least_significant_digit = 4)
        vals.setncatts(props[2])


    if attr != None:
        out_nc.setncatts(attr)

    # Close nc-file.
    out_nc.close()

def get_lats_lons(example, shape):
    
    gdal.UseExceptions()
    
    # Create temporary tif-file.
    temp_file = tempfile.NamedTemporaryFile(suffix='.tif').name
    
    inDriver = ogr.GetDriverByName("ESRI Shapefile")
    inDataSource = inDriver.Open(shape, 1)
    inLayer = inDataSource.GetLayer()

    options = gdal.WarpOptions(cutlineDSName = shape,
                               cutlineLayer = inLayer.GetName(),
                               cropToCutline = False,
                               dstNodata = -9999,
                               )
    
    sourceds = gdal.Warp(temp_file, example, options = options)

    geot    = sourceds.GetGeoTransform()
    xsize   = sourceds.RasterXSize # columns
    ysize   = sourceds.RasterYSize # rows
    
    lons = np.arange(geot[0], (geot[0] + xsize * geot[1]) - geot[1] + 1e-10, geot[1]) + 0.5 * geot[1]
    lats = np.arange(geot[3], (geot[3] + ysize * geot[5]) - geot[5] - 1e-10, geot[5]) + 0.5 * geot[5]

    minX = geot[0]
    minY = geot[3] + ysize * geot[5]
    maxX = geot[0] + xsize * geot[1]
    maxY = geot[3]
    
    assert lats.size == ysize
    assert lons.size == xsize
    
#     print(np.diff(lats)[0] - geot[5])
#     print(np.diff(lons)[0] - geot[1])

    optionsProj = gdal.WarpOptions(
                               outputBounds = (minX, minY, maxX, maxY),
                               width = xsize,
                               height = ysize,
                               dstNodata = -9999,
                               options = ["GDALWARP_IGNORE_BAD_CUTLINE YES"],
                               )

    # optionsClip = gdal.WarpOptions(                               
    #                             outputBounds = (minX, minY, maxX, maxY),
    #                             width = xsize,
    #                             height = ysize,
    #                             dstNodata = -9999,
    #                             options = ["GDALWARP_IGNORE_BAD_CUTLINE YES"],
    #                             )
    
    optionsClip = gdal.WarpOptions(
                                cutlineDSName = shape,
                                cutlineLayer = inLayer.GetName(),
                                cropToCutline = False,
                                outputBounds = (minX, minY, maxX, maxY),
                                width = xsize,
                                height = ysize,
                                dstNodata = -9999,
                                options = ["GDALWARP_IGNORE_BAD_CUTLINE YES"],
                                )
    
    return lats, lons, optionsProj, optionsClip

def fill_nc_one_timestep(nc_file, var, shape, time_val = None):
    # Open existing nc-file.
    out_nc = netCDF4.Dataset(nc_file, 'r+')
    varis = out_nc.variables.keys()
    dimis = out_nc.dimensions.keys()
    
    # Add time-dependent data to nc-file.
    if time_val is not None:
        time = out_nc.variables['time']
        tidx = time.shape
        time[tidx] = time_val
        
        for name in [x for x in varis if "time" in out_nc[x].dimensions and x not in dimis]:
            field = out_nc.variables[name]
            if name in var.keys():
                field[tidx,...] = var[name]
            else:
                shape = tuple([y for x, y in enumerate(out_nc[name].shape) if out_nc[name].dimensions[x] != "time"])
                dummy_data = np.ones(shape) * out_nc[name]._FillValue
                field[tidx,...] = dummy_data
    
    # Add invariant data to nc-file.
    else:
        for name, data in var.items():
            out_nc.variables[name][...] = data
    
    # Close nc-file.
    out_nc.close()

def make_netcdf(nc_file, dataset, shape, example, name, start=None, end=None):
    
    print (f" \n writing {nc_file}")
    
    # Give necessary dimensions in nc-file.
    dims = {'time':  None, 'latitude': None, 'longitude': None}
    
    # Point to datasets, specificy dimensions, units and format.
#    datasets = {
#                'P'             : [r"F:\Products\CHIRPS", 
#                                   ('time','latitude', 'longitude'), 
#                                   {'units': 'mm/day', 'source': 'CHIRPS', 'quantity':'P'}]
#        
#                'ETa_SSEBOP'    : [r"F:\Products\SSEBop", 
#                                   ('time','latitude', 'longitude'), 
#                                   {'units': 'mm/dekad', 'source': 'SSEBOP', 'quantity':'ETa'}],
#                                   
#                'ETa_GLEAM'     : [r"F:\Products\SSEBop", 
#                                   ('time','latitude', 'longitude'), 
#                                   {'units': 'mm/day', 'source': 'GLEAM', 'quantity':'ETa'}],
#    
#                'SMtop'         :  [r"F:\Products\SMAP\AS1\GTiff",
#                                    ('time','latitude', 'longitude'), 
#                                    {'units': 'mm', 'source': 'SMAP AS1', 'quantity':'SMrz'}],
#                            
#                'SMdown'        : [r"F:\Products\SMAP\AS2\GTiff",
#                                   ('time','latitude', 'longitude'), 
#                                   {'units': 'mm', 'source': 'SMAP AS2', 'quantity':'SMrz'}],
#    
#                'SMmax'         : [r"F:\Products\SMmax\SMmax_CRU_mm_invar.tif", 
#                                   ('latitude', 'longitude'), 
#                                   {'units': 'mm', 'source': 'CRU', 'quantity':'SMmax'}],
#    
#                'ts_S'          : [r"F:\Products\GRACE\GSFC_basin_{0}.csv".format(name), 
#                                   ('time'), 
#                                   {'units': 'mm', 'source': 'GRACE', 'quantity': 'S'}],
#                            
#                'LAI'           : [r"F:\Products\LAI\NOAA",
#                                   ('time', 'latitude', 'longitude'),
#                                   {'units': 'm2/m2', 'source': 'NOAA', 'quantity': 'LAI'}],
                                   
#               }

    dims['latitude'], dims['longitude'], optionsProj, optionsClip = get_lats_lons(example, shape)
    init_nc(nc_file, dims, dataset, attr = {"basin_name" : name})

    overview = make_overview(dataset, start, end)
    succes = fill_data_to_nc(nc_file, overview, optionsProj, optionsClip, shape)
    return succes

##%% Example
#
#name = 'Mahaweli'
#datasets = {'P'        : [r'E:\SriLanka\Data\Precipitation\CHIRPS\Monthly', 
#                               ('time','latitude', 'longitude'), 
#                               {'units': 'mm/month', 'source': 'CHIRPS', 'quantity':'P'}],
#            'P2'        : [r'E:\SriLanka\Data\Precipitation\TRMM\Monthly', 
#                               ('time','latitude', 'longitude'), 
#                               {'units': 'mm/month', 'source': 'TRMM', 'quantity':'P'}],      
#            'ETens'    : [r'E:\SriLanka\Data\Evaporation\ETensV1_0', 
#                               ('time','latitude', 'longitude'), 
#                               {'units': 'mm/month', 'source': 'ETens', 'quantity':'ETa'}],
#        }
#
## lu_path needed for resampling
#lu_path = r"E:\SriLanka\Sri_Lanka\LC_computation\Results\Mahaweli.tif"
## shapefile needed for clipping
#shp_path = r"E:\SriLanka\Sri_Lanka\Basin_shapefile\Mahaweli_basin_mwsip_WGS84_valid.shp"
#
#save_location = r"D:\Test"
#
##%% Make netCDF from tiff files
#nc_files = []
#for d in datasets:
#    dataset = {d: datasets[d]}
#    fname = name+'_'+datasets[d][2]['quantity']+'_'+ datasets[d][2]['source']+'.nc'
#    nc_file = os.path.join(save_location, fname)
#    nc_files.append(nc_file)
#    succes = make_netcdf(nc_file, dataset, shp_path, lu_path, name)
## Make plot of january average with xarray
#import xarray as xr
#import matplotlib.pyplot as plt
#nc_file = r"D:\Test\MahaweliVI_P_CHIRPS.nc"
#ds = xr.open_dataset(nc_file)
## monthly average - spatially
##ds.groupby('time.month').mean('time')
#plt.imshow(ds.groupby('time.month').mean('time')['P'][0])
#
## generate timeseries of average month values
#m_ts = ds.groupby('time.month').mean(dim=xr.ALL_DIMS)['P']
#
#
##dsel = ds.sel(time=slice('2006-05-01', '2012-04-01'))
#
#dy = ds.resample(time='A-MAY').sum(skipna=False).mean(dim=['latitude', 'longitude'])
#
