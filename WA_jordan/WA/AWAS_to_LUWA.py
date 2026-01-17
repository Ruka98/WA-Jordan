# -*- coding: utf-8 -*-
"""
Created on May,2024

@author: agt
LCC to LUWA
"""


from WA import GIS_functions as gis
import numpy as np
import os
from WA.rasterize_shapefile import Rasterize_shapefile

def Rasterize_shape_basin(shapefile,raster_template,output_raster):

    driver,NDV,xsize,ysize,GeoT,Projection=gis.GetGeoInfo(raster_template)
    latlim=[GeoT[3]+ysize*GeoT[5],GeoT[3]]
    lonlim=[GeoT[0],GeoT[0]+xsize*GeoT[1]]
    xRes=GeoT[1]
    yRes=-GeoT[5]    
    Rasterize_shapefile(shapefile,output_raster,latlim,lonlim,xRes,yRes)
    
def Adjust_GRaND_reservoir(output_raster,LCC,GRaND_Reservoir,
                           Resrv_to_Lake,Lake_to_Reserv):   
  
     #Getting GeoTranformation from LCC map
    driver,NDV,xsize,ysize,GeoT,Projection=gis.GetGeoInfo(LCC)
    latlim=[GeoT[3]+ysize*GeoT[5],GeoT[3]]
    lonlim=[GeoT[0],GeoT[0]+xsize*GeoT[1]]
    xRes=GeoT[1]
    yRes=-GeoT[5]
    #Rasterize selected area for reservoir and un-reservoir shapefile
    Basin_reservoir=os.path.join(os.path.split(Resrv_to_Lake)[0],'Reservoir_GRanD.tif')
    Rasterize_shapefile(GRaND_Reservoir,Basin_reservoir,
                                latlim,lonlim,xRes,yRes)
    Rasterize_shapefile(Resrv_to_Lake,Resrv_to_Lake.replace('.shp','.tif'),
                                latlim,lonlim,xRes,yRes)
    
    Rasterize_shapefile(Lake_to_Reserv,Lake_to_Reserv.replace('.shp','.tif'),
                                latlim,lonlim,xRes,yRes)
    
    #Edit Resvr
    Resrv=gis.OpenAsArray(Basin_reservoir,nan_values=True)
    LCC=gis.OpenAsArray(LCC,nan_values=True)
    UnResrv=gis.OpenAsArray(Resrv_to_Lake.replace('.shp','.tif'),nan_values=True)
    MakeResrv=gis.OpenAsArray(Lake_to_Reserv.replace('.shp','.tif'),nan_values=True)
    
    Resrv=np.where(((LCC==80)*(MakeResrv==1)),1,Resrv)
    Resrv=np.where(((Resrv==1)*(UnResrv==1)),np.nan,Resrv)
    
#    output=os.path.join(os.path.split(Resrv_to_Lake)[0],'Reservoir_adjusted.tif')
    gis.CreateGeoTiff(output_raster, Resrv, driver, NDV, xsize, ysize, GeoT, Projection)
    return output_raster

def Reclass_LCC_to_LUWA_(LCC,Output_dir,ProtectedArea_tif,
                        Reservoir_tif,LCC_LUWA_dict=None):    
    if LCC_LUWA_dict is None:
        LCC_LUWA_dict={
                'PLU':(1,[]),
               'ULU':(2,[]),
               'MLU':(3,[41,43]),#Rainfed crop
               'MWU':(4,[42,50]), #irrigated crop and built-up
               } 
    driver,NDV,xsize,ysize,GeoT,Projection=gis.GetGeoInfo(LCC)
    LCC=gis.OpenAsArray(LCC,nan_values=True)
    #ULU: The default is ULU 
    LUWA=2*np.ones(np.shape(LCC),dtype=np.float32)    
    #PLU: WDPA 
    PLU=gis.OpenAsArray(ProtectedArea_tif,nan_values=True)
    LUWA=np.where(PLU==1,1,LUWA)
    #MLU: Rainfed crop => Modified Land Use
    for code in LCC_LUWA_dict['MLU'][1]:
        LUWA=np.where(LCC==code,3,LUWA)
    #MWU: Irrigated crop, Reservoir, Urban => Managed Water Use
    for code in LCC_LUWA_dict['MWU'][1]:
        LUWA=np.where(LCC==code,4,LUWA)
    MWU=gis.OpenAsArray(Reservoir_tif,nan_values=True)
    LUWA=np.where(MWU==1,4,LUWA)
    output_file=os.path.join(Output_dir,os.path.basename(LCC).replace('LCC','LUWA'))
    gis.CreateGeoTiff(output_file,LUWA,driver,NDV,xsize,ysize,GeoT,Projection)

