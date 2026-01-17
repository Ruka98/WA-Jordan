# -*- coding: utf-8 -*-
"""
Created on Fri May 1 15:09:33 2020

@author: ntr002

Functions to calculate extra data needed for WA+ sheets from pixel-based model results (NetCDF dataset)

"""
import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import calendar
import datetime
import csv
from itertools import groupby
from operator import itemgetter
from dateutil.relativedelta import relativedelta
from . import calculate_flux as cf
from . import get_dictionaries as gd
from . import GIS_functions as gis
##
from scipy import interpolate

#%% General
def check_requirement_sheet(BASIN,requirements,
                             gis_data=True,
                             data_cube=True,
                             params=True): 
    '''
    Check if BASIN dictionary includes the path to files required for WA+ sheet
    BASIN: dictionary
    requirements: dictionary
    
    '''
    #check parameters requirements
    if len(requirements['params']-BASIN['gis_data'].keys())>0:
        print('Required parameters for Sheet {0} are missing: '.format(
                requirements['sheet']))
        print(requirements['gis_data']-BASIN['gis_data'].keys())
        gis_data=False        
    #check GIS data requirements
    if len(requirements['gis_data']-BASIN['gis_data'].keys())>0:
        print('Required GIS data for Sheet {0} are missing: '.format(
                requirements['sheet']))
        print(requirements['gis_data']-BASIN['gis_data'].keys())
        gis_data=False
    #check data cube requirements
    if len(requirements['data_cube']-BASIN['data_cube'].keys())>0:
        missing_data=list(requirements['data_cube']-BASIN['data_cube'].keys())
        print('Required spatial data for Sheet {0} are missing: '.format(
                requirements['sheet']))
        print(missing_data)
        for data in missing_data:            
            if data.replace('yearly','monthly') in BASIN['data_cube'].keys():
                print('Convert {0} from {1}'.format(data,
                      data.replace('yearly','monthly')))
                output=cf.create_yearly_dataset(
                        BASIN['data_cube'][data.replace('yearly',
                                         'monthly')],
                                        hydroyear=BASIN['hydroyear'],
                                        chunksize=BASIN['chunksize']
                                         )
                BASIN['data_cube'][data]=output
            else:
                print('Missing mothly data to convert to {0}'.format(data))
                data_cube=False
    
    return gis_data*data_cube*params

def calc_yearly_sheet(monthly_csvs,output_folder,hydroyear='A-DEC'):
    '''
    calculate hydro-yearly sheet from monthly sheet csvs
    
    '''
    hydroyear_boundary={'A-DEC':1,'A-JAN':2,'A-FEB':3,'A-MAR':4,'A-APR':5,
                        'A-MAY':6,'A-JUN':7,'A-JUL':8,'A-AUG':9,'A-SEP':10,
                        'A-OCT':11,'A-NOV':12}
    boundary_month=hydroyear_boundary[hydroyear]
    
    all_years=np.array(
            [int(os.path.basename(csv).split('.')[0].split('_')[1]) for csv in monthly_csvs])
    years=np.unique(all_years)#get unique years
    yearly_csvs=[]
    for year in years:        
        start = datetime.date(year, boundary_month, 1)
        end=start+relativedelta(years=1)-relativedelta(days=1)
        csvs_in_years=[]
        for file in monthly_csvs:
            sheet=os.path.basename(file).split('.')[0].split('_')[0]
            m_year=int(os.path.basename(file).split('.')[0].split('_')[1])
            m_month=int(os.path.basename(file).split('.')[0].split('_')[2])
            date=datetime.date(m_year,m_month,1)            
            if start<=date<=end: #check if month belong to year
                csvs_in_years.append(file) #append to the current year
        if len(csvs_in_years)<12: #if hydro year does not have enough months
            print('Missing monthly sheet for year {0}'.format(year))
        elif len(csvs_in_years)==12: #if hydro year has enough months
            for i in range(12):
                if i==0:
                    df_year=pd.read_csv(csvs_in_years[i],sep=';')
                else:
                    df=pd.read_csv(csvs_in_years[i],sep=';')
                    for col in df.columns:
                        if type(df[col][0]) is not str:
                            df_year[col]+=df[col].values
            output_fh=os.path.join(output_folder,'{0}_{1}.csv'.format(sheet,year))
            df_year.to_csv(output_fh,sep=';',index=False)
            yearly_csvs.append(output_fh)
    return yearly_csvs

            
            
    return yearly_csvs
def add_flow(flow_nc,additional_flow_nc,
             name='total_flow',
             output=None,chunksize=None):
    '''
    Add additional_flow_nc to flow_nc and save to new dataset
    '''
    flow=cf.open_nc(flow_nc,chunksize=chunksize,layer=0)
    additional_flow=cf.open_nc(additional_flow_nc,
                               chunksize=chunksize,layer=0)
    source_info='sum of '+flow.name+' and '+additional_flow.name
    total_flow=flow+additional_flow
    #Add attributes
    total_flow.name=name
    total_flow=total_flow.transpose('time',
                                    'latitude','longitude')
    total_flow.attrs={'units':flow.attrs['units'],
                    'source':source_info,
                    'quantity':name
                                  }    
    if output is None:
        output=os.path.join(
                os.path.dirname(flow_nc),
                '{0}.nc'.format(name))
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    print('Save summed {0} as {1}'.format(name,output))
    total_flow.to_netcdf(output,
                 encoding={total_flow.name:comp})  
    return output  

