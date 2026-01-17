# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 17:10:28 2020

@author: ntr002
"""
import os
import csv
from . import calculate_flux as cf
from . import get_dictionaries as gd
from . import hydroloop as hl

def main(BASIN,unit_conversion=1):
    '''
    unit_conversion: 1 for TCM, 1000 for MCM, 1e6 for BCM or km3)
    '''
    #check requirements
#    requirements=gd.get_requirements_for_sheet(6)    
#    if not cf.check_requirement_sheet(BASIN,requirements):
#        print("ERROR: Data requirements for Sheet 6 are not fulfilled")
#        return None
    
    #create folder to save intermetidate data
    folder=os.path.join(BASIN['output_folder'],
                        'csv','timeseries')        
    if not os.path.exists(folder):
        os.makedirs(folder)
    output_file=os.path.join(folder,'sheet6_{0}.csv')
    #create folder to save sheet 6 csv
    sheet_folder=os.path.join(BASIN['output_folder'],'csv','sheet6') 
    if not os.path.exists(sheet_folder):
        os.makedirs(sheet_folder) 

    #Get sheet 6 classes
    classes=gd.get_sheet4_6_classes(version='1.0')
    #Calulate time-series data to fill in Sheet 6   
    data={}
    for variable in ['recharge','supply_gw','return_gw_from_gw','return_gw_from_sw']:
        df=cf.calc_flux_per_LU_class(
                BASIN['data_cube']['monthly'][variable],
                BASIN['data_cube']['monthly']['lu'],
                BASIN['gis_data']['basin_mask'],
                chunksize=BASIN['chunksize'],
                output=output_file.format(variable),
                lu_dictionary=classes
                )
        data[variable]=df/unit_conversion 
        
    df=cf.calc_flux_per_basin(
                BASIN['data_cube']['monthly']['bf'],
                BASIN['gis_data']['basin_mask'],
                chunksize=BASIN['chunksize'],
                output=output_file.format(variable)                
                )
    data['bf']=df/unit_conversion
    #Fill data in Sheet 6 csv
    monthly_csvs=[]
    for i in range(len(df.index)):
        year=df.index[i].year
        month=df.index[i].month
        entries={
                'RETURN_FLOW_GROUNDWATER':{},
                'VERTICAL_RECHARGE':{},
                'VERTICAL_GROUNDWATER_WITHDRAWALS':{},
                'RETURN_FLOW_SURFACEWATER':{},                
                }
        for lu in classes:
            entries['RETURN_FLOW_GROUNDWATER'][lu]=data['return_gw_from_gw'][lu].iloc[i]
            entries['VERTICAL_RECHARGE'][lu]=data['recharge'][lu].iloc[i]
            entries['VERTICAL_GROUNDWATER_WITHDRAWALS'][lu]=data['supply_gw'][lu].iloc[i]
            entries['RETURN_FLOW_SURFACEWATER'][lu]=data['return_gw_from_sw'][lu].iloc[i]
               
        entries_2={'CapillaryRise': '0.0', #assume no capillary rise
                         'DeltaS': '0.0',
                         'ManagedAquiferRecharge': '0.0',
                         'Baseflow': data['bf'].iloc[i][0],
                         'GWInflow': '0.0',
                         'GWOutflow': '0.0'}
        #write sheet 2 csv
        output_fh=os.path.join(sheet_folder,'sheet6_{0}_{1}.csv'.format(year,month))
        create_sheet6_csv(entries,entries_2,output_fh)    
        monthly_csvs.append(output_fh)
    ##calculate yearly csvs
    yearly_folder=os.path.join(sheet_folder,'yearly') 
    if not os.path.exists(yearly_folder):
        os.makedirs(yearly_folder) #create sheet1 folder  
    yearly_csvs=hl.calc_yearly_sheet(monthly_csvs,
                                     yearly_folder,
                                     hydroyear=BASIN['hydroyear'])
    return yearly_csvs
        
def create_sheet6_csv(entries, entries_2, output_fh):
    """
    Create a csv-file with all necessary values for Sheet 6.
    
    Parameters
    ----------
    entries : dict
        Dictionary with 'VERTICAL_RECHARGE', 'VERTICAL_GROUNDWATER_WITHDRAWALS',
        'RETURN_FLOW_GROUNDWATER' and 'RETURN_FLOW_SURFACEWATER' keys. Values are strings pointing to
        files of maps.
    entries_2 : dict
        Dictionary with 'CapillaryRise', 'DeltaS', 'ManagedAquiferRecharge', 'Baseflow',
        'GWInflow' and 'GWOutflow' as keys. Values are floats or 'nan.
    output_fh : str
        File to store results.
        
    Returns
    -------
    output_csv_fh : str
        String pointing to the newly created csv-file.
    """
  
    required_landuse_types = ['Wetlands','Greenhouses','Rainfed Crops','Residential','Industry','Natural Grasslands',
                              'Forests','Shrubland','Managed water bodies','Other (Non-Manmade)','Aquaculture','Forest Plantations',
                              'Irrigated crops','Other','Natural Water Bodies', 'Glaciers']              
    
    
    first_row = ['TYPE', 'SUBTYPE', 'VALUE']
    
    csv_file = open(output_fh, 'w')
    writer = csv.writer(csv_file, delimiter=';', lineterminator = '\n')
    writer.writerow(first_row)
    
    for SUBTYPE in list(entries.keys()):
        for TYPE in list(entries[SUBTYPE].keys()):
            row = [TYPE, SUBTYPE, entries[SUBTYPE][TYPE]]
            writer.writerow(row)
            if TYPE in required_landuse_types:
                required_landuse_types.remove(TYPE)
    
    for missing_landuse_type in required_landuse_types:
        writer.writerow([missing_landuse_type, 'VERTICAL_RECHARGE', 'nan'])
        writer.writerow([missing_landuse_type, 'VERTICAL_GROUNDWATER_WITHDRAWALS', 'nan'])
        writer.writerow([missing_landuse_type, 'RETURN_FLOW_GROUNDWATER', 'nan'])
        writer.writerow([missing_landuse_type, 'RETURN_FLOW_SURFACEWATER', 'nan'])
                   
    for key in list(entries_2.keys()):
        row = ['NON_LU_SPECIFIC', key, entries_2[key]]
        writer.writerow(row)
            
    csv_file.close()
    
    return True