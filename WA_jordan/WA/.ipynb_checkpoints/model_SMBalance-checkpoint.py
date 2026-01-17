# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 08:22:17 2019

@author: sse
"""
import os
import numpy as np
import gdal
import xarray as xr
#import glob
#import datetime
import warnings
import time


#%% Functions
def open_nc(nc,timechunk=1,chunksize=1000):
    dts=xr.open_dataset(nc)
    key=list(dts.keys())[0]
    var=dts[key].chunk({"time": timechunk, "latitude": chunksize, "longitude": chunksize}) #.ffill("time")
    return var,key

def open_nc_e(nc):
    dts=xr.open_dataset(nc)
    key=list(dts.keys())[0]
    var=dts[key]
    return var,key

def SCS_calc_SRO(P,I,NRD,SMmax,SM, cf): 

    SRO = ((((P-I)/NRD)**2)/((P-I)/NRD+cf*(SMmax-SM))).where((P-I)>0,P*0)
    return SRO*NRD

def get_rootdepth(version = '1.0'):
    '''
    Roothdepth dictionary, use only for WAPOR Land Cover Map
    for other land cover map, change dictionary
    '''
    lcc_code = dict()
    lcc_code['1.0'] = {
       'Shrubland':20,
       'Grassland':30,
       'Rainfed Cropland':41,
       'Irrigated Cropland':42,
       'Fallow Cropland':43,
       'Built-up':50,
       'Bare/sparse vegetation':60,
       'Permanent snow/ ice':70,
       'Water bodies':80,
       'Temporary water bodies':81,
       'Shrub or herbaceous cover, flooded':90,     
       'Tree cover: closed, evergreen needle-leaved':111,
       'Tree cover: closed, evergreen broad-leaved':112, 
       'Tree cover: closed, deciduous broad-leaved':114, #
       'Tree cover: closed, mixed type':115, #
       'Tree cover: closed, unknown type':116, #
       'Tree cover: open, evergreen needle-leaved':121,#
       'Tree cover: open, evergreen broad-leaved':122, #
       'Tree cover: open, deciduous needle-leaved':123, #
       'Tree cover: open, deciduous broad-leaved':124, #
       'Tree cover: open, mixed type':125, #
       'Tree cover: open, unknown type':126, #     
       'Seawater':200, #       
       }
    
    root_depth = dict()
    '''
    based on Global estimation of effective plant rooting depth: 
    Implications for hydrological modeling by Yang et al (2016)
    '''
    root_depth['1.0'] = {
       'Shrubland':370,
       'Grassland':510,
       'Rainfed Cropland':550,
       'Irrigated Cropland':550,
       'Fallow Cropland':550,
       'Built-up':370,
       'Bare/sparse vegetation':370,
       'Permanent snow/ ice':0,
       'Water bodies':0,
       'Temporary water bodies':0,
       'Shrub or herbaceous cover, flooded':0,     
       'Tree cover: closed, evergreen needle-leaved':1800,
       'Tree cover: closed, evergreen broad-leaved':3140, 
       'Tree cover: closed, deciduous broad-leaved':1070, #
       'Tree cover: closed, mixed type':2000, #
       'Tree cover: closed, unknown type':2000, #
       'Tree cover: open, evergreen needle-leaved':1800,#
       'Tree cover: open, evergreen broad-leaved':3140, #
       'Tree cover: open, deciduous needle-leaved':1070, #
       'Tree cover: open, deciduous broad-leaved':1070, #
       'Tree cover: open, mixed type':2000, #
       'Tree cover: open, unknown type':2000, #     
       'Seawater':0, #       
    }
    
    return lcc_code[version], root_depth[version]

def get_rootdepth_wa_plus(version = '1.0'):
    '''
    Roothdepth dictionary, use only for WAPOR Land Cover Map
    for other land cover map, change dictionary
    '''
    lcc_code = dict()
    lcc_code['1.0'] = {
       'Shrubland':[2, 12, 13, 14, 29],
       'Grassland':[3, 7, 15, 16, 17, 20, 32, 47, 48, 49, 50, 68, 69, 70, 71, 73],
       'Rainfed Cropland':[34, 35, 36, 37, 38, 39, 40, 41, 42, 43],
       'Irrigated Cropland':[53, 54, 55, 56, 57, 58, 59, 60,61, 62],
       'Fallow Cropland':[45],
       'Built-up':[51, 64, 66, 67, 72, 78, 79, 80],
       'Bare/sparse vegetation':[18, 21, 26, 27, 28, 46, 76],
       'Permanent snow/ ice':[6, 22],
       'Water bodies':[4, 23, 24, 63, 65, 75, 77],
       'Temporary water bodies':[19, 25],
       'Shrub or herbaceous cover, flooded':[5, 30, 31, 74],     
       'Tree cover: closed, evergreen':[10],
       'Tree cover: closed, deciduous':[8], #
       'Tree cover: closed, mixed type':[1], #
       'Tree cover: closed, unknown type':[33, 44, 52], #
       'Tree cover: open, evergreen':[11],#
       'Tree cover: open, deciduous':[9] #
       }
    
    root_depth = dict()
    '''
    based on Global estimation of effective plant rooting depth: 
    Implications for hydrological modeling by Yang et al (2016)
    '''
    root_depth['1.0'] = {
       'Shrubland':370,
       'Grassland':510,
       'Rainfed Cropland':550,
       'Irrigated Cropland':550,
       'Fallow Cropland':550,
       'Built-up':370,
       'Bare/sparse vegetation':370,
       'Permanent snow/ ice':0,
       'Water bodies':0,
       'Temporary water bodies':0,
       'Shrub or herbaceous cover, flooded':0,     
       'Tree cover: closed, evergreen':3140,
       'Tree cover: closed, deciduous':1070, #
       'Tree cover: closed, mixed type':2000, #
       'Tree cover: closed, unknown type':2000, #
       'Tree cover: open, evergreen' :3140,#
       'Tree cover: open, deciduous':1070, #   
    }
    
    # test
    root_depth['2.0'] = {
       'Shrubland':300,
       'Grassland':300,
       'Rainfed Cropland':300,
       'Irrigated Cropland':300,
       'Fallow Cropland':300,
       'Built-up':200,
       'Bare/sparse vegetation':300,
       'Permanent snow/ ice':0,
       'Water bodies':0,
       'Temporary water bodies':0,
       'Shrub or herbaceous cover, flooded':0,     
       'Tree cover: closed, evergreen':2000,
       'Tree cover: closed, deciduous':800, #
       'Tree cover: closed, mixed type':1000, #
       'Tree cover: closed, unknown type':1000, #
       'Tree cover: open, evergreen' :2000,#
       'Tree cover: open, deciduous':1000, #   
    }
    
    
    return lcc_code['1.0'], root_depth[version]


def root_depth(lu, root_depth_version):
    rootdepth=lu.copy()
    rootdepth.name='Root depth'
    rootdepth.attrs={'units':'mm',
                    'quantity':'Effective root depth',
                    'source':'Root depth lookup table',
                    'period':'year'}
    lu_categories, root_depth = get_rootdepth_wa_plus(version = root_depth_version)
    for key in root_depth.keys():
      lu_codes=lu_categories[key]
      for lu_code in lu_codes:
          rd = root_depth[key]
          rootdepth=rootdepth.where(lu!=lu_code,rd)
    return rootdepth 


def get_fractions(version = '1.0'):
# adding stuff for WA+ LU map
    lucs = dict()
    
    lucs['1.0'] = {
    'Shrubland':              [2, 12, 14, 15],
    'Grassland':              [3, 13, 16, 20],
    'Rainfed Cropland':       [34, 35, 36, 37, 38, 39, 40, 41, 42, 43],
    'Irrigated Cropland':     [52,53,54,55,56,57,58,59,60,61,62],
    'Fallow Cropland':        [45],
    'Built-up':               [66, 67, 72, 73, 79, 80],
    'Bare/sparse vegetation': [27, 7, 18, 21, 26,28, 29, 32, 46, 47, 48, 49, 50, 51, 64, 68,69,70,71,76,78], # + other
    'Permanent snow/ ice':    [6, 22],
    'Water bodies':           [4, 19, 23, 24, 63,74,75,77, 5, 25, 30, 31, 65],  # natural + man-made + wetlands +aquaculture
    'Temporary water bodies': [],
    'Shrub or herbaceous cover, flooded': [],
    'Tree cover: closed, evergreen needle-leaved':[1, 8, 9, 10, 11, 17, 33, 44], # forest +forest plantation
    'Tree cover: closed, evergreen broad-leaved':[], 
    'Tree cover: closed, deciduous broad-leaved':[], #
    'Tree cover: closed, mixed type':[], #
    'Tree cover: closed, unknown type':[], #
    'Tree cover: open, evergreen needle-leaved':[],#
    'Tree cover: open, evergreen broad-leaved':[], #
    'Tree cover: open, deciduous needle-leaved':[], #
    'Tree cover: open, deciduous broad-leaved':[], #
    'Tree cover: open, mixed type':[], #
    'Tree cover: open, unknown type':[], #     
    'Seawater':[]}


    consumed_fractions = dict()
    
    consumed_fractions['1.0'] = {
       'Shrubland':1.00,
       'Grassland':1.00,
       'Rainfed Cropland':1.00,
       'Irrigated Cropland':0.80,
       'Fallow Cropland':1.00,
       'Built-up':1.00,
       'Bare/sparse vegetation':1.00,
       'Permanent snow/ ice':1.00,
       'Water bodies':1.00,
       'Temporary water bodies':1.00,
       'Shrub or herbaceous cover, flooded':1.00,     
       'Tree cover: closed, evergreen needle-leaved':1.00,
       'Tree cover: closed, evergreen broad-leaved':1.00, 
       'Tree cover: closed, deciduous broad-leaved':1.00, #
       'Tree cover: closed, mixed type':1.00, #
       'Tree cover: closed, unknown type':1.00, #
       'Tree cover: open, evergreen needle-leaved':1.00,#
       'Tree cover: open, evergreen broad-leaved':1.00, #
       'Tree cover: open, deciduous needle-leaved':1.00, #
       'Tree cover: open, deciduous broad-leaved':1.00, #
       'Tree cover: open, mixed type':1.00, #
       'Tree cover: open, unknown type':1.00, #     
       'Seawater':1.00, #       

    }
    
    return consumed_fractions[version], lucs[version]

def Consumed_fraction(lu):
    f_consumed=lu.copy()
    f_consumed.name='Consumed fraction'
    f_consumed.attrs={'units':'Fraction',
                    'quantity':'Consumed fraction',
                    'source':'Consumed fraction look-up table',
                    'period':'year'}
#    consumed_fractions = get_fractions(version = '1.0')
    consumed_fractions, lu_categories = get_fractions(version = '1.0')
#    lu_categories, root_depth = get_rootdepth(version = '1.0')
    for key in consumed_fractions.keys():
        lu_code=lu_categories[key]
        consumed_fraction = consumed_fractions[key]
        for code in lu_code:
            f_consumed = f_consumed.where(lu!=code,consumed_fraction)
    return f_consumed 

def OpenAsArray(fh, bandnumber = 1, dtype = 'float32', nan_values = False):
    """
    Open a map as an numpy array. 
    
    Parameters
    ----------
    fh: str
        Filehandle to map to open.
    bandnumber : int, optional 
        Band or layer to open as array, default is 1.
    dtype : str, optional
        Datatype of output array, default is 'float32'.
    nan_values : boolean, optional
        Convert he no-data-values into np.nan values, note that dtype needs to
        be a float if True. Default is False.
        
    Returns
    -------
    Array : ndarray
        Array with the pixel values.
    """
    datatypes = {"uint8": np.uint8, "int8": np.int8, "uint16": np.uint16, "int16":  np.int16, "Int16":  np.int16, "uint32": np.uint32,
    "int32": np.int32, "float32": np.float32, "float64": np.float64, "complex64": np.complex64, "complex128": np.complex128,
    "Int32": np.int32, "Float32": np.float32, "Float64": np.float64, "Complex64": np.complex64, "Complex128": np.complex128,}
    DataSet = gdal.Open(fh, gdal.GA_ReadOnly)
    Type = DataSet.GetDriver().ShortName
    if Type == 'HDF4':
        Subdataset = gdal.Open(DataSet.GetSubDatasets()[bandnumber][0])
        NDV = int(Subdataset.GetMetadata()['_FillValue'])
    else:
        Subdataset = DataSet.GetRasterBand(bandnumber)
        NDV = Subdataset.GetNoDataValue()
    Array = Subdataset.ReadAsArray().astype(datatypes[dtype])
    if nan_values:
        Array[Array == NDV] = np.nan
    Array = Array.astype(np.float32)
    return Array

#%% main
def run_SMBalance(MAIN_FOLDER,p_in,e_in,i_in,nrd_in,lu_in,smsat_file, aridity, start_year, end_year, 
        f_perc=1,f_Smax=0.9, cf =  20, f_bf = 0.1, deep_perc_f = 0.1, root_depth_version = '1.0',
         chunks=[1,1000,1000]):
    '''
    Arguments:
        
    ## required   
    MAIN_FOLDER='$PATH/nc/'
    p_in = '$PATH/p_monthly.nc' # Monthly Precipitation
    e_in = '$PATH/e_monthly.nc' # Monthly Actual Evapotranspiration
    i_in = '$PATH/i_monthly.nc' # Monthly Interception
    rd_in = '$PATH/nRD_monthly.nc' # Monthly Number of Rainy days
    lu_in = '$PATH/lcc_yearly.nc' # Yearly WaPOR Land Cover Map
    smsat_file = '$PATH/thetasat.nc' #Saturated Water Content (%)
    start_year=2009 
    
    #default
    f_perc=1 # percolation factor
    f_Smax=0.9 #threshold for percolation
    cf =  20 #f_Ssat soil mositure correction factor to componsate the variation in filling up and drying in a month
    f_bf = 0.1 # base flow factor (multiplier of SM for estimating base flow)
 
    '''
    warnings.filterwarnings("ignore", message='invalid value encountered in greater')
    warnings.filterwarnings("ignore", message='divide by zero encountered in true_divide')
    warnings.filterwarnings("ignore", message='invalid value encountered in true_divide')
    warnings.filterwarnings("ignore", message='overflow encountered in exp')

    tchunk=chunks[0]
    chunk=chunks[1]
    
    
    #########
    #to remove: just to check root depth computations
    #LU_files = becgis.list_files_in_folder(os.path.join(MAIN_FOLDER, 'LU'))
    #driver, ndv, xsize, ysize, geot, projection = becgis.get_geoinfo(LU_files[0])
    
    
    
    Pt,_=open_nc(p_in,timechunk=tchunk,chunksize=chunk)
#    Pt,_ = open_nc_e(p_in)
    E,_=open_nc(e_in,timechunk=tchunk,chunksize=chunk)
#    E,_ = open_nc_e(e_in)
    Int,_=open_nc(i_in,timechunk=tchunk,chunksize=chunk)
#    Int,_ = open_nc_e(i_in)
    nRD,_=open_nc(nrd_in,timechunk=tchunk,chunksize=chunk)
#    nRD,_ = open_nc_e(nrd_in)
    LU,_=open_nc(lu_in,timechunk=tchunk,chunksize=chunk)
#    lu,_=open_nc(lu_in,timechunk=tchunk,chunksize=chunk)
#    lu,_=open_nc_e(lu_in)
    A,_ = open_nc(aridity,timechunk=tchunk,chunksize=chunk)
    
    thetasat,_ =open_nc(smsat_file,timechunk=tchunk,chunksize=chunk)
#    thetasat,_ =open_nc_e(smsat_file)
    # no computation of rootdepoth
#    Rd,_=open_nc(root_depth_file,timechunk=tchunk,chunksize=chunk)
#    Rd,_ = open_nc_e(root_depth_file)
 
    ### convert nRD = 0 to 1
    nRD = nRD.where(nRD!=0,1)
    
    ### Create 
    SM=E[0]*0
    GW=E[0]*0
#    SM = lu*0
#    SM=SM[0]#         
#     ari = Ari.isel(time = 0)
    Ari = A[0]
    
    for j in range(len(LU.time)):
        

#        for j in range(end_year - start_year+1):
        t1 = j*12
        t2 = (j+1)*12    
       
        lu = LU.isel(time=j)
        f_consumed = Consumed_fraction(lu)
        
        #mask lu for water bodies
#        mask = xr.where(((lu==80) | (lu==81) | (lu==70) | (lu==200)|(lu==90)), 1,0)
        mask = xr.where(((lu==4) | (lu==23) | (lu==24) | (lu==63)|(lu==75)), 1,0)
        #include flooded shrub?
        Rd = root_depth(lu, root_depth_version) 
#       SMmax=thetasat[0]*Rd
#        SMmax=Rd*thetasat[0]
        SMmax=Rd*thetasat[0]
        

#        SMmax = SMmax[0]

# the original code was generating negative soil moisture content over water bodies
# I am going to change ti so that ET is satified before the runoff is calculated when ET>P
# only over water bodies

            
        for t in range(t1,t2):
            print('time: ', t)
            SMt_1=SM.copy()
            GWt_1 = GW.copy()
#            SMt_1 = SM
            P = Pt.isel(time=t)
            ETa = E.isel(time=t)
            I = Int.isel(time=t)
            NRD = nRD.isel(time=t)
            
            ### calculate surface runoff  as a function of SMt_1
            SMt_1=SMt_1.where(SMt_1<SMmax, SMmax)
            SRO=SCS_calc_SRO(P,I,NRD,SMmax,SMt_1,cf)
            
            
#             Correct ETa for desert areas
            ETa = ETa.where(ETa > 0, P)
            ETa = P.where((ETa < P) & (Ari < 0.2),ETa)
#             ETa = ETa.where(ETa > 0, (P.where((P != 0) & (ari < 0.3)), P*0 ))
    
            # this is the change for fixing the negative soil moisture (not sufficient)
            SRO = (P*0).where(((mask==1) & (P<ETa)), SRO)
            SRO = (P-ETa).where(((mask==1) & (P>=ETa)), SRO)
            
             
            ### calculate Percolation as a function of SMt_1
            perc=(SMt_1*(xr.ufuncs.exp(-f_perc/SMt_1))).where(SMt_1>f_Smax*SMmax,P*0)
            # time dimension in the second time step disappear (because SMt_1 and P have different dates)
            # so I am forcing it to the time of P
            perc['time'] = P['time']
            
    
    #        maskerror = xr.where(((I.notnull()) & (P.isnull())), 1,np.nan)
    
                    
            ### Calculate SM temp
            Stemp = SMt_1+(P-I)-(ETa-I)-SRO-perc #???
    #         Stemp = SMt_1+P-ETa-SRO-perc ##why not this??
#             Stemp = 2+(2-0.2)-(6-0.2)-0.5-0.3 = -2.8
#             Stemp = 1+(0-0)-(4-0)-0-0.15 = -3.15
    #
            
            ### Calculate ETincr, ETrain, Qsupply, and update SM
            ETincr = (P*0).where(Stemp>=0, -1*Stemp)
            
            # ETinct should lower than ET
#             ETincr = ETincr.where(ETincr >= ETa, ETa)
           
            # adjust ETincr for water bodies
            ETincr = (P*0).where(((mask==1) & (P >= ETa)),(ETa-P).where(((mask==1) & (P <ETa)), ETincr))
            
            ETrain = ETa.where(Stemp>=0,ETa-ETincr)
            ETrain = ETrain.where(ETrain > 0,0) # This line has been added by Lahiru in order to eleminate negative values in ETrain
            
            # Etrain = ETa-ETincr
            
            Qsupply = (P*0).where(Stemp>=0,ETincr/f_consumed)
            SM = Stemp.where(Stemp>=0,Stemp+Qsupply)
    #        SM = SM.where(SM>=0,P*0)
            ### Calculate increametal percolation and increamental runoff
            
            perc_incr = ((SM-SMmax)*perc/(perc+SRO)).where(((SM>SMmax)&(perc+SRO>0)), P*0)
            #perc_incr = perc_incr.where(perc+SRO>0,P*0)
  
            
            SROincr = (SM-SMmax-perc_incr).where(SM>SMmax, P*0)
            overflow = SM-SMmax # we don't use overflow at the moment
            SM=SM.where(SM<SMmax, SMmax) # this is a repeatition of the first calculation in the loop
            SRO=SRO+overflow.where(overflow>0, SRO)
            
            # groundwater storage update
            GW_temp = GWt_1 + perc + perc_incr
    
            # test base flow (percentage of percolation)
            BF = GW_temp* f_bf
            TF = BF+SRO+SROincr
            
            # groundwater storage update
            GW = GW_temp - BF
            # loss
            Deep_perc = deep_perc_f*GW
            GW = GW - Deep_perc
          
            
    
            if t == 0:
                etb = ETincr
                etg = ETrain
                sro = SRO
                dsro = SROincr
                perco = perc
                dperc = perc_incr
                supply = Qsupply
                sm = SM
                gw = GW
                bf = BF
                tf = TF
            else:
                etb = xr.concat([etb, ETincr], dim='time')  
                etg = xr.concat([etg, ETrain], dim='time')
                sro = xr.concat([sro, SRO], dim='time')
                perco = xr.concat([perco, perc], dim='time')
                dperc = xr.concat([dperc, perc_incr], dim='time')
                supply = xr.concat([supply, Qsupply], dim='time')
                dsro = xr.concat([dsro, SROincr], dim='time')
                sm = xr.concat([sm, SM], dim='time')
                gw = xr.concat([gw, GW], dim='time')
                bf = xr.concat([bf, BF], dim='time')
                tf = xr.concat([tf, TF], dim='time')
                
            
            del ETincr
            del ETrain
            
            del Stemp
            del GW_temp
            del perc_incr
            del SRO
            del SROincr
            del perc
            del Qsupply 
            
            del P
            del ETa
            del I
            del NRD
            del SMt_1
            del GWt_1
    # to remove: testing root depth computations

        #f_name_Rd = os.path.join(MAIN_FOLDER, 'root_depth_%s.tif' %(np.datetime_as_string(LU['time'][j].values)[:4]))
        #becgis.create_geotiff(f_name_Rd, Rd.values, driver, ndv, xsize, ysize, geot, projection)
    
    # force time dimension of output DataArray equal to input time dimension
    etb['time']=E['time']
    etg['time']=E['time']
    sro['time']=E['time']
    perco['time']=E['time']
    dperc['time']=E['time']
    supply['time']=E['time']
    dsro['time']=E['time']
    sm['time']=E['time']
    gw['time']=E['time']
    bf['time']=E['time']
    tf['time']=E['time']
    #change coordinates order to [time,latitude,longitude]
    etb=etb.transpose('time','latitude','longitude')
    etg=etg.transpose('time','latitude','longitude')  
    sro=sro.transpose('time','latitude','longitude')
    perco=perco.transpose('time','latitude','longitude') 
    dperc=dperc.transpose('time','latitude','longitude')  
    supply=supply.transpose('time','latitude','longitude')  
    dsro=dsro.transpose('time','latitude','longitude')
    sm=sm.transpose('time','latitude','longitude')
    gw=gw.transpose('time','latitude','longitude')
    bf=bf.transpose('time','latitude','longitude')
    tf=tf.transpose('time','latitude','longitude')

#####################


    
    del Pt
    del E
    del Int
    del nRD
#    del LU
    del lu
    del Rd
    del thetasat
    del SM
    del GW
    del SMmax
    del f_consumed
    del mask
    etb
    attrs={"units":"mm/month", "source": "-", "quantity":"Rainfall_ET_M"}
    etg.attrs=attrs
    etg.name = 'Rainfall_ET_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"Incremental_ET_M"}
    etb.attrs=attrs
    etb.name = 'Incremental_ET_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"SRO_M"}
    sro.attrs=attrs
    sro.name = 'SRO_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"PERC_M"}
    perco.attrs=attrs
    perco.name = 'PERC_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"D_PERC_M"}
    dperc.attrs=attrs
    dperc.name = 'D_PERC_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"Supply_M"}
    supply.attrs=attrs
    supply.name = 'Supply_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"Incremental_SRO_M"}
    dsro.attrs=attrs
    dsro.name = 'Incremental_SRO_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"Root_Depth_Soil_Moisture_M"}
    sm.attrs=attrs
    sm.name = 'Root_Depth_Soil_Moisture_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"Grounwater_Storage_M"}
    gw.attrs=attrs
    gw.name = 'Groundwater_Storage_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"Base_Flow_M"}
    bf.attrs=attrs
    bf.name = 'Base_Flow_M'
    
    attrs={"units":"mm/month", "source": "-", "quantity":"Total_Flow_M"}
    tf.attrs=attrs
    tf.name = 'Total_Flow_M'

    ### Write netCDF files
    # chunks = [1, 300, 300]
    comp = dict(zlib=True, 
                least_significant_digit=2, 
                chunksizes=chunks)
    # comp = dict(zlib=True, 
    #             complevel=9, 
    #             least_significant_digit=2, 
    #             chunksizes=chunks)
# # #    comp = dict(zlib=True, complevel=9, least_significant_digit=2)
    start = time.time()
    print("\n\nwriting the ET_incremental netcdf file\n\n")
    etincr_path=os.path.join(MAIN_FOLDER,'etincr_monthly.nc')
    encoding = {"Incremental_ET_M": comp}
    etb.to_netcdf(etincr_path,encoding=encoding)
    del etb
    end = time.time()
    print('\n',end - start)
    
    ##green ET 
    start = time.time()
    print("\n\nwriting the ET_rain netcdf file\n\n")
    etrain_path=os.path.join(MAIN_FOLDER,'etrain_monthly.nc')
    encoding = {"Rainfall_ET_M": comp}
    etg.to_netcdf(etrain_path,encoding=encoding)
    del etg
    end = time.time()
    print('\n',end - start)
    
    print("\n\nwriting the SRO netcdf file\n\n")
    sro_path=os.path.join(MAIN_FOLDER,'sro_monthly.nc')
    encoding = {"SRO_M": comp}
    sro.to_netcdf(sro_path,encoding=encoding)
    del sro
    
    start = time.time()
    print("\n\nwriting the percolation netcdf file\n\n")
    perco_path=os.path.join(MAIN_FOLDER,'perco_monthly.nc')
    encoding = {"PERC_M": comp}
    perco.to_netcdf(perco_path,encoding=encoding)
    del perco
    end = time.time()
    print('\n',end - start)
    
    start = time.time()
    print("\n\nwriting the incremental percolation netcdf file\n\n")
    dperc_path=os.path.join(MAIN_FOLDER,'d_perco_monthly.nc')
    encoding = {"D_PERC_M": comp}
    dperc.to_netcdf(dperc_path,encoding=encoding)
    del dperc
    end = time.time()
    print('\n',end - start)
    
    start = time.time()
    print("\n\nwriting the supply netcdf file\n\n")
    supply_path=os.path.join(MAIN_FOLDER,'supply_monthly.nc')
    encoding = {"Supply_M": comp}
    supply.to_netcdf(supply_path,encoding=encoding)
    del supply
    end = time.time()
    print('\n',end - start)
    
    start = time.time()
    print("\n\nwriting the incremental runoff netcdf file\n\n")
    dsro_path=os.path.join(MAIN_FOLDER,'d_sro_monthly.nc')
    encoding = {"Incremental_SRO_M": comp}
    dsro.to_netcdf(dsro_path,encoding=encoding)
    del dsro
    end = time.time()
    print('\n',end - start)
    
    start = time.time()
    print("\n\nwriting the root depth soil moisture netcdf file\n\n")
    sm_path=os.path.join(MAIN_FOLDER,'sm_monthly.nc')
    encoding = {"Root_Depth_Soil_Moisture_M": comp}
    sm.to_netcdf(sm_path,encoding=encoding)
    del sm
    end = time.time()
    print('\n',end - start)
    
    start = time.time()
    print("\n\nwriting the groundwater storage netcdf file\n\n")
    gw_path=os.path.join(MAIN_FOLDER,'gw_monthly.nc')
    encoding = {"Groundwater_Storage_M": comp}
    gw.to_netcdf(gw_path,encoding=encoding)
    del gw
    end = time.time()
    print('\n',end - start)
    
    start = time.time()
    print("\n\nwriting the base flow netcdf file\n\n")
    bf_path=os.path.join(MAIN_FOLDER,'bf_monthly.nc')
    encoding = {"Base_Flow_M": comp}
    bf.to_netcdf(bf_path,encoding=encoding)
    del bf
    end = time.time()
    print('\n',end - start)
    
    start = time.time()
    print("\n\nwriting the total flow netcdf file\n\n")
    tf_path=os.path.join(MAIN_FOLDER,'tf_monthly.nc')
    encoding = {"Total_Flow_M": comp}
    tf.to_netcdf(tf_path,encoding=encoding)
    del tf
    end = time.time()
    print('\n',end - start)
        
        
