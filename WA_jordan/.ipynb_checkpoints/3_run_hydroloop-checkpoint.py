# -*- coding: utf-8 -*-
"""

"""
import os
import sys
sys.path.append(r'/efs/CWA/scripts')
import pandas as pd

from WAsheets import calculate_flux as cf
from WAsheets import hydroloop as hl

#%%
wp_folder=r"/efs/CWA/netcdf_files" #folder with nc files from water balance model
BASIN={
       'name': 'AFR',
       'hydroyear':'A-DEC', #Water year end month
       'chunksize':None,
       'unit_conversion':1e6, #1e3 for input data in MCM, 1e6 for input data in km3
       'output_folder':r"/efs/CWA/hydroloop_results",
       'gis_data':{
               'basin_mask': r'/efs/CWA/static_datasets/basin_mask/AFR_basinmask_1km.tif',
               'subbasin_mask':{
                       1: r"/efs/CWA/static_datasets/basin_mask/AFR_basinmask_1km.tif"                       
                       },
               'dem':r"/efs/CWA/static_datasets/DEM/DEM_HydroShed_1km_AFR.tif",
               'aeisw':r"/efs/CWA/static_datasets/AEISW/AFR_gmia_v5_aei_pct_1km.tif", #area equipped with surface water irrigation percentage
               'population':r"/efs/CWA/static_datasets/Population/AFR_PPP_2015_adj_v2_1km.tif",
               'wpl':r"/efs/CWA/static_datasets/WPL/WPL_Max1.tif",
               'environ_water_req': r"/efs/CWA/static_datasets/EWR/EWR.tif"
               },
       'data_cube':{
           'monthly':{
               'p':os.path.join(wp_folder,
                                          'AFR_P_CHIRPS.nc'),
                'etref':os.path.join(wp_folder,
                                          'AFR_ETref_WA.nc'),
               'et':os.path.join(wp_folder,
                                          'AFR_ETa_SSEBop.nc'),
               'i':os.path.join(wp_folder,
                                          'i_monthly.nc'),
               't':None,
               'e':None,
               'nrd':os.path.join(wp_folder,
                                          'nRD_monthly.nc'),
               'etincr':os.path.join(wp_folder,
                                          'etincr_monthly.nc'),
               'etrain':os.path.join(wp_folder,
                                          'etrain_monthly.nc'),
               'lai':os.path.join(wp_folder,
                                          'AFR_LAI_MOD15.nc'),
              'ndm':os.path.join(wp_folder,
                                          'AFR_NDM_ProbaV.nc'),
             'sro':os.path.join(wp_folder,
                                         'sro_monthly.nc'),
             'sroincr':os.path.join(wp_folder,
                                          'd_sro_monthly.nc'),
             'perc':os.path.join(wp_folder,
                                          'perco_monthly.nc'),
             'percincr':os.path.join(wp_folder,
                                          'd_perco_monthly.nc'),
             'bf':os.path.join(wp_folder,
                                          'bf_monthly.nc'),
            'supply':os.path.join(wp_folder,
                                          'supply_monthly.nc')
               },
           'yearly':{
                'lu':os.path.join(wp_folder,
                                          'AFR_LU_WA.nc'),
                   }      
                     },
        'ts_data':{
                'q_in_sw':{
                        'basin':None,
                        1:None, #unit MCM
                        2:None,
                        },
                'q_in_gw':{
                        'basin':None,
                        1:None, #unit MCM
                        2:None,
                        },
                'q_in_desal':{
                        'basin':None,
                        1:None, #unit MCM
                        2:None,
                        },
                'q_outflow':{ #river flow
                        'basin':None,
                        1:None,
                        2:None
                        },
                'q_out_sw':{ #interbasin transfer
                        'basin':None,
                        1:None,
                        2:None,
                        },
                'q_out_gw':{ #interbasin transfer
                        'basin':None,
                        1:None,
                        2:None,
                        },
                'dS_sw':{
                        'basin':None,
                        1:None, #unit MCM
                        2:None,
                        },
                                
                },
        'params':{
            'crops':{#lu_code: [r'seasons_dates.csv','Crop_type']
                    35.0: [r'C:\_WA\wasa\basin_data\Cimanuk\static_datasets\growing seasons\rice_rain_java.txt','N/A'],
                    54.0: [r'C:\_WA\wasa\basin_data\Cimanuk\static_datasets\growing seasons\rice_irrigated_java.txt','N/A'],    
                    52.0: [r'C:\_WA\wasa\basin_data\Cimanuk\static_datasets\growing seasons\palm_perennial.txt','N/A'],
                    33.0: [r'C:\_WA\wasa\basin_data\Cimanuk\static_datasets\growing seasons\palm_perennial.txt','N/A']             
                    },
            'dico_in':{1:[]},
            'dico_out':{1:[0]},
            'residential_sw_supply_fraction':0.6,
            'wcpc':110, #Water consumption per capita per day in [liter/person/day]
            'wcpc_min':100, #minimum demand
            'fraction_xs':[4,25,4,25]
        }
        
       }
            