def substract_flow(flow_nc,subtract_flow_nc,
             name='difference_flow',
             output=None,chunksize=None):
    '''
    substract subtract_flow_nc from flow_nc and save to new dataset
    '''
    flow=cf.open_nc(flow_nc,chunksize=chunksize,layer=0)
    subtract_flow=cf.open_nc(subtract_flow_nc,
                               chunksize=chunksize,layer=0)
    source_info='difference of '+flow.name+' and '+subtract_flow.name
    difference_flow=flow-subtract_flow
    #Add attributes
    difference_flow.name=name
    difference_flow=difference_flow.transpose('time',
                                    'latitude','longitude')
    difference_flow.attrs={'units':flow.attrs['units'],
                    'source':source_info,
                    'quantity':name
                                  }    
    if output is None:
        output=os.path.join(
                os.path.dirname(flow_nc),
                '{0}.nc'.format(name))
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    print('Save {0} as {1}'.format(name,output))
    difference_flow.to_netcdf(output,
                 encoding={difference_flow.name:comp})  
    return output  

def split_flow(flow_nc,
               fraction=0.5,
               fraction_nc=None,                           
               output=None,
               chunksize=None,
               sub_names = ['sw','gw'] ):
    '''
    split flow_nc into 2 flows using a fraction map or value.
    For example, used to split supply into sw and gw supply, 
    or for split return flow into sw and gw return flow
    
    flow_nc: str
        path to the flow to split
    fraction: float
        single fraction value. default is 0.5
    fraction_nc: str
        path to the fraction map
    output: str
        path to the output filename 'output_{0}.nc'
    sub_names: list
        name of the splitted flows ex. ['sw','gw']
    '''
    flow=cf.open_nc(flow_nc,chunksize=chunksize,layer=0)
    source_info=flow.name
    if fraction_nc is not None: #use fraction map
        fraction=cf.open_nc(fraction_nc,
                            chunksize=chunksize,layer=0)
        source_info+= ' multiplied by ' +fraction.name
    else:
        source_info+= ' multiplied by {0}'.format(fraction)

    flow_one=flow*fraction 
    flow_two=flow-flow_one 
    
    #modify attributes of splitted flow datasets
    flow_one=flow_one.transpose('time','latitude','longitude')
    flow_two=flow_two.transpose('time','latitude','longitude')
    name=flow.name
    flow_one.name='{0}_{1}'.format(name,sub_names[0])
    flow_two.name='{0}_{1}'.format(name,sub_names[1])
    flow_one.attrs={'units':flow.attrs['units'],
                    'source':source_info,
                    'quantity':flow.attrs['quantity']
                                  }
    flow_two.attrs={'units':flow.attrs['units'],
                    'source':flow.name+' minus ' +source_info,
                    'quantity':flow.attrs['quantity']
                                  }
    if output is None:
        output=flow_nc.replace('.nc','_{0}.nc')
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    one_output=output.format(sub_names[0])
    two_output=output.format(sub_names[1])
    print('Save splitted {0} as {1} and {2}'.format(
            name,one_output,two_output))
    flow_one.to_netcdf(one_output,
                 encoding={flow_one.name:comp})
    flow_two.to_netcdf(two_output,
                 encoding={flow_two.name:comp})    
    return one_output,two_output

def flow_ratio(numerator_nc,denominator_nc,
               name=None,attrs=None,
               chunksize=None,
               output=None
               ):
    '''
    Calculate ratio of dataset divided by another dataset
    '''
    numerator=cf.open_nc(numerator_nc,chunksize=chunksize,layer=0)
    denominator=cf.open_nc(denominator_nc,chunksize=chunksize,layer=0)
    if name is None:
        name=numerator.name+' by '+denominator.name+' ratio'
    ratio=numerator/denominator #calculate ratio
    #add attributes
    ratio=ratio.transpose('time','latitude','longitude')
    ratio.name=name
    if attrs is None:
        attrs={'units': '-', 
               'source': numerator.source +', '+denominator.source,
               'quantity':name}
    ratio.attrs=attrs
    #save ratio to new netCDF
    if output is None:
        output=os.path.join(os.path.dirname(numerator_nc),
                            '{0}.nc'.format(name.replace(' ','_')))
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    ratio.to_netcdf(output,
                 encoding={ratio.name:comp})  
    return output

