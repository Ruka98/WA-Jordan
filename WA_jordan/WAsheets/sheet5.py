# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 17:10:28 2020

@author: ntr002
"""
import os

import csv
import pandas as pd
import numpy as np
from . import calculate_flux as cf
from . import get_dictionaries as gd
from . import hydroloop as hl

def main(BASIN,unit_conversion=1):
    '''
    unit_conversion: 1 for TCM, 1000 for MCM, 1e6 for BCM or km3)
    '''
    ### check requirements
#    requirements=gd.get_requirements_for_sheet(5)    
#    if not cf.check_requirement_sheet(BASIN,requirements):
#        sys.exit("ERROR: Data requirements for Sheet 5 are not fulfilled")
    #create folder to save intermetidate data
    folder=os.path.join(BASIN['output_folder'],
                        'csv','timeseries')        
    if not os.path.exists(folder):
        os.makedirs(folder)
    output_file=os.path.join(folder,'sheet5_{0}.csv')
    #create folder to save sheet 3 csv
    sheet_folder=os.path.join(BASIN['output_folder'],'csv','sheet5') 
    if not os.path.exists(sheet_folder):
        os.makedirs(sheet_folder) 
    ### Get LU classes dictionary
    lu_dict=gd.get_sheet1_classes()  
    
    ### Calulate monthly data to fill in Sheet 5  
    data={'basin':dict()}
    # Full basin
    for variable in ['sro','bf','supply_sw']:
        df=cf.calc_flux_per_LU_class(
                 BASIN['data_cube']['monthly'][variable], 
                 BASIN['data_cube']['monthly']['lu'], 
                 BASIN['gis_data']['basin_mask'],
#                 chunksize=BASIN['chunksize'], 
                 output=output_file.format('{0}_{1}'.format('basin',variable)), 
                 lu_dictionary=lu_dict, #calc for LU categories
                 quantity='volume')
        data['basin'][variable]=df/unit_conversion
                
    for variable in ['return_sw','return_sw_from_gw','return_sw_from_sw']:        
        df=cf.calc_flux_per_basin(
                 BASIN['data_cube']['monthly'][variable], 
                 BASIN['gis_data']['basin_mask'],
#                 chunksize=BASIN['chunksize'], 
                 output=output_file.format('{0}_{1}'.format('basin',variable)),
                 quantity='volume')
        data['basin'][variable]=df/unit_conversion

    #connection between subbasin
    sb_codes=BASIN['gis_data']['subbasin_mask'].keys()
    dico_in = BASIN['params']['dico_in']
    dico_out = BASIN['params']['dico_out']    

    basin_total_outflow=pd.read_csv(BASIN['ts_data']['q_outflow']['basin'],
                                          sep=';',index_col=0)/unit_conversion
    basin_inflows=basin_total_outflow*0
    #Sub basins
    for sb in sb_codes:
        data[sb]=dict()
        for variable in ['sro','bf','supply_sw']:
            df=cf.calc_flux_per_LU_class(
                     BASIN['data_cube']['monthly'][variable], 
                     BASIN['data_cube']['monthly']['lu'], 
                     BASIN['gis_data']['subbasin_mask'][sb],
#                     chunksize=BASIN['chunksize'], 
                     output=output_file.format('subbasin_{0}_{1}'.format(sb,variable)), 
                     lu_dictionary=lu_dict, #calc for LU categories
                     quantity='volume')
            data[sb][variable]=df/unit_conversion
        for variable in ['return_sw','return_sw_from_gw','return_sw_from_sw']:        
            df=cf.calc_flux_per_basin(
                     BASIN['data_cube']['monthly'][variable], 
                     BASIN['gis_data']['subbasin_mask'][sb],
#                     chunksize=BASIN['chunksize'], 
                     output=output_file.format('subbasin_{0}_{1}'.format(sb,variable)),
                     quantity='volume')
            data[sb][variable]=df/unit_conversion
        ##read timeseries
        #inflow
        if len(dico_in[sb])==0: #no inflow
            inflow=data[sb]['sro']*0 
        else: #1 or more inflows
            for i in range(len(dico_in[sb])):            
                if dico_in[sb][i] == 0: #inflow from outside
                    df_inflow=pd.read_csv(BASIN['ts_data']['q_in_sw'][sb],
                                          sep=';',index_col=0)/unit_conversion
                    basin_inflows=basin_inflows+df_inflow
                else: #inflow from upstream subbasin                  
                    subbasin_in=BASIN['params']['dico_in'][sb][i]
                    df_inflow=pd.read_csv(
                            BASIN['ts_data']['q_outflow'][subbasin_in],
                                          sep=';',index_col=0)/unit_conversion 
                    df_inflow=df_inflow
                    #assuming that outflow of upstream subbasin was calculated before
                if i == 0:
                    inflow=df_inflow
                else:
                    inflow=inflow+df_inflow    
        data[sb]['inflows']=inflow
        #outflow
        data[sb]['total_outflow']=pd.read_csv(BASIN['ts_data']['q_outflow'][sb],
                                          sep=';',index_col=0)/unit_conversion
        #interbasin transfer
        if BASIN['ts_data']['q_out_sw'][sb] is not None:
            data[sb]['interbasin_transfers']=pd.read_csv(
                    BASIN['ts_data']['q_out_sw'][sb],
                    sep=';',index_col=0)/unit_conversion
        else:
            data[sb]['interbasin_transfers']=data[sb]['inflows']*0
        #dS_sw
        if BASIN['ts_data']['dS_sw'][sb] is not None:
            data[sb]['deltaS']=pd.read_csv(
                    BASIN['ts_data']['dS_sw'][sb],
                    sep=';',index_col=0)/unit_conversion
        else:
            data[sb]['deltaS']=data[sb]['inflows']*0
        # add to basin interbasin_transfers and deltaS
        if sb==1:
            basin_interbasin_transfers=data[sb]['interbasin_transfers']
            basin_deltaS=data[sb]['deltaS']
        else:
            basin_interbasin_transfers=basin_interbasin_transfers\
            +data[sb]['interbasin_transfers']
            basin_deltaS=basin_deltaS+data[sb]['deltaS']

    #basin inflow, outflow, dS, interbasin_transfers
    data['basin']['inflows']=basin_inflows
    data['basin']['total_outflow']=basin_total_outflow
    data['basin']['interbasin_transfers']=basin_interbasin_transfers
    data['basin']['deltaS']=basin_deltaS

    ### Fill data in Sheet 5 csv
    monthly_csvs=[]
    for i in range(len(data['basin']['sro'])):
        year=data['basin']['sro'].index[i].year
        month=data['basin']['sro'].index[i].month
        results=Vividict()
        for sb in data.keys():
            for lu in lu_dict:
                results['surf_runoff'][sb][lu]=data[sb]['sro'][lu].values[i] 
                results['base_runoff'][sb][lu]=data[sb]['bf'][lu].values[i] 
            results['total_runoff'][sb]=np.nansum([results['surf_runoff'][sb][lu] for lu in lu_dict])\
                        +np.nansum([results['base_runoff'][sb][lu] for lu in lu_dict])
            results['withdrawls'][sb]['man']=data[sb]['supply_sw']['MANAGED'].values[i]                 
            results['withdrawls'][sb]['natural']=\
                            data[sb]['supply_sw']['PROTECTED'].values[i]\
                            +data[sb]['supply_sw']['UTILIZED'].values[i]\
                            +data[sb]['supply_sw']['MODIFIED'].values[i]
            results['return_sw_sw'][sb]=data[sb]['return_sw_from_sw'].values[i][0]
            results['return_gw_sw'][sb]=data[sb]['return_sw_from_gw'].values[i][0]
            results['inflows'][sb]=data[sb]['inflows'].values[i][0]
            results['total_outflow'][sb]=data[sb]['total_outflow'].values[i][0]
            results['interbasin_transfers'][sb]=data[sb]['interbasin_transfers'].values[i][0]
            results['deltaS'][sb]=data[sb]['deltaS'].values[i][0]
        
        #write sheet 5 csv
        output_fh=os.path.join(sheet_folder,'sheet5_{0}_{1}.csv'.format(year,month))
        create_sheet5_csv(results,output_fh)    
        monthly_csvs.append(output_fh)
    ##calculate yearly csvs
    yearly_folder=os.path.join(sheet_folder,'yearly') 
    if not os.path.exists(yearly_folder):
        os.makedirs(yearly_folder) #create sheet1 folder  
    yearly_csvs=hl.calc_yearly_sheet(monthly_csvs,
                                     yearly_folder,
                                     hydroyear=BASIN['hydroyear'])
    return yearly_csvs

class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value        

def create_sheet5_csv(dresults, output_fh):
    """
    Create the csv-file for sheet 5.

    Parameters
    ----------
    results : dict
        Dictionary of results generated in sheet5_run.py
    output_fh : str
        Filehandle to store the csv-file.
    """
    first_row = ['SUBBASIN', 'VARIABLE', 'VALUE', 'UNITS']
    if not os.path.exists(os.path.split(output_fh)[0]):
        os.makedirs(os.path.split(output_fh)[0])
    csv_file = open(output_fh, 'w')
    writer = csv.writer(csv_file, delimiter=';', lineterminator = '\n')
    writer.writerow(first_row)
    lu_classes = ['PROTECTED', 'UTILIZED', 'MODIFIED', 'MANAGED']
    for sb in list(dresults['surf_runoff'].keys()):
        writer.writerow([sb, 'Inflow', 
                         '{0}'.format(dresults['inflows'][sb]), 'MCM'])
        for lu_class in lu_classes:
            writer.writerow([sb, 'Fast Runoff: '+lu_class, 
                             '{0}'.format(dresults['surf_runoff'][sb][lu_class]), 'MCM'])
            writer.writerow([sb, 'Slow Runoff: ' +lu_class, 
                             '{0}'.format(dresults['base_runoff'][sb][lu_class]), 'MCM'])
        writer.writerow([sb, 'Total Runoff', 
                         '{0}'.format(dresults['total_runoff'][sb]), 'MCM'])
        writer.writerow([sb, 'SW withdr. manmade', 
                         '{0}'.format(dresults['withdrawls'][sb]['man']), 'MCM'])
        writer.writerow([sb, 'SW withdr. natural', 
                         '{0}'.format(dresults['withdrawls'][sb]['natural']), 'MCM'])
        writer.writerow([sb, 'SW withdr. total', 
                 '{0}'.format(dresults['withdrawls'][sb]['man']+dresults['withdrawls'][sb]['natural']),
                 'MCM'])
        writer.writerow([sb, 'Return Flow SW', 
                         '{0}'.format(dresults['return_sw_sw'][sb]), 'MCM'])
        writer.writerow([sb, 'Return Flow GW', 
                         '{0}'.format(dresults['return_gw_sw'][sb]), 'MCM'])
        writer.writerow([sb, 'Total Return Flow', 
                     '{0}'.format(dresults['return_sw_sw'][sb]+dresults['return_gw_sw'][sb]), 'MCM'])
        writer.writerow([sb, 'Outflow: Total', 
                         '{0}'.format(dresults['total_outflow'][sb]), 'MCM'])
        writer.writerow([sb, 'Outflow: Committed', 'nan', 'MCM'])
        writer.writerow([sb, 'Outflow: Non Recoverable', 'nan', 'MCM'])
        writer.writerow([sb, 'Outflow: Non Utilizable', 'nan', 'MCM'])
        writer.writerow([sb, 'Outflow: Utilizable', 'nan', 'MCM'])
        writer.writerow([sb,'Interbasin Transfer',
                         '{0}'.format(dresults['interbasin_transfers'][sb]),'MCM'])
        writer.writerow([sb, 'SW storage change', 
                         '{0}'.format(dresults['deltaS'][sb]), 'MCM'])
    csv_file.close()
    return