#%% Calculate hydroloop datacube

### Resample yearly LU to monthly netCDF
yearly_nc=BASIN['data_cube']['yearly']['lu']
sample_nc=BASIN['data_cube']['monthly']['p']
monthly_nc=cf.resample_to_monthly_dataset(yearly_nc, sample_nc,
                                start_month=0,
                                output=None,
                                chunksize=None) 
BASIN['data_cube']['monthly']['lu']=monthly_nc
### Split ETI
e_nc,i_nc,t_nc=hl.split_ETI(et_nc=BASIN['data_cube']['monthly']['et'],
                            i_nc=BASIN['data_cube']['monthly']['i'],
                            t_nc=BASIN['data_cube']['monthly']['t'],
                              p_nc=BASIN['data_cube']['monthly']['p'],
                              lai_nc=BASIN['data_cube']['monthly']['lai'],
                              nrd_nc=BASIN['data_cube']['monthly']['nrd'],
                              ndm_nc=BASIN['data_cube']['monthly']['ndm']
              )        
BASIN['data_cube']['monthly']['i']=i_nc
BASIN['data_cube']['monthly']['t']=t_nc
BASIN['data_cube']['monthly']['e']=e_nc

### split supply
sw_supply_fraction_nc=hl.calc_sw_supply_fraction_by_LU(BASIN['data_cube']['monthly']['lu'],
                                                       BASIN['gis_data']['aeisw'])
sw_supply_nc,gw_supply_nc=hl.split_flow(BASIN['data_cube']['monthly']['supply'],
              fraction_nc=sw_supply_fraction_nc)
### demand of land surface
demand_nc=hl.calc_land_surface_water_demand(BASIN['data_cube']['monthly']['lai'],
                                  BASIN['data_cube']['monthly']['etref'],
                                  BASIN['data_cube']['monthly']['p'],
                                  BASIN['data_cube']['monthly']['lu'])
### non-consumed supply or return flow
return_nc=hl.substract_flow(BASIN['data_cube']['monthly']['supply'],
                                  BASIN['data_cube']['monthly']['etincr'],
                                  name='return')
### split return by sroincr/total_incremental ratio
sw_return_fraction_nc=hl.calc_sw_return_fraction(
        BASIN['data_cube']['monthly']['sroincr'],
        BASIN['data_cube']['monthly']['percincr'])
sw_return_nc,gw_return_nc=hl.split_flow(return_nc,fraction_nc=sw_return_fraction_nc)

### residential supply and demand
residential_supply_nc=hl.calc_residential_water_consumption(
        BASIN['gis_data']['population'],
        BASIN['gis_data']['basin_mask'],
        BASIN['data_cube']['monthly']['lu'],
        wcpc=110,
        flow_type='supply')
residential_demand_nc=hl.calc_residential_water_consumption(
        BASIN['gis_data']['population'],
        BASIN['gis_data']['basin_mask'],
        BASIN['data_cube']['monthly']['lu'],
        wcpc=100,
        flow_type='demand')

### split return flow by source sw/gw
return_sw_from_sw_nc,return_sw_from_gw_nc=hl.split_flow(
        sw_return_nc,fraction_nc=sw_supply_fraction_nc)
return_gw_from_sw_nc,return_gw_from_gw_nc=hl.split_flow(
        gw_return_nc,fraction_nc=sw_supply_fraction_nc)

### split residential supply by sw/gw fraction
f=BASIN['params']['residential_sw_supply_fraction']
sw_residential_supply_nc,gw_residential_supply_nc=hl.split_flow(
        residential_supply_nc,fraction=f)
### add residential sw/gw supply to sw/gw supply and sw/gw return
BASIN['data_cube']['monthly']['supply_sw']=hl.add_flow(
        sw_supply_nc,sw_residential_supply_nc,name='total_sw_supply')
BASIN['data_cube']['monthly']['supply_gw']=hl.add_flow(
        gw_supply_nc,gw_residential_supply_nc,name='total_gw_supply')

#assume that residential supply from sw return to sw, from gw return to gw
BASIN['data_cube']['monthly']['return_sw_from_sw']=hl.add_flow(
        return_sw_from_sw_nc,sw_residential_supply_nc,name='total_return_sw_from_sw')
BASIN['data_cube']['monthly']['return_gw_from_gw']=hl.add_flow(
        return_gw_from_gw_nc,gw_residential_supply_nc,name='total_return_gw_from_gw')

