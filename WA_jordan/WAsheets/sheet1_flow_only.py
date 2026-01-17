# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 17:06:08 2020

@author: ntr002
"""
import os
import csv
import pandas as pd
from . import calculate_flux as cf
from . import get_dictionaries as gd
from . import hydroloop as hl

import numpy as np
import tempfile as tf
import shutil
import WA_Hyperloop.becgis as becgis

def main(BASIN,unit_conversion=1000):
    '''
    unit_conversion: 1 for TCM, 1000 for MCM, 1e6 for BCM or km3)
    '''
    #check requirements
#    requirements=gd.get_sheet_requirements(1)    
#    if not cf.check_requirement_sheet(BASIN,requirements):
#        print("ERROR: Data requirements for Sheet 1 are not fulfilled")
#        return None
    #get sheet 1 dictionary
    lu_dictionary=gd.get_sheet1_classes()  
    
    folder=os.path.join(BASIN['output_folder'],'csv','timeseries')        
    if not os.path.exists(folder):
        os.makedirs(folder)
    output_file=os.path.join(folder,'sheet1_{0}.csv')
    
    #Calulate yearly data to fill in Sheet 1
#     df_P=cf.calc_flux_per_basin(BASIN['data_cube']['monthly']['p'], 
#                                 BASIN['gis_data']['basin_mask'],
#                                 chunksize=BASIN['chunksize'],
#                                 output=output_file.format('basin_p_monthly'),
#                                 quantity='volume')
    
    df_P = pd.read_csv(output_file.format('basin_p_monthly'))
    # df_ET=cf.calc_flux_per_basin(BASIN['data_cube']['monthly']['et'], 
    #                             BASIN['gis_data']['basin_mask'], 
    #                             chunksize=BASIN['chunksize'],
    #                             output=output_file.format('basin_et_monthly'),
    #                             quantity='volume')
#     df_ETrain=cf.calc_flux_per_LU_class(BASIN['data_cube']['monthly']['etrain'], 
#                              BASIN['data_cube']['monthly']['lu'], 
#                              BASIN['gis_data']['basin_mask'],
#                      chunksize=BASIN['chunksize'], #option to process in chunks
#                      output=output_file.format('basin_etrain_monthly'), 
#                      #option to save output as csv                     
#                      lu_dictionary=lu_dictionary, #calc for LU categories
#                      quantity='volume')
    
    df_ETrain = pd.read_csv(output_file.format('basin_etrain_monthly'))
    
#     df_ETincr=cf.calc_flux_per_LU_class(BASIN['data_cube']['monthly']['etincr'], 
#                              BASIN['data_cube']['monthly']['lu'], 
#                              BASIN['gis_data']['basin_mask'],
#                      chunksize=BASIN['chunksize'], #option to process in chunks
#                      output=output_file.format('basin_etincr_monthly'), 
#                      #option to save output as csv                     
#                      lu_dictionary=lu_dictionary, #calc for LU categories
#                      quantity='volume')
    df_ETincr = pd.read_csv(output_file.format('basin_etincr_monthly'))
    
    #calc_non_utilizable
    df_non_util_ro = cf.calc_non_utilizable(BASIN['data_cube']['monthly']['p'],
                                      BASIN['data_cube']['monthly']['etrain'],
                                      BASIN['data_cube']['monthly']['etincr'],
                                      BASIN['data_cube']['monthly']['fraction'],
                                      BASIN['gis_data']['basin_mask'],
                                      chunksize=BASIN['chunksize'],
                                      unit_conversion=unit_conversion                                     
                                      )
    
    ##calculate reserved_outflow_actual part 1
    flows=dict()       
    if BASIN['ts_data']['q_outflow']['basin'] is not None:
        df=pd.read_csv(BASIN['ts_data']['q_outflow']['basin'],sep=';',index_col=0)                
        flows['q_outflow']= df[df.columns[0]]/unit_conversion
    else:
        flows['q_outflow']=0.
    
    q_out_avg = np.nanmean(flows['q_outflow'])
    
    lu_fh = BASIN['gis_data']['basin_mask']
    df_wpl = os.path.join(BASIN['gis_data']['wpl'])
    df_ewr = os.path.join(BASIN['gis_data']['environ_water_req'])
    
    #gray_water_fraction = 0.9029011
    gray_water_fraction = calc_basinmean(df_wpl, lu_fh)
    ewr_percentage = calc_basinmean(df_ewr, lu_fh)
    
    sheet_folder=os.path.join(BASIN['output_folder'],'csv','sheet1') 
    if not os.path.exists(sheet_folder):
        os.makedirs(sheet_folder) #create sheet1 folder       

    #Fill in Sheet 1 csv
    monthly_csvs=[]    
    for i in range(len(df_P)):
        results=dict()
        results['p_advection']=df_P[df_P.columns[0]].values[i]/unit_conversion
        results['landscape_et_plu']=df_ETrain[df_ETrain.columns[0]].values[i]/unit_conversion
        results['landscape_et_ulu']=df_ETrain[df_ETrain.columns[1]].values[i]/unit_conversion
        results['landscape_et_mlu']=df_ETrain[df_ETrain.columns[2]].values[i]/unit_conversion
        results['landscape_et_mwu']=df_ETrain[df_ETrain.columns[3]].values[i]/unit_conversion
                
        #calculate water balance
        P=results['p_advection']
        ET=results['landscape_et_plu']+results['landscape_et_ulu']\
         +results['landscape_et_mlu']+results['landscape_et_mwu']\
         +df_ETincr[df_ETincr.columns[0]].values[i]/unit_conversion\
         +df_ETincr[df_ETincr.columns[1]].values[i]/unit_conversion\
         +df_ETincr[df_ETincr.columns[2]].values[i]/unit_conversion\
         +df_ETincr[df_ETincr.columns[3]].values[i]/unit_conversion
                                 
        #Read time-series input
        ts_data_sheet1=['q_in_sw', 'q_in_gw', 'q_in_desal',
                        'q_outflow','q_out_sw','q_out_gw']
        for key in ts_data_sheet1:
            if BASIN['ts_data'][key]['basin'] is not None:
                df=pd.read_csv(BASIN['ts_data'][key]['basin'],sep=';',index_col=0)
                results[key]=df[df.columns[0]].values[i]/unit_conversion
            else:
                results[key]=0.
                
        
        Qin=results['q_in_sw']+results['q_in_gw']+results['q_in_desal']
        Qout=results['q_outflow']+results['q_out_sw']+results['q_out_gw']
        results['dS_error'] = 0
        
        #In case yearly dS is not available, calculate dS
        if 'dS' not in BASIN['ts_data'].keys():
            print('Calculating sheet 1 dS')
            results['dS']=calc_water_balance_residual(P,ET,Qin=Qin,Qout=Qout, Qdesal=results['q_in_desal'])
            print('P: {0}, ET:{1},Qin: {2}, Qout:{3}, dS:{4}'.format(P,ET,Qin,Qout,results['dS']))
            
        # in case yearly dS and q_outflow is available calculate dS_error
        elif BASIN['ts_data']['dS'] is not None and BASIN['ts_data']['q_outflow']['basin'] is not None:
            df=pd.read_csv(BASIN['ts_data']['dS'],sep=';',index_col=0)
            results['dS']=df[df.columns[0]].values[i]   
            results['dS_error']=calc_water_balance_residual(P,ET,Qin=Qin,Qout=Qout,dS=results['dS'])

        #in case yearly dS is available, calculate q_outflow
        else:
            df=pd.read_csv(BASIN['ts_data']['dS'],sep=';',index_col=0)
            results['dS']=df[df.columns[0]].values[i]            
            results['q_outflow']=calc_water_balance_residual(P,ET,
                   Qin=Qin,dS=results['dS'])
            
        results['manmade'] = (df_ETincr[df_ETincr.columns[3]].values[i] + results['q_in_desal'])/unit_conversion
        results['natural'] = df_ETincr[df_ETincr.columns[0]].values[i]/unit_conversion\
         +df_ETincr[df_ETincr.columns[1]].values[i]/unit_conversion\
         +df_ETincr[df_ETincr.columns[2]].values[i]/unit_conversion
         
        results['non_recoverable'] = gray_water_fraction * (results['q_outflow'] + results['q_out_sw']) # Mekonnen and Hoekstra (2015), Global Gray Water Footprint and Water Pollution Levels Related to Anthropogenic Nitrogen Loads to Fresh Water
                
        results['other'] = 0.0 
        other_fractions = {'Modified': 0.00,
                       'Managed':  1.00,
                       'Protected':0.00,
                       'Utilized': 0.00}    
                       
        non_recoverable_fractions = {'Modified': 0.00,
                                 'Managed':  1.00,
                                 'Protected':0.00,
                                 'Utilized': 0.00}  
        
        results['uf_plu'], results['uf_ulu'], results['uf_mlu'], results['uf_mwu'] = calc_utilizedflow(df_ETincr.iloc[i], results['other'], results['non_recoverable'], results['q_in_desal'], other_fractions, non_recoverable_fractions,unit_conversion)
                             
        results['calc_non_utilizable']=df_non_util_ro[1][i]
        
        ##To calculate reserved outflow part 2        
        results['reserved_outflow_demand'] = q_out_avg * ewr_percentage        
        
        net_inflow = results['p_advection'] + results['q_in_sw'] + results['q_in_gw'] + results['q_in_desal'] + (-results['dS'])
        consumed_water = ET + results['other'] + results['non_recoverable']
        non_consumed_water = net_inflow - consumed_water - results['q_in_desal']       
                    
        results['non_utilizable_outflow'] = min(non_consumed_water, max(0.0, results['calc_non_utilizable']))
        results['reserved_outflow_actual'] = min((non_consumed_water - results['non_utilizable_outflow']), results['reserved_outflow_demand'])
        results['utilizable_outflow'] = max(0.0, non_consumed_water - results['non_utilizable_outflow'] - results['reserved_outflow_actual'])
     
        #write sheet 1 csv
        #year value
        year=df_P.index[i].year
        month=df_P.index[i].month
        
        output_fh=os.path.join(sheet_folder,'sheet1_{0}_{1}.csv'.format(year,month))
        create_sheet1_csv(results, output_fh) #write results to sheet1 csv
        monthly_csvs.append(output_fh)
    ##calculate yearly sheets
    yearly_folder=os.path.join(sheet_folder,'yearly') 
    if not os.path.exists(yearly_folder):
        os.makedirs(yearly_folder) #create sheet1 folder  
    yearly_csvs=hl.calc_yearly_sheet(monthly_csvs,
                                     yearly_folder,
                                     hydroyear=BASIN['hydroyear'])
    return yearly_csvs

def calc_basinmean(perc_fh, lu_fh):
    """
    Calculate the mean of a map after masking out the areas outside an basin defined by
    its landusemap.
    
    Parameters
    ----------
    perc_fh : str
        Filehandle pointing to the map for which the mean needs to be determined.
    lu_fh : str
        Filehandle pointing to landusemap.
    
    Returns
    -------
    percentage : float
        The mean of the map within the border of the lu_fh.
    """
    output_folder = tf.mkdtemp()
    perc_fh = becgis.match_proj_res_ndv(lu_fh, np.array([perc_fh]), output_folder)
    EWR = becgis.open_as_array(perc_fh[0], nan_values = True)
    LULC = becgis.open_as_array(lu_fh, nan_values = True)
    EWR[np.isnan(LULC)] = np.nan
    percentage = np.nanmean(EWR)
    shutil.rmtree(output_folder)
    return percentage   

def calc_water_balance_residual(P,ET,dS=None,Qin=None,Qout=None, Qdesal=None):
    if Qin is not None:
        gross_inflow=P+Qin
    else:
        gross_inflow=P
        
    if dS is not None and Qout is not None:
        err= (ET + Qout - gross_inflow) - dS # dS is taking from grace csv
        err_fraction = err/P
        return err_fraction
    
    if dS is not None:
        Qout=gross_inflow-ET-dS
        return Qout
    
    if Qout is not None:
        dS=gross_inflow-ET-Qout-Qdesal
        return dS

def calc_utilizedflow(incremental_et, other, non_recoverable, q_in_desal, other_fractions, non_recoverable_fractions, unit_conversion):
    """
    Calculate the utilized flows per landuse category from total incremental ET, non_recoverable water and other.
    
    Parameters
    ----------
    incremental_et : dict
        Incremental ET per landuse category (i.e. Protected, Utilized, Modified and Managed).
    other : dict
        Other water consumptions per landuse category (i.e. Protected, Utilized, Modified and Managed).
    non_recoverable : dict
        Non recoverable water consumption per landuse category (i.e. Protected, Utilized, Modified and Managed).
    other_fractions : dict
        Fractions describing how much of other water consumption should be assigned to each category.
    non_recoverable_fractions : dict
        Fractions describing how much of non_recoverable water consumption should be assigned to each category.
        
    Returns
    -------
    uf_plu : float
        Utilized Flow for Protected LU.
    uf_ulu : float
        Utilized Flow for Utilized LU.
    uf_mlu : float
        Utilized Flow for Modified LU.
    uf_mwu : float
        Utilized Flow for Managed Water Use.
    """
    #assert np.sum(other_fractions.values()) == 1.00, "Fractions for other should sum to 1.00."
    #assert np.sum(non_recoverable_fractions.values()) == 1.00, "Fractions for non_recoverable should sum to 1.00."   
    
    #np.array(incremental_et.values()) + np.array(other_fractions.values()) * other + np.array(non_recoverable_fractions.values()) * non_recoverable
    
    uf_plu = incremental_et['PROTECTED']/unit_conversion + other_fractions['Protected'] * other + non_recoverable_fractions['Protected'] * non_recoverable
    uf_ulu = incremental_et['UTILIZED']/unit_conversion + other_fractions['Utilized'] * other + non_recoverable_fractions['Utilized'] * non_recoverable
    uf_mlu = incremental_et['MODIFIED']/unit_conversion + other_fractions['Modified'] * other + non_recoverable_fractions['Modified'] * non_recoverable
    uf_mwu = incremental_et['MANAGED']/unit_conversion  + q_in_desal +other_fractions['Managed'] * other + non_recoverable_fractions['Managed'] * non_recoverable
        
    return uf_plu, uf_ulu, uf_mlu, uf_mwu

def create_sheet1_csv(results, output_fh):
    """
    Create the csv-file needed to plot sheet 1.
    
    Parameters
    ----------
    results : dict
        Dictionary generated by calc_sheet1.
    output_fh : str
        Filehandle to store the csv-file.
    """
    first_row = ['CLASS', 'SUBCLASS', 'VARIABLE', 'VALUE']
    
    if not os.path.exists(os.path.split(output_fh)[0]):
        os.makedirs(os.path.split(output_fh)[0])
    
    csv_file = open(output_fh, 'w')
    writer = csv.writer(csv_file, delimiter=';', lineterminator = '\n')
    writer.writerow(first_row)

    writer.writerow(['INFLOW', 'PRECIPITATION', 'Rainfall',
                     '{0}'.format(results['p_advection'])])
    writer.writerow(['INFLOW', 'PRECIPITATION', 'Snowfall',
                     0.])
    writer.writerow(['INFLOW', 'PRECIPITATION', 'Precipitation recycling',
                     0.])
    writer.writerow(['INFLOW', 'SURFACE WATER', 'Main riverstem',
                     '{0}'.format(results['q_in_sw'])])
    writer.writerow(['INFLOW', 'SURFACE WATER', 'Tributaries',
                     0.])
    writer.writerow(['INFLOW', 'SURFACE WATER', 'Utilized surface water',
                     0.])
    writer.writerow(['INFLOW', 'SURFACE WATER', 'Flood', 
                     0.])
    writer.writerow(['INFLOW', 'GROUNDWATER', 'Natural', 
                     '{0}'.format(results['q_in_gw'])])
    writer.writerow(['INFLOW', 'GROUNDWATER', 'Utilized',
                     0.])
    writer.writerow(['INFLOW', 'OTHER', 'Desalinized', 
                     '{0}'.format(results['q_in_desal'])])
    writer.writerow(['STORAGE', 'CHANGE', 'Surface storage', 
                     '{0}'.format(-results['dS'])])
    writer.writerow(['ERROR', 'ERROR', 
                     '{0}'.format(-results['dS_error'])])
    writer.writerow(['STORAGE', 'CHANGE', 'Storage in sinks',
                     0.])
    writer.writerow(['OUTFLOW', 'ET LANDSCAPE', 'Protected',
                     '{0}'.format(results['landscape_et_plu'])])
    writer.writerow(['OUTFLOW', 'ET LANDSCAPE', 'Utilized',
                     '{0}'.format(results['landscape_et_ulu'])])
    writer.writerow(['OUTFLOW', 'ET LANDSCAPE', 'Modified',
                     '{0}'.format(results['landscape_et_mlu'])])
    writer.writerow(['OUTFLOW', 'ET LANDSCAPE', 'Managed',
                     '{0}'.format(results['landscape_et_mwu'])])
    writer.writerow(['OUTFLOW', 'ET UTILIZED FLOW', 'Protected',
                     '{0}'.format(results['uf_plu'])])
    writer.writerow(['OUTFLOW', 'ET UTILIZED FLOW', 'Utilized',
                     '{0}'.format(results['uf_ulu'])])
    writer.writerow(['OUTFLOW', 'ET UTILIZED FLOW', 'Modified',
                     '{0}'.format(results['uf_mlu'])])
    writer.writerow(['OUTFLOW', 'ET UTILIZED FLOW', 'Managed',
                     '{0}'.format(results['uf_mwu'])])        
    writer.writerow(['OUTFLOW', 'ET INCREMENTAL', 'Manmade',
                     '{0}'.format(results['manmade'])])  
    writer.writerow(['OUTFLOW', 'ET INCREMENTAL', 'Natural',
                     '{0}'.format(results['natural'])])
    writer.writerow(['OUTFLOW', 'SURFACE WATER', 'Main riverstem',
                     '{0}'.format(results['q_outflow'])])
    writer.writerow(['OUTFLOW', 'SURFACE WATER', 'Tributaries', 
                     0.])  
    writer.writerow(['OUTFLOW', 'SURFACE WATER', 'Utilized surface water',
                     0.])  
    writer.writerow(['OUTFLOW', 'SURFACE WATER', 'Flood',
                     0.])
    writer.writerow(['OUTFLOW', 'SURFACE WATER', 'Interbasin transfer',
                     '{0}'.format(results['q_out_sw'])])
    writer.writerow(['OUTFLOW', 'GROUNDWATER', 'Natural', 
                     '{0}'.format(results['q_out_gw'])]) 
    writer.writerow(['OUTFLOW', 'GROUNDWATER', 'Utilized', 
                     0.])
    writer.writerow(['OUTFLOW', 'OTHER', 'Non-utilizable',
                     '{0}'.format(results['non_utilizable_outflow'])])
    writer.writerow(['OUTFLOW', 'OTHER', 'Other', 
                     0.])
    writer.writerow(['OUTFLOW', 'RESERVED', 'Commited',
                     '{0}'.format(results['reserved_outflow_actual'])]) 
    writer.writerow(['OUTFLOW', 'RESERVED', 'Navigational',
                     0.]) 
    writer.writerow(['OUTFLOW', 'RESERVED', 'Environmental',
                     0.]) 
    
    csv_file.close()
    