def Reclass_LCC_to_LUWA(LCC_fh, Output_dir, ProtectedArea_tif, Reservoir_tif, LCC_LUWA_dict=None):
        
    if LCC_LUWA_dict is None:
        LCC_LUWA_dict = {
                      'wapor_classes': ['Code', 'Landuse', 'Wapor_description','Description','lu_new_classes'],
                                        0: ['X','X','n.a','n.a',np.nan],
                                        10: ['ULU3', 'Utilized', 'Cropland, rainfed', 'Rainfed pastures for grazing',10],
                                        14: ['ULU7', 'Utilized', 'Herbaceous cover', 'Herbaceous cover',15],
                                        12: ['ULU8', 'Utilized', 'Tree or shrub cover', 'Shrub land & mesquite',14],
                                        20: ['ULU7', 'Utilized', 'Cropland, irrigated or post‐flooding', 'Irrigated crops - cereals',14],
                                        30: ['ULU9', 'Utilized','Mosaic cropland (>50%) / natural vegetation (tree, shrub, herbaceous cover) (<50%)','Mixed species agro-forestry',16],
                                        41: ['MLU3', 'Modified', 'Mosaic natural vegetation (tree, shrub, herbaceous cover) (>50%) / cropland (<50%)', 'Shrub land & mesquite',35],
                                        42: ['MWU8', 'Utilized', 'Tree cover, broadleaved, deciduous, open (15‐40%)','Open deciduous forest',59],
                                        50: ['MWU21', 'Managed', 'Tree cover, broadleaved, evergreen, closed to open (>15%)', 'Closed evergreen forest', 72],
                                        60: ['ULU20', 'Utilized', 'Tree cover, broadleaved, deciduous, closed to open (>15%)','Closed deciduous forest',27],
                                        61: ['ULU1', 'Utilized', 'Tree cover, broadleaved, deciduous, closed (>40%)', 'Closed deciduous forest',8], 
                                        62: ['ULU2', 'Utilized', 'Tree cover, broadleaved, deciduous, open (15‐40%)','Open deciduous forest',9],
                                        70: ['ULU4', 'Utilized', 'Tree cover, needleleaved, evergreen, closed to open (>15%)', 'Open evergreen forest',11],
                                        71: ['ULU3', 'Utilized', 'Tree cover, needleleaved, evergreen, closed (>40%)', 'Closed evergreen forest', 10],
                                        72: ['ULU4', 'Utilized', 'Tree cover, needleleaved, evergreen, open (15‐40%)', 'Open evergreen forest',11],
                                        80: ['MWU12', 'Managed', 'Tree cover, needleleaved, deciduous, closed to open (>15%)', 'Closed deciduous forest',63],
                                        81: ['ULU1', 'Utilized', 'Tree cover, needleleaved, deciduous, closed (>40%)','Closed evergreen forest',8],
                                        82: ['ULU2', 'Utilized', 'Tree cover, needleleaved, deciduous, open (15‐40%)', 'Open deciduous forest',9],
                                        90: ['MWU24', 'Managed' , 'Tree cover, mixed leaf type (broadleaved and needleleaved)','Open evergreen forest',75],
                                        100: ['ULU7', 'Utilized', 'Mosaic tree and shrub (>50%) / herbaceous cover (<50%)','Shrub land & mesquite',75],
                                        110: ['ULU8', 'Utilized', 'Mosaic herbaceous cover (>50%) / tree and shrub (<50%)', ' Herbaceous cover',15],
                                        120: ['ULU7', 'Utilized', 'Shrubland', 'Shrub land & mesquite',14],
                                        121: ['ULU7', 'Utilized', 'Evergreen shrubland','Shrub land & mesquite',14],
                                        122: ['ULU7', 'Utilized', 'Deciduous shrubland','Shrub land & mesquite',14],
                                        130: ['ULU9', 'Utilized', 'Grassland','Meadows & open grassland',16],
                                        140: ['ULU23', 'Utilized', 'Lichens and mosses','Wetland',30],
                                        150: ['ULU7', 'Utilized', 'Sparse vegetation (tree, shrub, herbaceous cover) (<15%)','Shrub land & mesquite',14],
                                        151: ['ULU7', 'Utilized', 'Sparse tree (<15%)','Shrub land & mesquite',14],
                                        152: ['ULU7', 'Utilized', 'Sparse shrub (<15%)','Shrub land & mesquite',14],
                                        153: ['ULU8', 'Utilized', 'Sparse herbaceous cover (<15%)',' Herbaceous cover',15],
                                        160: ['ULU23', 'Utilized', 'Tree cover, flooded, fresh or brakish water','Wetland',30],
                                        170: ['ULU23', 'Utilized', 'Tree cover, flooded, fresh or brakish water','Wetland',30],
                                        180: ['ULU7', 'Utilized', 'Shrub or herbaceous cover, flooded, fresh/saline/brakish water','Shrub land & mesquite',14],
                                        190: ['MWU21', 'Managed', 'Urban areas','Urban paved Surface (lots, roads, lanes)',72],
                                        200: ['ULU20', 'Utilized', 'Bare areas','Bare soil',27],
                                        201: ['ULU20', 'Utilized', 'Consolidated bare areas','Bare soil',27],
                                        202: ['ULU20', 'Utilized', 'Unconsolidated bare areas','Bare soil',27],
                                        210: ['MWU12', 'Managed', 'Water bodies', 'Managed water bodies (reservoirs, canals, harbors, tanks)',63],
                                        220: ['ULU15', 'Utilized', 'Permanent snow and ice', 'Permafrosts',22]
                                        
                                        
                 }
        
 
    driver,NDV,xsize,ysize,GeoT,Projection=gis.GetGeoInfo(LCC_fh)
    LCC=gis.OpenAsArray(LCC_fh,nan_values=True)
    LULC = LCC.astype(np.float)
    for lu_class in list(LCC_LUWA_dict.keys())[1:]:
        LULC[LULC == lu_class] = LCC_LUWA_dict[lu_class][4]

    Protected_dict = {
                 'legend':['Code','wa_lu'],
                     1:['PLU1',[8,9,10,11]],
                     2:['PLU2',[14]],
                     3:['PLU3',[12,13]],
                     4:['PLU4',[23,24]],
                     5:['PLU5',[30,74]]            
                 }
    
    #PLU: WDPA
    PLU=np.where(np.isnan(gis.OpenAsArray(ProtectedArea_tif,nan_values=True)),False,True)
    mask = np.zeros(np.shape(LULC)).astype(np.bool)
    mask_all = np.zeros(np.shape(LULC)).astype(np.bool)
    for key,values in Protected_dict.items():
        if isinstance(key, int):            
            mask = np.all([PLU, np.logical_or.reduce([LULC == x for x in values[1:][0]])], axis = 0)
            mask_all = np.any([mask_all,mask],axis=0)
            LULC[mask] = key             
    
    #Protected:other categorise as 7
    mask_other = np.where(mask_all,False,True)
    mask_all_ = np.all([PLU,mask_other], axis=0)    
    mask_all_ = np.where(np.isnan(LULC),False,mask_all_)
    LULC=np.where(mask_all_,7,LULC)
    
    #MWU: Irrigated crop, Reservoir, Urban => Managed Water Use
    MWU=gis.OpenAsArray(Reservoir_tif,nan_values=True)
    LULC=np.where(MWU==1,63,LULC)   
    explicit = True
    compress = 'LZW'
    
    output_file=os.path.join(Output_dir,os.path.basename(LCC_fh).replace('LCC','LUWA'))
    gis.CreateGeoTiff(output_file,LULC,driver,NDV,xsize,ysize,GeoT,Projection) 
    
    