BASIN['data_cube']['monthly']['return_sw_from_gw']=return_sw_from_gw_nc
BASIN['data_cube']['monthly']['return_gw_from_sw']=return_gw_from_sw_nc
### add residential demand to total demand
BASIN['data_cube']['monthly']['demand']=hl.add_flow(
        demand_nc,residential_demand_nc,name='total_demand')
### total return and supply
BASIN['data_cube']['monthly']['return_sw']=hl.add_flow(
        BASIN['data_cube']['monthly']['return_sw_from_gw'],
        BASIN['data_cube']['monthly']['return_sw_from_sw'],
        name='return_sw')
BASIN['data_cube']['monthly']['return_gw']=hl.add_flow(
        BASIN['data_cube']['monthly']['return_gw_from_gw'],
        BASIN['data_cube']['monthly']['return_gw_from_sw'],
        name='return_gw')
BASIN['data_cube']['monthly']['supply']=hl.add_flow(
        BASIN['data_cube']['monthly']['supply_sw'],
        BASIN['data_cube']['monthly']['supply_gw'],
        name='total_supply')
### calculate recharge
BASIN['data_cube']['monthly']['recharge']=BASIN['data_cube']['monthly']['perc']

BASIN['data_cube']['monthly']['fraction'] = hl.calc_fractions(BASIN['data_cube']['monthly']['p'],
                                                              dem=BASIN['gis_data']['dem'],
                                                              lu=BASIN['data_cube']['yearly']['lu'],
                                                              fraction_altitude_xs=BASIN['params']['fraction_xs'])

#%% Calculate monthly discharge timeseries
### Calculate subbasin-wide timeseries

for sb in BASIN['gis_data']['subbasin_mask']:
    subbasin={}
    for key in ['sro','return_sw','bf','supply_sw']:
        output=os.path.join(BASIN['output_folder'],
                            'subbasin_{0}_{1}.csv'.format(sb,key))
        df=cf.calc_flux_per_basin(BASIN['data_cube']['monthly'][key],
                                BASIN['gis_data']['subbasin_mask'][sb],
                                output=output)
        subbasin[key]=df        
    # read subbasin inflow
    if len(BASIN['params']['dico_in'][sb])==0: #no inflow
        inflow=None 
    else: #1 or more inflows
        for i in range(len(BASIN['params']['dico_in'][sb])):            
            if BASIN['params']['dico_in'][sb][i] == 0: #inflow from outside
                needed_params = ['q_in_desal','q_in_sw','q_in_gw'] #check only inflows
                t = 0
                for q_in in BASIN['ts_data'].keys():
                    if (q_in in needed_params) and (BASIN['ts_data'][q_in][sb] != None):       #check csv                 
                        df_inflow_ = pd.read_csv(BASIN['ts_data'][q_in][sb],
                                      sep=';',index_col=0)
                        
                        if t == 0:
                            df_inflow = df_inflow_
                        else:
                            df_inflow = df_inflow + df_inflow_
                        
                        t += 1
                        
                if t == 0:                                
                    print('Warning, missing inflow textfiles, proceeding without inflow textfiles')
                 
                         
            else: #inflow from upstream subbasin                  
                subbasin_in=BASIN['params']['dico_in'][sb][i]
                df_inflow=pd.read_csv(
                        BASIN['ts_data']['q_outflow'][subbasin_in],
                                      sep=';',index_col=0) 
                # df_inflow = pd.read_csv(BASIN['ts_data']['q_in_sw'][subbasin_in],
                #                       sep=';',index_col=0)                
                #assuming that outflow of upstream subbasin was calculated before
            if i == 0:
                inflow=df_inflow
            else:
                inflow=inflow+df_inflow    
    
    ## Interbasin transfer outflow
    if BASIN['ts_data']['q_out_sw'][sb] == None:
        q_out_sw=None
    else: 
        q_out_sw = pd.read_csv(
                        BASIN['ts_data']['q_out_sw'][sb],
                                      sep=';',index_col=0)

    # calculate sw discharge and dS from pixel-based model results
    output=os.path.join(BASIN['output_folder'],
                        'subbasin_{0}_{1}.csv'.format(sb,'{0}'))
    discharge,dS_sw=hl.calc_sw_from_wp(subbasin['sro'],
                                        subbasin['return_sw'],
                                        subbasin['bf'],
                                        subbasin['supply_sw'],
                                        inflow=inflow,
                                        q_out_sw = q_out_sw,
                                        output=output,
                                        outflow=True, #not endorheic basin
                                        plot=True
                                        )
    BASIN['ts_data']['q_outflow'][sb]=discharge
    BASIN['ts_data']['dS_sw'][sb]=dS_sw    
    inflow = None
    
