# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 17:10:28 2020

@author: ntr002
"""
import os
import csv
import numpy as np
from . import calculate_flux as cf
from . import get_dictionaries as gd
from . import hydroloop as hl

def main(BASIN,unit_conversion=1000):
    '''
    unit_conversion: 1 for TCM, 1000 for MCM, 1e6 for BCM or km3)

    '''
    #check requirements
#    requirements=gd.get_requirements_for_sheet(4)    
#    if not cf.check_requirement_sheet(BASIN,requirements):
#        print("ERROR: Data requirements for Sheet 4 are not fulfilled")
#        return None
    #create folder to save intermetidate data
    folder=os.path.join(BASIN['output_folder'],
                        'csv','timeseries')        
    if not os.path.exists(folder):
        os.makedirs(folder)
    output_file=os.path.join(folder,'sheet4_{0}.csv')
    #create folder to save sheet 3 csv
    sheet_folder=os.path.join(BASIN['output_folder'],'csv','sheet4') 
    if not os.path.exists(sheet_folder):
        os.makedirs(sheet_folder) 
    #Get sheet 4 classes
    classes=gd.get_sheet4_6_classes(version='1.0')
    #Calulate time-series data to fill in Sheet 4   
    data={}
    variables=['supply_sw','supply_gw','etincr','return_sw','return_gw','demand']
    for variable in variables:
        df=cf.calc_flux_per_LU_class(
                BASIN['data_cube']['monthly'][variable],
                BASIN['data_cube']['monthly']['lu'],
                BASIN['gis_data']['basin_mask'],
                chunksize=BASIN['chunksize'],
                output=output_file.format(variable),
                lu_dictionary=classes
                )
        data[variable]=df/unit_conversion
    #Fill data in Sheet 4 csv
    monthly_csvs=[]
    for i in range(len(df.index)):
        year=df.index[i].year
        month=df.index[i].month
        results={'SUPPLY_SURFACEWATER' : {},
              'SUPPLY_GROUNDWATER' : {},
               'CONSUMED_ET' : {},
               'CONSUMED_OTHER' : {},
               'NON_CONVENTIONAL_ET' : {},
               'RECOVERABLE_SURFACEWATER' : {},
               'RECOVERABLE_GROUNDWATER' : {},
               'NON_RECOVERABLE_SURFACEWATER': {},
               'NON_RECOVERABLE_GROUNDWATER': {},
               'DEMAND': {}}
        for lu in classes:
            results['SUPPLY_SURFACEWATER'][lu]=data['supply_sw'][lu].iloc[i]              
            results['SUPPLY_GROUNDWATER'][lu]=data['supply_gw'][lu].iloc[i]   
            results['CONSUMED_ET'][lu]=data['etincr'][lu].iloc[i]
            results['CONSUMED_OTHER'][lu]=0.0
            results['NON_CONVENTIONAL_ET'][lu]=0.0
            results['RECOVERABLE_SURFACEWATER'][lu]=data['return_sw'][lu].iloc[i]
            results['RECOVERABLE_GROUNDWATER'][lu]=data['return_gw'][lu].iloc[i]
            results['NON_RECOVERABLE_SURFACEWATER'][lu]=0.0
            results['NON_RECOVERABLE_GROUNDWATER'][lu]=0.0
            results['DEMAND'][lu]=data['demand'][lu].iloc[i]

        #write sheet 4 csv
        output_fh=os.path.join(sheet_folder,'sheet4_{0}_{1}.csv'.format(year,month))
        create_sheet4_csv(results,output_fh)    
        monthly_csvs.append(output_fh)
    ##calculate yearly sheets
    yearly_folder=os.path.join(sheet_folder,'yearly') 
    if not os.path.exists(yearly_folder):
        os.makedirs(yearly_folder) #create sheet1 folder  
    yearly_csvs=hl.calc_yearly_sheet(monthly_csvs,
                                     yearly_folder,
                                     hydroyear=BASIN['hydroyear'])
    return yearly_csvs
        
def create_sheet4_csv(results, output_fh):
    """
    Create a csv-file used to generate sheet 4.
    
    Parameters
    ----------
    results : dict
        Dictionary with strings pointing to different tif-files, see example below.
    output_fh: str
        path to output file
    Returns
    -------
    output_csv_file : str
        newly created csv-file.
        
    Examples
    --------
    >>> results = {'SUPPLY_SURFACEWATER' : {'lu':'-'},
    >>>           'SUPPLY_GROUNDWATER' : {'lu':'-'},
    >>>           'CONSUMED_ET' : {'lu':'-'},
    >>>           'CONSUMED_OTHER' : {'lu':'-'},
    >>>           'NON_CONVENTIONAL_ET' : {'lu':'-'},
    >>>           'RECOVERABLE_SURFACEWATER' : {'lu':'-'},
    >>>           'RECOVERABLE_GROUNDWATER' : {'lu':'-'},
    >>>           'NON_RECOVERABLE_SURFACEWATER': {'lu':'-'},
    >>>           'NON_RECOVERABLE_GROUNDWATER': {'lu':'-'},
    >>>           'DEMAND': {'lu':'-'}}
    """
    required_landuse_types = ['Wetlands','Greenhouses','Rainfed Crops','Residential','Industry','Natural Grasslands',
                              'Forests','Shrubland','Managed water bodies','Other (Non-Manmade)','Aquaculture','Power and Energy','Forest Plantations',
                              'Irrigated crops','Other','Natural Water Bodies']
                              
       
    first_row = ['LANDUSE_TYPE'] + list(results.keys())
    
    csv_file = open(output_fh, 'w')
    writer = csv.writer(csv_file, delimiter=';', lineterminator = '\n')
    writer.writerow(first_row)
    
    for lu_type in list(results.values())[0].keys():
        row = list()
        row.append(lu_type)
        for flow in list(results.keys()):
            row.append(results[flow][lu_type] )
        writer.writerow(row)
        if lu_type in required_landuse_types: 
            required_landuse_types.remove(lu_type)
            
    for missing_lu_type in required_landuse_types:
        writer.writerow([missing_lu_type, 'nan', 'nan', 'nan', 'nan', 'nan', 'nan', 'nan', 'nan', 'nan', 'nan'])
    
    csv_file.close()
    
    return True