##To create fractions.nc file        
def calc_fractions(p_nc,dem,lu,fraction_altitude_xs,output=None,chunksize=None):
    dts_p=cf.open_nc(p_nc,chunksize=chunksize,layer=0)
    lu=cf.open_nc(lu,chunksize=chunksize,layer=0)    
    dem_fh=gis.OpenAsArray(dem,nan_values=True)

    lu_fh = lu[0] * 0
    upstream_fh = lu_fh.astype(np.int16).values
    
    fractions_altitude = linear_fractions(lu_fh, upstream_fh, dem_fh, 
                     fraction_altitude_xs, unit='m', quantity='Altitude',
                     plot_graph=False)
    
    dates  = pd.DatetimeIndex(dts_p['time'].values)
    p_months = np.array([date.month for date in dates])

    frac = np.zeros((len(dts_p['time']),len(dts_p['latitude']),len(dts_p['longitude'])))
    for i in range(len(dts_p.time)):
        P_i = dts_p.isel(time=i).values      
        fra = dts_p[0]*0
        aa = [p_months == dates[i].month]      
        P = dts_p[aa[0]].values
        std, mean = calc_mean_std(P)
        fra['time'] = dts_p.isel(time=i)['time']
        fractions_dryness_fh = dryness_fractions(P_i, std, mean, base=-0.5, top=0.0)
        
        FH1 = fractions_altitude
        FH2 = fractions_dryness_fh
        FH3 = FH1 * FH2
        frac[i] = FH3    
    
    f = frac + dts_p*0         
    # f = xr.DataArray(frac, dims=['time','latitude','longitude'], coords={'time':dts_p['time'], 
    #                                                                     'latitude':dts_p['latitude'],
    #                                                                     'longitude':dts_p['longitude']})       

    # f = frac + dts_p[0]*0
    f=f.transpose('time','latitude','longitude') 
    f.name='fraction'
    f.attrs={'quantity':'Fraction'}
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    encoding = {f.name: comp}    
    if output is None:
        output=os.path.join(os.path.dirname(p_nc),
                            'fractions.nc')
    print('Save Fraction datacube as {0}'.format(output)) 
    f.to_netcdf(output,encoding=encoding)
    #close dataset
    dts_p.close()
    lu.close()   
    return output   

def linear_fractions(lu_fh, upstream_fh, proxy_fh, xs, unit='km',
                     quantity='Distance to water', gw_only_classes=None,
                     plot_graph=True):

    upstream = upstream_fh.astype(np.bool)
    distances = np.array(proxy_fh)
    f1 = interpolate.interp1d([xs[0], xs[1]], [1, 0], kind='linear',
                              bounds_error=False, fill_value=(1, 0))
    f2 = interpolate.interp1d([xs[2], xs[3]], [1, 0], kind='linear',
                              bounds_error=False, fill_value=(1, 0))
    
    LULC = lu_fh.values    
    distances[np.isnan(LULC)] = np.nan

    alpha = np.zeros(np.shape(distances))
    alpha[upstream] = f1(distances[upstream])
    alpha[~upstream] = f2(distances[~upstream])
      
    return alpha

def calc_mean_std(fihs):
    """
    Calculate the mean and the standard deviation per pixel for a serie of maps.

    Parameters
    ----------
    fihs : ndarray
        Array with filehandles pointing to maps to be used.

    Returns
    -------
    std : ndarray
        Array with the standard deviation for each pixel.
    mean : ndarray
        Array with the mean for each pixel.
    """
    data_sum = data_count = np.zeros_like(fihs[0])

    for fih in fihs:
        data = fih
        # data[np.isnan(data)] = 0
        data_sum = np.nansum([data_sum, data], axis=0)

        count = np.ones_like(data)
        count[np.isnan(data)] = 0
        data_count += count

    mean = data_sum / data_count
    data_sum = np.zeros_like(data)

    for fih in fihs:
        data = (fih - mean)**2 / data_count
        data_sum += data

    std = np.sqrt(data_sum)

    return std, mean
  
def dryness_fractions(P, std, mean, base=-0.5, top=0.0):
    """
    Calculate fractions per pixel based on the distribution P compared to its long-term
    mean and std.

    Parameters
    ----------
    p_fh : str
        Filehandle pointing to precipitation map.
    std_fh : str
        Filehandle pointing to standard deviation map.
    mean_fh : str
        Filehandle pointing to map with mean values.
    fractions_dryness_fh : str
        Filehandle indicating where to store result.
    base : float, optional
        Use base to shift to lower boundary. Fractions are zero for pixels where
        the precipitation is smaller than (mean + base * std). Default is -0.5.
    top : float, optional
        Use top to shift the upper boundary. Fractions are one for pixels where the precipitation
        is larger than (mean + top *std). Default is 0.0.
    """
    
    STD = std
    MEAN = mean

    BASE = MEAN + base * STD
    TOP = MEAN + top * STD

    fractions = np.where(P > BASE, np.min([(1.0 / (TOP - BASE)) * (P - BASE), np.ones(np.shape(P))], axis=0), np.zeros(np.shape(P)))

    return fractions
#%% Sheet 2 functions
    