# outflow of basin is outflow of downstream subbasin   
for sb in BASIN['params']['dico_out']:
    if 0 in BASIN['params']['dico_out'][sb]: #if subbasin outflow is basin outflow
        BASIN['ts_data']['q_outflow']['basin']=BASIN['ts_data']['q_outflow'][sb]

# dS_sw of basin is sum of dS_sw of all subbasins
for i in range(len(BASIN['gis_data']['subbasin_mask'])):
    sb=list(BASIN['gis_data']['subbasin_mask'].keys())[i]
    df=pd.read_csv(BASIN['ts_data']['dS_sw'][sb],sep=';',index_col=0)
    if i==0:
        dS_sw=df
    else:
        dS_sw=dS_sw+df
dS_sw.to_csv(os.path.join(BASIN['output_folder'],
                        'basin_dS_sw.csv'),sep=';')
BASIN['ts_data']['dS_sw']['basin']=os.path.join(BASIN['output_folder'],
                        'basin_dS_sw.csv')
#%% yearly datacube
for key in BASIN['data_cube']['monthly']:
    if key != 'lu':
        BASIN['data_cube']['yearly'][key]=cf.create_yearly_dataset(
                BASIN['data_cube']['monthly'][key], hydroyear=BASIN['hydroyear'])
#%% Calculate yearly and (intermediate) monthly sheet csvs
from WAsheets import sheet1
from WAsheets import sheet2
from WAsheets import sheet3
from WAsheets import sheet4
from WAsheets import sheet5
from WAsheets import sheet6

sheet1_yearly_csvs=sheet1.main(BASIN,unit_conversion=BASIN['unit_conversion'])
sheet2_yearly_csvs=sheet2.main(BASIN,unit_conversion=BASIN['unit_conversion'])
sheet3_yearly_csvs=sheet3.main(BASIN,unit_conversion=BASIN['unit_conversion'])
sheet4_yearly_csvs=sheet4.main(BASIN,unit_conversion=BASIN['unit_conversion'])
sheet5_yearly_csvs=sheet5.main(BASIN,unit_conversion=BASIN['unit_conversion'])
sheet6_yearly_csvs=sheet6.main(BASIN,unit_conversion=BASIN['unit_conversion'])

#%% Print hydro-yearly sheet csv
from WAsheets import print_sheet as ps

if BASIN['unit_conversion'] == 1e6:
    str_unit='km3/year'
elif BASIN['unit_conversion']==1e3:
    str_unit='MCM/year'
    
for sheet1_csv in sheet1_yearly_csvs:
    period=os.path.basename(sheet1_csv).split('.')[0].split('_')[-1]
    output=sheet1_csv.replace('.csv','.pdf')
    ps.print_sheet1(BASIN['name'],period=period,
                    output=output,units=str_unit,data=sheet1_csv)

for sheet2_csv in sheet2_yearly_csvs:
    period=os.path.basename(sheet2_csv).split('.')[0].split('_')[-1]
    output=sheet2_csv.replace('.csv','.pdf')
    ps.print_sheet2(BASIN['name'],period=period,output=output,
                    units=str_unit,data=sheet2_csv)
    
for sheet3_csv in sheet3_yearly_csvs:
    period=os.path.basename(sheet3_csv).split('.')[0].split('_')[-1]
    output=sheet3_csv.replace('.csv','.pdf')
    ps.print_sheet3(BASIN['name'],period=period,output=output,units=[str_unit,'kg/ha','kg/m3'],data=sheet3_csv)
    
for sheet4_csv in sheet4_yearly_csvs:
    period=os.path.basename(sheet4_csv).split('.')[0].split('_')[-1]
    output=[sheet4_csv.replace('.csv','_part1.pdf'),sheet4_csv.replace('.csv','_part2.pdf')]
    ps.print_sheet4(BASIN['name'],period=period,output=output,
                    units=[str_unit,str_unit],data=[sheet4_csv,sheet4_csv])
    
for sheet5_csv in sheet5_yearly_csvs:
    period=os.path.basename(sheet5_csv).split('.')[0].split('_')[-1]
    output=sheet5_csv.replace('.csv','.pdf')
    ps.print_sheet5(BASIN['name'],sb_codes=[1], dico_in=BASIN['params']['dico_in'], dico_out=BASIN['params']['dico_out'],
                    period=period,output=output,units=str_unit,
                    data=sheet5_csv)
    
for sheet6_csv in sheet6_yearly_csvs:
    period=os.path.basename(sheet6_csv).split('.')[0].split('_')[-1]
    output=sheet6_csv.replace('.csv','.pdf')
    ps.print_sheet6(BASIN['name'],period=period,output=output,units=str_unit,
                    data=sheet6_csv)
