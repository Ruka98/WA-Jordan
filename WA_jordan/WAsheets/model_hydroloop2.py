from . import calculate_flux as cf
from . import hydroloop as hl
import os
import pandas as pd
import time
import warnings

def create_data_cube(metadata, nc_files,table_data):
    basin_name = metadata['name']
    hydro_year = metadata['hydro_year']
    chunksize = metadata['chunksize']
    unit_conversion = metadata['unit_conversion']
    output_folder = metadata['result_folder']
    basin_mask = metadata['mask']
    dem = metadata['dem']
    aeisw = metadata['aeisw']
    population = metadata['population']
    wpl = metadata['wpl']
    environ_water_req = metadata['environ_water_req']
    
    q_in_sw = table_data['q_in_sw']
    q_outflow = table_data['q_outflow']
    cw_do = table_data['cw_do']
    tww = table_data['tww']
    
    
    BASIN = {
       'name': basin_name,
       'hydroyear':hydro_year, #Water year end month
       'chunksize':chunksize,
       'unit_conversion':unit_conversion, #1e3 for input data in MCM, 1e6 for input data in km3
       'output_folder':output_folder,
       'gis_data':{
               'basin_mask': basin_mask,
               'subbasin_mask':{
                       1: basin_mask,                       
                       },
               'dem':dem,
               'aeisw':aeisw, #area equipped with surface water irrigation percentage
               'population':population,
               'wpl':wpl,
               'environ_water_req': environ_water_req
               },
       'data_cube':{
           'monthly':{
               'p':nc_files['P'],
                'etref':nc_files['ETref'],
               'et':nc_files['ET'],
               'i':nc_files['I'],
               't':None,
               'e':None,
               'nrd':nc_files['NRD'],
               'etincr':nc_files['ETB'],
               'etrain':nc_files['ETG'],
               'lai':nc_files['LAI'],
               'ndm':nc_files['ProbaV'],
               'sro':nc_files['SRO'],
               'sroincr':nc_files['ISRO'],
               'perc':nc_files['PERC'],
               'percincr':nc_files['DPERC'],
               'bf':nc_files['BF'],
               'supply':nc_files['Supply']
               },
           'yearly':{
               'lu':nc_files['LU'],
                   }      
                     },
        'ts_data':{
                'q_in_sw':{
                        'basin':q_in_sw,
                        1:q_in_sw, #unit MCM
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
                        'basin':q_outflow,
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
                'cw_do':{ #Consumed Water domestic
                        'basin':cw_do,
                        1:cw_do,
                        2:None,
                        },
                'cw_in':{ #Consumed Water industrial
                        'basin':None,
                        1:None,
                        2:None,
                        },
                'cw_to':{ #Consumed Water tourism
                        'basin': None,
                        1:None,
                        2:None,
                        },
                'cw_li':{ #Consumed Water livestock
                        'basin': None,
                        1:None,
                        2:None,
                        },
                'tww':{ #Treated Waste Water- Return Flow to the river
                        'basin': tww,
                        1:None,
                        2:None,
                        }
                },
        'params':{
            'crops':{#lu_code: [r'seasons_dates.csv','Crop_type']
                    35.0: [r'/efs/Cimanuk/static_datasets/growing seasons/rice_rain_java.txt','N/A'],
                    54.0: [r'/efs/Cimanuk/static_datasets/growing seasons/rice_irrigated_java.txt','N/A'],    
                    52.0: [r'/efs/Cimanuk/static_datasets/growing seasons/palm_perennial.txt','N/A'],
                    33.0: [r'/efs/Cimanuk/static_datasets/growing seasons/palm_perennial.txt','N/A']             
                    },
            'dico_in':{1:[0]},
            'dico_out':{1:[]},
            'residential_sw_supply_fraction':0.6,
            'wcpc':110, #Water consumption per capita per day in [liter/person/day]
            'wcpc_min':100, #minimum demand
            'fraction_xs':[4,25,4,25]
        }
        
       }
    return BASIN
    
def collect_tables(folder,inflow,outflow,tatal_water_consumption,treated_waste_water):
    table_data = {}
    table_data['q_in_sw'] = os.path.join(folder,inflow)
    table_data['q_outflow'] = os.path.join(folder,outflow)
    table_data['cw_do'] = os.path.join(folder,tatal_water_consumption)
    table_data['tww'] = os.path.join(folder,treated_waste_water)
    
    return table_data

def create_metadata(basin_name,hydro_year,output_folder,basin_mask,dem,aeisw,population,wpl,environ_water_req,unit_conversion = 1e3,chunksize = [1, 300,300]):
    
    metadata = {}

    metadata['name'] = basin_name
    metadata['hydro_year'] = hydro_year
    metadata['chunksize'] = chunksize 
    metadata['unit_conversion'] = unit_conversion
    metadata['result_folder'] = output_folder
    metadata['mask'] = basin_mask
    metadata['dem'] = dem
    metadata['aeisw'] = aeisw
    metadata['population'] = population
    metadata['wpl'] = wpl
    metadata['environ_water_req'] = environ_water_req
    
    return metadata

def initialize_hydroloop(metadata, nc_files,table_data):
    out_folder = metadata['result_folder']
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    BASIN = create_data_cube(metadata, nc_files,table_data)
    print("Initialized successfully...")

    return BASIN
          
def resample_lu(BASIN): 
    warnings.filterwarnings("ignore")
    ### Resample yearly LU to monthly netCDF
    yearly_nc=BASIN['data_cube']['yearly']['lu']
    sample_nc=BASIN['data_cube']['monthly']['p']
    monthly_nc=cf.resample_to_monthly_dataset(yearly_nc, sample_nc,
                                    start_month=0,
                                    output=None,
                                    chunksize=BASIN['chunksize'])
     ## check this one again
    BASIN['data_cube']['monthly']['lu']=monthly_nc
    return BASIN
    
    
def split_et(BASIN):
    warnings.filterwarnings("ignore")
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
          
    return BASIN
          
def split_supply(BASIN):
    warnings.filterwarnings("ignore")
    ### split supply
    sw_supply_fraction_nc=hl.calc_sw_supply_fraction_by_LU(BASIN['data_cube']['monthly']['lu'],
                                                           BASIN['gis_data']['aeisw'],
                                                          chunksize=BASIN['chunksize'])

    sw_supply_nc,gw_supply_nc=hl.split_flow(BASIN['data_cube']['monthly']['supply'],
                  fraction_nc=sw_supply_fraction_nc, chunksize=BASIN['chunksize'])

    BASIN['data_cube']['monthly']['sw_supply_fraction']=sw_supply_fraction_nc
    BASIN['data_cube']['monthly']['sw_supply']=sw_supply_nc
    BASIN['data_cube']['monthly']['gw_supply']=gw_supply_nc
          
    return BASIN
    

def calc_demand(BASIN):
    warnings.filterwarnings("ignore")
    ### demand of land surface
    demand_nc=hl.calc_land_surface_water_demand(BASIN['data_cube']['monthly']['lai'],
                                      BASIN['data_cube']['monthly']['etref'],
                                      BASIN['data_cube']['monthly']['p'],
                                      BASIN['data_cube']['monthly']['lu'],
                                      chunksize=BASIN['chunksize']) 
    BASIN['data_cube']['monthly']['demand'] = demand_nc
    return BASIN

def calc_return(BASIN):
    warnings.filterwarnings("ignore")
    ### non-consumed supply or return flow
    return_nc=hl.substract_flow(BASIN['data_cube']['monthly']['supply'],
                                      BASIN['data_cube']['monthly']['etincr'],
                                      name='return',
                                      chunksize=BASIN['chunksize']
                                      )
    
    ### split return by sroincr/total_incremental ratio
    sw_return_fraction_nc=hl.calc_sw_return_fraction(
            BASIN['data_cube']['monthly']['sroincr'],
            BASIN['data_cube']['monthly']['percincr'])
    sw_return_nc,gw_return_nc=hl.split_flow(return_nc,fraction_nc=sw_return_fraction_nc, chunksize=BASIN['chunksize'])

    BASIN['data_cube']['monthly']['sw_return']=sw_return_nc
    BASIN['data_cube']['monthly']['gw_return']=gw_return_nc
          
    return BASIN
          
def calc_residential_supply(BASIN):
    warnings.filterwarnings("ignore")
    ### residential supply and demand
    residential_supply_nc=hl.calc_residential_water_consumption(
            BASIN['gis_data']['population'],
            BASIN['gis_data']['basin_mask'],
            BASIN['data_cube']['monthly']['lu'],
            wcpc=BASIN['params']['wcpc'],
            flow_type='supply',
            chunksize=BASIN['chunksize']
            )

    residential_demand_nc=hl.calc_residential_water_consumption(
            BASIN['gis_data']['population'],
            BASIN['gis_data']['basin_mask'],
            BASIN['data_cube']['monthly']['lu'],
            wcpc=BASIN['params']['wcpc_min'],
            flow_type='demand',
            chunksize=BASIN['chunksize'])

    BASIN['data_cube']['monthly']['residential_supply']=residential_supply_nc
    BASIN['data_cube']['monthly']['residential_demand']=residential_demand_nc
          
    return BASIN
          
def calc_total_supply(BASIN):
    warnings.filterwarnings("ignore")
    ### split return flow by source sw/gw

    sw_supply_fraction_nc = BASIN['data_cube']['monthly']['sw_supply_fraction']
    sw_return_nc = BASIN['data_cube']['monthly']['sw_return']
    gw_return_nc = BASIN['data_cube']['monthly']['gw_return']
    residential_supply_nc = BASIN['data_cube']['monthly']['residential_supply']
    residential_demand_nc = BASIN['data_cube']['monthly']['residential_demand']
    sw_supply_nc = BASIN['data_cube']['monthly']['sw_supply']
    gw_supply_nc = BASIN['data_cube']['monthly']['gw_supply']
    demand_nc = BASIN['data_cube']['monthly']['demand']
 
    return_sw_from_sw_nc,return_sw_from_gw_nc = hl.split_flow(
            sw_return_nc,fraction_nc = sw_supply_fraction_nc, chunksize=BASIN['chunksize'])
    return_gw_from_sw_nc,return_gw_from_gw_nc = hl.split_flow(
            gw_return_nc,fraction_nc = sw_supply_fraction_nc, chunksize=BASIN['chunksize'])

    ### split residential supply by sw/gw fraction
    f=BASIN['params']['residential_sw_supply_fraction']
    sw_residential_supply_nc,gw_residential_supply_nc=hl.split_flow(
            residential_supply_nc,fraction=f, chunksize=BASIN['chunksize'])

    ### add residential sw/gw supply to sw/gw supply and sw/gw return
    BASIN['data_cube']['monthly']['supply_sw']=hl.add_flow(
            sw_supply_nc,sw_residential_supply_nc,name='total_sw_supply', chunksize=BASIN['chunksize'])
    BASIN['data_cube']['monthly']['supply_gw']=hl.add_flow(
            gw_supply_nc,gw_residential_supply_nc,name='total_gw_supply', chunksize=BASIN['chunksize'])

    #assume that residential supply from sw return to sw, from gw return to gw
    BASIN['data_cube']['monthly']['return_sw_from_sw']=hl.add_flow(
            return_sw_from_sw_nc,sw_residential_supply_nc,name='total_return_sw_from_sw', chunksize=BASIN['chunksize'])
    BASIN['data_cube']['monthly']['return_gw_from_gw']=hl.add_flow(
            return_gw_from_gw_nc,gw_residential_supply_nc,name='total_return_gw_from_gw', chunksize=BASIN['chunksize'])

    BASIN['data_cube']['monthly']['return_sw_from_gw']=return_sw_from_gw_nc
    BASIN['data_cube']['monthly']['return_gw_from_sw']=return_gw_from_sw_nc

    ### add residential demand to total demand
    BASIN['data_cube']['monthly']['demand']=hl.add_flow(
            demand_nc,residential_demand_nc,name='total_demand', chunksize=BASIN['chunksize'])

    ### total return and supply
    BASIN['data_cube']['monthly']['return_sw']=hl.add_flow(
            BASIN['data_cube']['monthly']['return_sw_from_gw'],
            BASIN['data_cube']['monthly']['return_sw_from_sw'],
            name='return_sw',
            chunksize=BASIN['chunksize'])

    BASIN['data_cube']['monthly']['return_gw']=hl.add_flow(
            BASIN['data_cube']['monthly']['return_gw_from_gw'],
            BASIN['data_cube']['monthly']['return_gw_from_sw'],
            name='return_gw',
            chunksize=BASIN['chunksize'])

    BASIN['data_cube']['monthly']['supply']=hl.add_flow(
            BASIN['data_cube']['monthly']['supply_sw'],
            BASIN['data_cube']['monthly']['supply_gw'],
            name='total_supply',
            chunksize=BASIN['chunksize'])
          
    return BASIN
          
def calc_fraction(BASIN):
    warnings.filterwarnings("ignore")
    ### calculate recharge
    BASIN['data_cube']['monthly']['recharge']=BASIN['data_cube']['monthly']['perc']

    BASIN['data_cube']['monthly']['fraction'] = hl.calc_fractions(BASIN['data_cube']['monthly']['p'],
                                                                  dem=BASIN['gis_data']['dem'],
                                                                  lu=BASIN['data_cube']['yearly']['lu'],
                                                                  fraction_altitude_xs=BASIN['params']['fraction_xs'],
                                                                  chunksize=BASIN['chunksize'])
          
    return BASIN
          
def calc_time_series(BASIN):
          
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
                                            plot=False
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
          
    return BASIN
          
          
    