def split_ETI(et_nc,i_nc=None,t_nc=None,
              chunksize=None,**input_data):
    '''
    split actual evapotranspiration into 3 components
    Evaporation, Transpiration, and Interception
    
    '''
    keys=input_data.keys()
    
    #Interception
    if i_nc is None:
        #check input data        
        list_rq=['p_nc','lai_nc','nrd_nc']
        check=[item in keys for item in list_rq]
        if not all(check): #not enough input_data
            print('ERROR:Missing data to calculate interception')
            print('p_nc: path to precipitation dataset')
            print('lai_nc: path to LAI dataset')
            print('nrd_nc: path to number of rainy days dataset')            
            return None
        else: #input_data is sufficient to calculate i
            p_nc=input_data['p_nc']
            lai_nc=input_data['lai_nc']
            nrd_nc=input_data['nrd_nc']
            i_nc=calc_interception(p_nc,lai_nc,nrd_nc,
                              chunksize=chunksize)

            return
    #Transpiration
    if t_nc is None:
        #check input data        
        list_rq=['ndm_nc']
        check=[item in keys for item in list_rq]
        if not all(check): #not enough input_data
            print('ERROR:Missing data to calculate             transpiration')
            print('et_nc: path to actual evapotranspiration                  dataset')
            print('ndm_nc: path to Net-Dry-Matter dataset')
            print('i_nc: path to interception dataset')
            return None
        else: #input_data is sufficient to calculate t        
            if 'ndm_max_original' in keys:#check ndm_max method
                ndm_max_original=input_data['ndm_max_original']
            else: #if no method specified, keep False
                ndm_max_original=False           

            ndm_nc=input_data['ndm_nc']
            t_nc=calc_transpiration(et_nc,i_nc,ndm_nc,
                       chunksize=chunksize,
                       ndm_max_original=ndm_max_original)            
    #Evaporation
    e_nc=calc_evaporation(et_nc,i_nc,t_nc,chunksize=chunksize)            
    return e_nc,i_nc,t_nc

def calc_interception(p_nc,lai_nc,nrd_nc,
                      output=None,
                      chunksize=None):
    '''
    calculate interception from LAI and precipitation
    '''
    #open dataset
    p=cf.open_nc(p_nc,chunksize=chunksize,layer=0)
    lai=cf.open_nc(lai_nc,chunksize=chunksize,layer=0)
    nrd=cf.open_nc(nrd_nc,chunksize=chunksize,layer=0)
    #fill nan
    
    #calculate Interception
    i = lai * (1 - (1 + (p/nrd) \
                    * (1 - xr.ufuncs.exp(-0.5 * lai)) \
                    * (1/lai))**-1) * nrd
    #fill in nan value due to missing lai value    
    i = xr.where(xr.ufuncs.isnan(i),0,i)+p*0
    #save dataset
    i=i.transpose('time','latitude','longitude') 
    i.name='Interception'
    i.attrs={'units':p.attrs['units'],
    'source':'LAI* (1-(1+(P/nRD)*(1-exp(-0.5*LAI))*(1/LAI))**-1)*nRD',
    'quantity':'interception'
    }
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    encoding = {i.name: comp}    
    if output is None:
        output=os.path.join(os.path.dirname(p_nc),
                            'interception.nc')
    print('Save Interception datacube as {0}'.format(output)) 
    i.to_netcdf(output,encoding=encoding)
    #close dataset
    p.close()
    lai.close()
    nrd.close()
    return output

