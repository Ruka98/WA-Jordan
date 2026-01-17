# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 17:10:28 2020

@author: ntr002
"""
import os
import csv
import numpy as np
import pandas as pd
from . import calculate_flux as cf
from . import get_dictionaries as gd
from . import hydroloop as hl

def main(BASIN,unit_conversion=1000):
    '''
    unit_conversion: 1 for TCM, 1000 for MCM, 1e6 for BCM or km3)
    '''
    #check requirements
#    requirements=gd.get_requirements_for_sheet(3)    
#    if not cf.check_requirement_sheet(BASIN,requirements):
#        sys.exit("ERROR: Data requirements for Sheet 3 are not fulfilled")
    #create folder to save intermetidate data
    folder=os.path.join(BASIN['output_folder'],
                        'csv','timeseries')        
    if not os.path.exists(folder):
        os.makedirs(folder)
    output_file=os.path.join(folder,'sheet3_{0}.csv')
    #create folder to save sheet 3 csv
    sheet_folder=os.path.join(BASIN['output_folder'],'csv','sheet3') 
    if not os.path.exists(sheet_folder):
        os.makedirs(sheet_folder) 
    # get sheet 3 dictionary
    sheet3_classes=gd.get_sheet3_classes(version='2.0')
    #Calulate monthly data to fill in Sheet 3    
    data={}
    yearly_data={}
    for key in ['et','etincr','etrain','ndm']:
        quantity='volume'
        if key=='ndm':
            quantity='depth'
        
        data[key]=cf.calc_flux_per_LU_class(
                     BASIN['data_cube']['monthly'][key],
                     BASIN['data_cube']['monthly']['lu'],
                     BASIN['gis_data']['basin_mask'],
                     output=output_file.format(
                             '{0}_monthly'.format(key)),
                     chunksize=BASIN['chunksize'],
                     quantity=quantity)
        #calculate et in mm
        if key=='et':
            data['et_depth']=cf.calc_flux_per_LU_class(
                     BASIN['data_cube']['monthly'][key],
                     BASIN['data_cube']['monthly']['lu'],
                     BASIN['gis_data']['basin_mask'],
                     output=output_file.format(
                             '{0}_monthly'.format(key)),
                     chunksize=BASIN['chunksize'],
                     quantity='depth')
    
    #calculate seasons
    data_years=[]
    for crop in BASIN['params']['crops']:
       yearly_data[crop]={}
       start_dates, end_dates=hl.import_growing_seasons(
       BASIN['params']['crops'][crop][0])
       for key in ['et','etincr','etrain','ndm', 'et_depth']:
           ts=data[key]['{0}'.format(crop)] #get time-series of crop class
           #calculate seasonal values
           df_season=hl.calc_seasonal_value(ts,start_dates,end_dates,
                                            output=output_file.format(
                                                    '{0}_{1}_season'.format(
                                                            crop,key)))
           
           #aggregate by year
           # if key=='ndm_wp':
           #     df=hl.aggregate_year_from_season(df_season,
           #        output=output_file.format('{0}_{1}_yearly'.format(crop,key)),
           #        hydroyear=BASIN['hydroyear'],
           #        how='mean')
           #     df*=0.1 #convert 0.1kg/m3 to kg/m3
               
           if key=='ndm':
               df=hl.aggregate_year_from_season(df_season,
                  output=output_file.format('{0}_{1}_yearly'.format(crop,key)),
                  hydroyear=BASIN['hydroyear'],
                  how='sum') #total kg/ha
                            
           else:
               df=hl.aggregate_year_from_season(df_season,
                  output=output_file.format('{0}_{1}_yearly'.format(crop,key)),
                  hydroyear=BASIN['hydroyear'],
                  how='sum')
               df/=unit_conversion  #convert TCM to volume unit
           #save data
           yearly_data[crop][key]=df
           data_years.append(np.array(df.index)) #append data years

       #calculate seasonal ndm_wp    
       df_et=pd.read_csv(output_file.format('{0}_{1}_season'.format(crop,'et_depth')),sep=';')        
       df_ndm=pd.read_csv(output_file.format('{0}_{1}_season'.format(crop,'ndm')),sep=';')
       df_season['Seasonal']=df_ndm['Seasonal']/df_et['Seasonal']
        #save seasonal ndm_wp
       df_season.to_csv(output_file.format('{0}_{1}_season'.format(crop,'ndm_wp')),sep=';')
        #aggregate yearly ndm_wp
       df=hl.aggregate_year_from_season(df_season,
                  output=output_file.format('{0}_{1}_yearly'.format(crop,'ndm_wp')),
                  hydroyear=BASIN['hydroyear'],
                  how='mean') #total 0.1 kg/m3
       df*=0.1 #convert 0.1kg/m3 to kg/m3
       yearly_data[crop]['ndm_wp']=df
       data_years.append(np.array(df.index))
           
           
    #find common years of sheet 3
    for i in range(len(data_years)):
        if i==0:
            common_years=data_years[0]
        else:
            common_years=np.intersect1d(common_years,data_years[0])
    #Fill data in Sheet 3 csv for each year 
    out_csvs=[]
    for year in common_years:
        results={}
        for SEASON in sheet3_classes:
            results[SEASON]={}
            for TYPE in sheet3_classes[SEASON]:
                for i in range(len(sheet3_classes[SEASON][TYPE])):
                    crop=sheet3_classes[SEASON][TYPE][i]
                    try:
                        et_raifall=yearly_data[crop]['etrain'].loc[year].values[0]
                        et_incremental=yearly_data[crop]['etincr'].loc[year].values[0]
                        land_productivity=yearly_data[crop]['ndm'].loc[year].values[0]
                        water_productivity=yearly_data[crop]['ndm_wp'].loc[year].values[0]                        
                    except:
                        et_raifall=np.nan
                        et_incremental=np.nan
                        land_productivity=np.nan
                        water_productivity=np.nan                        
                results[SEASON][TYPE]=[et_raifall,et_incremental,
                       land_productivity,water_productivity]

        #write sheet 3 csv
        output_fh=os.path.join(sheet_folder,'sheet3_{0}.csv'.format(year))
        create_sheet3_csv(year,results,output_fh)    
        out_csvs.append(output_fh)
    return out_csvs
        
def create_sheet3_csv(year,results,output_fh):
    """
    Create the csv-file needed to plot sheet 1.
    
    Parameters
    ----------
    results : dict
        Dictionary generated by calc_sheet1.
    output_fh : str
        Filehandle to store the csv-file.
    """
    # get sheet 3 dictionary
    sheet3_classes=gd.get_sheet3_classes(version='2.0') 

    first_row = ['SEASON', 'TYPE', 
                 'ET_RAINFALL','ET_INCREMENTAL',
                 'LAND_PRODUCTIVITY','WATER_PRODUCTIVITY']
    
    if not os.path.exists(os.path.split(output_fh)[0]):
        os.makedirs(os.path.split(output_fh)[0])
    
    csv_file = open(output_fh, 'w')
    writer = csv.writer(csv_file, delimiter=';', lineterminator = '\n')
    writer.writerow(first_row)
    
    for SEASON in list(sheet3_classes.keys()):
            for TYPE in list(sheet3_classes[SEASON].keys()):
                writer.writerow([SEASON,TYPE,
                                results[SEASON][TYPE][0],results[SEASON][TYPE][1],
                                results[SEASON][TYPE][2],results[SEASON][TYPE][3]])    
    csv_file.close()
    return True
    