def calc_transpiration(et_nc,i_nc,ndm_nc,
                       chunksize=None,
                       output=None,
                       ndm_max_original=False):
    '''
    calculate transpiration from net-dry-matter, given actual 
    evapotranspiration and interception
    '''
    #open dataset
    et=cf.open_nc(et_nc,chunksize=chunksize,layer=0)
    interception=cf.open_nc(i_nc,chunksize=chunksize,layer=0)
    ndm=cf.open_nc(ndm_nc,chunksize=chunksize,layer=0)
    #calculate maximum NDM
    if not ndm_max_original:
        ndm_month_avg=ndm.groupby('time.month').mean(
                dim=['time'],skipna=True) #calculate monthly mean
        ndm_month_std=ndm.groupby('time.month').std(
                dim=['time'],skipna=True) #calculate monthly std
        ndm_month_max=ndm_month_avg+2*ndm_month_std
        #spread monthly max to all time steps in datacube
        ndm_max=ndm*0        
        for i in range(len(ndm_max)):
           m=pd.to_datetime(ndm.time[0].data).month #month index
           ndm_max[i]=ndm_month_max[m-1]
        
    if ndm_max_original:
        ndm_month_max=ndm.groupby('time.month').max(
                dim=['time'],skipna=True) #calculate monthly max      
        #spread monthly max to all time steps in datacube
        ndm_max=ndm*0  
        for i in range(len(ndm_max)):
           m=pd.to_datetime(ndm.time[0].data).month #month index
           ndm_max[i]=ndm_month_max[m-1]/0.95
    #calculate Transpiration
    t=xr.ufuncs.minimum((ndm/ndm_max),0.95)*(et-interception)
    #fill in nan value due to missing ndm value    
    t = xr.where(xr.ufuncs.isnan(t),0,t)+et*0
    #save dataset
    t=t.transpose('time','latitude','longitude') 
    t.name='transpiration'
    t.attrs={'units':et.attrs['units'],
    'source':'minimum(0.95,NDM/NDM_max)*(ETa-I)',
    'quantity':'Transpiration'
    }
    comp = dict(zlib=True, 
#                 complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    encoding = {t.name: comp}    
    if output is None:
        output=os.path.join(os.path.dirname(et_nc),
                            'transpiration.nc')
    print('Save Transpiration datacube as {0}'.format(output)) 
    t.to_netcdf(output,encoding=encoding)
    #close dataset
    et.close()
    interception.close()
    ndm.close()
    return output

def calc_evaporation(et_nc,i_nc,t_nc,
                     chunksize=None,
                     output=None):
    '''
    calculate evaporation from actual evapotranspiration, given interception
    and transpiration portions
    
    '''
    #open dataset
    et=cf.open_nc(et_nc,chunksize=chunksize,layer=0)
    i=cf.open_nc(i_nc,chunksize=chunksize,layer=0)
    t=cf.open_nc(t_nc,chunksize=chunksize,layer=0)
    #calculate evaporation
    e=et-i-t
    #save dataset
    e=e.transpose('time','latitude','longitude') 
    e.name='evaporation'
    e.attrs={'units':et.attrs['units'],
    'source':'ETa - I - T',
    'quantity':'Evaporation'
    }
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    encoding = {e.name: comp}    
    if output is None:
        output=os.path.join(os.path.dirname(et_nc),
                            'evaporation.nc')
    print('Save Evaporation datacube as {0}'.format(output)) 
    e.to_netcdf(output,encoding=encoding)
    #close dataset
    et.close()
    i.close()
    t.close()    
    
    return output

def calc_ndm(npp_nc):
    '''
    Calculate Net Dry Matter based on monthly Net Primary Production
    '''
    return
#%% Sheet 3 functions
def import_growing_seasons(csv_fh):
    """
    Reads an csv file with dates, see example for format of the csv file.
    
    Parameters
    ----------
    csv_fh : str
        Filehandle pointing to csv-file
        
    Returns
    -------
    start_dates : ndarray
        List with datetime.date objects
    end_dates : ndarray
        List with datetime.date object
    
    Examples
    --------
    The csv file should be like:
    >>> Start;End<new_line> 
            04/11/2000;17/02/2001<new_line>
            03/05/2001;02/07/2001<new_line>
            29/11/2001;27/02/2002<new_line>
            etc.
    
    """
    start_dates = np.array([])
    end_dates = np.array([])

    with open(csv_fh) as csvfile:
         reader = csv.reader(csvfile, delimiter=';')
         for row in reader:
             if np.all([row[0] != 'Start', row[1] != 'End']):
                 start_dates = np.append(start_dates, 
                                         datetime.datetime.strptime(row[0], 
                                         '%d/%m/%Y').date())
                 end_dates = np.append(end_dates, 
                                       datetime.datetime.strptime(row[1], 
                                       '%d/%m/%Y').date())    
    return start_dates, end_dates

def calc_seasonal_value(ts,start_dates,end_dates,output=None,name='Seasonal'):
    '''
    ts: pandas.series.Series
            monthly time-series
    start_dates: np.array datetime.date
    end_dates: np.array datetime.date
    '''
    season_data=[]
    for i in range(len(start_dates)): #loop over each season        
        startdate=start_dates[i] #season start date
        enddate=end_dates[i] #season end date
        current = datetime.date(startdate.year, startdate.month, 1)
        end_month = datetime.date(enddate.year, enddate.month, 1)
        
        req_dates = np.array([current])
        while current < end_month:
            current = current + relativedelta(months = 1)
            req_dates = np.append(req_dates, current)
        
        season_complete = True
        season_value=np.nan
        for date in req_dates: #check if all months in season available
            season_complete = np.all([season_complete, date in ts.index])
            if not season_complete:
                print("{0} missing in input data, skipping this season".format(date))
        if season_complete:        
            fractions = np.ones(np.shape(req_dates))            
            start_month_length = float(calendar.monthrange(startdate.year,
                                                           startdate.month)[1])
            end_month_length = float(calendar.monthrange(enddate.year,
                                                         enddate.month)[1])   
            #fraction of season days in the first month
            fractions[0] = (start_month_length - startdate.day + 1) / start_month_length
            #fraction of season days in the last month
            fractions[-1] = (enddate.day -1) / end_month_length        
            month_values=np.array(
                    [ts.loc[date]*fraction \
                     for date, fraction in zip(req_dates, fractions)])
            season_value=np.nansum(month_values)
        season_data.append(season_value)        
    result=pd.DataFrame({ #
            'start_dates':start_dates,
            'end_dates':end_dates,
            name:np.array(season_data)
            })
    if output is not None:
        result.to_csv(output,sep=';')    
    return result

def aggregate_year_from_season(df,output=None,
                               hydroyear='A-DEC',
                               name='Yearly',how='sum'):
    '''
    aggregate seasonal timeseries to yearly timeseries
    
    df: pandas.DataFrame
        seasonal dataframe with 3 columns
        start_dates: datetime.date
        end_dates: datetime.date
        Seasonal_total: float
    output: str
        path to output csv file
    how: str
        'sum' sum all seasonal value
        'mean' average all seasonal value
    '''
    start_dates=df.start_dates
    end_dates=df.end_dates
    ts=df[df.columns[2]]
    years = np.unique(np.array(
            [date.year for date in np.append(start_dates, end_dates)]))
    ###hydroyear boundary
    hydroyear_boundary={'A-DEC':1,'A-JAN':2,'A-FEB':3,'A-MAR':4,'A-APR':5,
                        'A-MAY':6,'A-JUN':7,'A-JUL':8,'A-AUG':9,'A-SEP':10,
                        'A-OCT':11,'A-NOV':12}
    boundary_month=hydroyear_boundary[hydroyear]
    
    #calculate for each year
    yearly_data=[]
    for year in years:
        starts, ends = (np.array([start_date for start_date, end_date in zip(start_dates, end_dates) if start_date.year == year or end_date.year == year]),
                        np.array([end_date for start_date, end_date in zip(start_dates, end_dates) if start_date.year == year or end_date.year == year]))
    
        boundary = datetime.date(year, boundary_month, 1)
        
        year_length = 366 if calendar.isleap(year) else 365

        lengths_total_season = [float(abs((end - start).days)) for start, end in zip(starts, ends)] #length of season
        
        lengths_within_year = np.array([min(year_length, abs((boundary - end).days)) - abs(min(0, (boundary - start).days)) for start, end in zip(starts, ends)])
    
        fractions = lengths_within_year / lengths_total_season #fraction of season
        if how == 'sum':
            y=np.sum(np.array(
                    [ts[start_dates == start].values[0] for start in starts])\
                    * fractions)
        elif how=='mean':
            y=np.average(np.array(
                    [ts[start_dates == start].values[0] for start in starts]),
                         weights = fractions)
        yearly_data.append(y)
        
    result=pd.DataFrame({ #
            'year':years,
             name:np.array(yearly_data)
            })
    result=result.set_index('year')
    if output is not None:
        result.to_csv(output,sep=';')  
    return result
#%% Sheet 4 functions

def calc_sw_supply_fraction_by_LU(lu_nc,aeisw_tif,
                                  output=None,
                                  chunksize=None):
    '''
    calculate SW supply fraction by LU map
    lu_nc: string
        path to Land Use datacube netCDF file
    aeisw_nc: string
        Area equipped with surface water irrigation map (netCDF)
        
    '''
    lucs = gd.get_sheet4_6_classes() 
    fractions = gd.get_sheet4_6_fractions() #SW supply fractions
    LU=cf.open_nc(lu_nc,chunksize=chunksize,layer=0)   
    
    sw_supply_fraction=LU*0
    # fraction from dictionary
    for key in list(fractions.keys()):
        classes = lucs[key]
        fraction = fractions[key]
        print('{0} {1} {2}'.format(key,classes,fraction))
        sw_supply_fraction = xr.where(
                LU.isin(classes),fraction,sw_supply_fraction)        
    # update fraction with aeisw (GMIA)
    aeisw=gis.OpenAsArray(aeisw_tif,nan_values=True)
    aeisw=aeisw/100 #convert percentage to fraction
    aeisw = np.where(np.isnan(aeisw),np.nanmean(aeisw),aeisw)  #assume average aeisw where NaN
    sw_supply_fraction = xr.where(
                LU.isin(lucs['Irrigated crops']),# for irrigated crops
                aeisw,#sw_supply_fraction = aeisw
                sw_supply_fraction)          
    #save output    
    sw_supply_fraction=sw_supply_fraction.transpose(
            'time','latitude','longitude')               

    sw_supply_fraction.attrs={'units':'fraction',
                              'source':'LUWA, GMIA_aeisw',
                              'quantity':'Fraction of SW supply'
                                  }
    sw_supply_fraction.name = 'sw_supply_fraction'
    
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    encoding = {'sw_supply_fraction': comp}    
    if output is None:
        output=os.path.join(os.path.dirname(lu_nc),
                            'sw_supply_fraction.nc')
    sw_supply_fraction.to_netcdf(output,encoding=encoding)
    print('Save monthly sw supply fraction datacube as {0}'.format(output))
    del LU
    return output

def calc_sw_return_fraction(sroincr_nc,percincr_nc,
                            output=None,
                            chunksize=None):
    '''
    Calculate surface water return fraction
    DTOT = DSRO + DPERC
    SWRETFRAC = LU * 0
    SWRETFRAC[DTOT > 0] = (DSRO/(DTOT))[DTOT > 0]
    
    sroincr_nc: str
        path to incremental surface runoff dataset
    percinicr_nc: str
        path to incremental percolation dataset
    output: str
        path to output dataset 
    '''
    sroincr=cf.open_nc(sroincr_nc,chunksize=chunksize,layer=0)
    percincr=cf.open_nc(percincr_nc,chunksize=chunksize,layer=0)
    #calculate sw return fraction
    dtot=sroincr+percincr
    sw_return_frac=xr.where(dtot>0,sroincr/dtot,0)
    #add attributes
    sw_return_frac.name='sw_return_fraction'
    sw_return_frac=sw_return_frac.transpose('time','latitude','longitude')
    sw_return_frac.attrs={'units':'-',
                              'source':'SROincr/(SROincr+PERCincr)',
                              'quantity':'sw_return_fraction'
                                  }   
    #save output
    if output is None:
        output=os.path.join(os.path.dirname(sroincr_nc),'sw_return_fraction.nc')
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    sw_return_frac.to_netcdf(output,
                     encoding={'sw_return_fraction':comp})   
    sroincr.close()
    percincr.close()    
    return output


def calc_nonconsumed_supply(supply_nc,etincr_nc,
                            output=None, chunksize=None):
    '''
    calculate non-consumed supply by substracting Incremental ET from supply
    
    supply_nc: str
        path to Supply netCDF file
    etincr_nc: str
        path to Incremental ET netCDF file
    '''
    supply=cf.open_nc(supply_nc,chunksize=chunksize,layer=0)
    etincr=cf.open_nc(etincr_nc,chunksize=chunksize,layer=0)
    
    non_consumed=supply-etincr
    
    non_consumed.name='non_consumed_supply'
    non_consumed=non_consumed.transpose('time','latitude','longitude')
    non_consumed.attrs={'units':supply.attrs['units'],
                              'source':'Supply - ET Incremental',
                              'quantity':'non_consumed_supply'
                                  }
    if output is None:
        output=os.path.join(os.path.dirname(supply_nc),
                            'non_consumed_supply.nc')
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    non_consumed.to_netcdf(output,
                     encoding={'non_consumed_supply':comp})       
    return output

def calc_land_surface_water_demand(lai_nc, etref_nc, p_nc, lu_nc, 
                output=None,chunksize=None):
    '''
    calculate water demand of land surface based on LAI
    
    lai_nc: str
        path to LAI netcdf file
    etref_nc: str
        path to ET reference netcdf file
    p_nc: str
        path to Precipiation netcdf file
    lu_nc: str
        path to LU netcdf file (invariant or monthly)
        
    return 
    demand: xr.DataArray
        water demand datacube
    '''
    #read netcdf data
    lai=cf.open_nc(lai_nc,chunksize=chunksize,layer=0)
    et_reference=cf.open_nc(etref_nc,chunksize=chunksize,layer=0)
    lu=cf.open_nc(lu_nc,chunksize=chunksize,layer=0)
    p=cf.open_nc(p_nc,chunksize=chunksize,layer=0)
    
    #calculate Potential ET using LAI-based crop coefficient Kc
    kc = xr.where(lu.isin([4, 5, 30, 23, 24, 63]), #mask water classes
                  1.4, #water KC
                  (1 - xr.ufuncs.exp(-0.5 * lai)) / 0.76) #non-water KC   
    
    et_potential = kc*et_reference
    #calculate land surface water demand as the gap between potential ET and effective rainfall
    phi = et_potential / p
    
    effective_rainfall = xr.ufuncs.sqrt(phi*xr.ufuncs.tanh(1/phi)\
                                        *(1-xr.ufuncs.exp(-phi))) * p
    
    demand = et_potential - effective_rainfall
    #add attributes to demand data
    demand.name='land_surface_water_demand'
    demand=demand.transpose('time','latitude','longitude')
    demand.attrs={'units':p.attrs['units'],
                              'source':'Potential ET - Effective Rainfall',
                              'quantity':'land_surface_water_demand'
                                  }   
    #save results
    if output is None:
        output=os.path.join(os.path.dirname(lai_nc),'water_demand.nc')
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    demand.to_netcdf(output,
                     encoding={'land_surface_water_demand':comp})           
    return output

def calc_residential_water_consumption(population_tif,
                                       basin_mask,
                                       lu_nc,
                                       wcpc=100,flow_type='demand',
                                       chunksize=None,
                                       output=None):
    '''
    calculate domestic water demand or supply based on population map and
    water consumption per capita and add values to demand and supply dataset.
    
    wcpc: number
        water consumption per capita (L/person/day)
        use minimal wcpc to calculate residential demand 
        and actual wcpc to calculate residential supply
    lu_nc: str
        path to monthly LU NetCDF file
    blue_water_nc: str
        path to demand or supply NetCDF file
    flow_type: str
        'demand' or 'supply'
    '''
    # Read input data
    population=gis.OpenAsArray(population_tif,nan_values=True)
    area=gis.MapPixelAreakm(basin_mask)
    lu=cf.open_nc(lu_nc,chunksize=chunksize,layer=0)
    #get residential classes
    sheet4_lucs=gd.get_sheet4_6_classes() 
    classes = sheet4_lucs['Residential']    
    # Convert [pop/ha] to [pop/pixel]
    population *= area * 100    
    # Calculate WC per pixel in [mm/day]
    residential_wc = wcpc * population * 10**-6 / area
    
    # Calculate number days per month
    months=pd.to_datetime(np.array(lu.time))
    ndays=np.array(
            [calendar.monthrange(date.year, 
                                 date.month)[1] for date in months])
    ndays_da = xr.DataArray(ndays, dims=["time"])
    ndays_da['time']=lu['time']
    
    # Calculate WC per pixel in [mm/month]
    mask=xr.where(lu.isin(classes),1,0)
    ndays_mask=mask*ndays_da
    residential_wc=ndays_mask*residential_wc
    # Add residential water to total blue water
    mean=residential_wc.mean(dim=['latitude','longitude'],skipna=True)
    residential_wc=xr.where(xr.ufuncs.isnan(residential_wc),
                            -999,#fill nan temporarily with finite value
                            residential_wc)
    nan_residential_wc=xr.where( #residential pixels that has nan wc
        lu.isin(classes) * (residential_wc==-999),
                    1.0,#True
                    0.0) #False
    residential_wc+=nan_residential_wc*mean #fill nan residential_wc w/ mean 
    residential_wc+=lu*0 #replace nan in blue_water     
    # Save total_blue_water
    residential_wc=residential_wc.transpose('time',
                                                 'latitude','longitude')
    residential_wc.name='residential_'+flow_type
    residential_wc.attrs={'units':'mm/month',
                      'source':'WCPC*Population/area',
                      'quantity':'residential water {0}'.format(flow_type)
                                  }
    if output is None:
        output=os.path.join(os.path.dirname(lu_nc),
                                     'residential_{0}.nc'.format(
                                             flow_type))
    comp = dict(zlib=True, 
                complevel=9, 
                least_significant_digit=2, 
                chunksizes=chunksize)
    print('Save residential water {0} as {1}'.format(
            flow_type,output))
    residential_wc.to_netcdf(output,
                         encoding={residential_wc.name:comp})    
    #close files and return results
    lu.close()
    del population
    del area
    return output

#%% Sheet 5 functions
def calc_sw_from_wp(sro,sroincr,bf,supply_sw,output=None,
                         inflow=None, q_out_sw=None,outflow=True,plot=False,
                         ):
    '''
    calculate surface water outflow and storage from pixel-based model results
    In DataFrame format
    TF: Total flow = SRO + SROincr + BF
    SRO: Surface runoff
    SROincr: Incremental surface runoff
    BF: Baseflow
    SUPsw: Surface water Supply
    
    Unit: TCM
   
    '''
    total_flow=sro[sro.columns[0]]\
                +sroincr[sroincr.columns[0]]\
                +bf[bf.columns[0]]
    available_sw=total_flow-supply_sw[supply_sw.columns[0]]
    if inflow is not None:
        available_sw=available_sw+inflow[inflow.columns[0]]
    if q_out_sw is not None:
        available_sw=available_sw-q_out_sw[q_out_sw.columns[0]]

    discharge,dS_sw=distribute_available_sw(available_sw,outflow=outflow)
    index=available_sw.index
    discharge=pd.DataFrame(data=discharge,index=index,columns=['Discharge'])
    dS_sw=pd.DataFrame(data=dS_sw,index=index,columns=['dS_sw'])

    #plot flows
    if plot:
        plt.plot(available_sw,label='TF - Supplysw')
        plt.plot(discharge,'purple',label='discharge')
        plt.plot(dS_sw,'orange',label='dS_sw')
        plt.ylabel('TCM/month')
        plt.legend()
        
    if output is not None:
        discharge_output=output.format('discharge')
        dS_output=output.format('dS_sw')
        discharge.to_csv(discharge_output,sep=';')
        dS_sw.to_csv(dS_output,sep=';')
        return discharge_output,dS_output
    return discharge,dS_sw

def distribute_available_sw(available_sw,outflow=True):
    '''
    Distribute monthly available surface water into discharge and surface
    water storage change.
    available_sw= total_runoff + other_inflow - interbasin_outflow - sw_supply
    total_runoff= surface_runoff + incremental_surface_runoff + base_flow
    
    Assumption: The total negative available surface water in dry period is 
    compensated by the storing water to SW storage from the previous month
    with positive available surface water. The amount of stored water each 
    month is proportional to the positive available water each during the wet 
    period.
    ex.
    available_sw=[8 4 0 -2 -2 -2]
    return
    dS=[4 2 0 -2 -2 -2]
    discharge=[4 2 0 0 0 0]
    ----
    available_sw:np.array or pandas.Series
    outflow: True (default)
        True for basin with outflow
        False for endorheic basin
    available_sw=np.array([8,4,0,-2,-2,-2])
    '''
  
    ### if basin/subbasin has surface water outflow
    if outflow is False:
        dS=available_sw
        discharge = np.zeros(len(available_sw))
        
    ### if basin/subbasin has no surface water outflow
    else:
        dS = np.zeros(len(available_sw))
        for i in np.where(available_sw < 0):
            dS[i] = available_sw[i] 
            # DeltaS = RO(includes_returns) + otherInflows - W  where negative
    
        discharge = np.copy(available_sw)
        discharge[discharge < 0] = 0
        # Discharge = RO(includes_returns) + otherInflows - W where positive 
        
        ##backwards estimate SW storage increase in previous months based on negative dS        
        dS_temp=np.copy(dS)
        data = list(np.where(dS_temp < 0)[0])
        prev_end = 0
        for k, g in groupby(enumerate(data), lambda i_x: i_x[0]-i_x[1]):
            decr_st = list(map(itemgetter(1), g))
            start = decr_st[0]
            end = decr_st[-1]
            deltaS_season = np.sum(dS_temp[start:end+1])
            avail_per_month = available_sw[prev_end:start]
            avail_prev_season = np.sum(available_sw[prev_end:start])
            weight_per_month = avail_per_month/avail_prev_season
            if start > 0:
                if avail_prev_season < abs(deltaS_season):
                    print('Warning, insufficient runoff and inflows in previous months to meet DeltaS')
                    dS_temp[prev_end:start] = np.min((avail_per_month, -deltaS_season * weight_per_month), axis=0)
                    discharge[prev_end:start] = discharge[prev_end:start] \
                                             - dS_temp[prev_end:start]
                else:
                    dS_temp[prev_end:start] = dS_temp[prev_end:start] \
                                - deltaS_season * weight_per_month
                    discharge[prev_end:start] = discharge[prev_end:start]\
                                                    - dS_temp[prev_end:start]
            prev_end = end + 1
        dS = dS_temp        
    return discharge,dS

#%% Sheet 6 functions
