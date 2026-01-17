# -*- coding: utf-8 -*-
"""
Created on Fri Aug 12 13:23:06 2022

@author: p.thilina-prabhath
"""
import os
import shutil
import glob
from watertools_iwmi.Controller import collect_urls as cu
from watertools_iwmi.Controller import download_hdfs as dh
from watertools_iwmi.Collect import MOD16, MOD15, MOD17
from watertools_iwmi.Functions.Time_Conversions import Eightdaily_to_monthly_flux as em


def generateTiffs(args, hdfs):

    [Dir, product_name, startdate, enddate, latlim, lonlim] = args

    if product_name == 'MOD16':
        pathTiffs = MOD16.ET_8daily(
            Dir, startdate, enddate, latlim, lonlim, hdf_library=hdfs)
    elif product_name == 'LAI':
        pathTiffs = MOD15.LAI_8daily(
            Dir, startdate, enddate, latlim, lonlim, hdf_library=hdfs)
    elif product_name == 'GPP':
        pathTiffs = MOD17.GPP_8daily(
            Dir, startdate, enddate, latlim, lonlim, hdf_library=hdfs)
    elif product_name == 'NPP':
        pathTiffs = MOD17.NPP_yearly(
            Dir, startdate, enddate, latlim, lonlim, hdf_library=hdfs)
    else:
        print('{product_name} is not available currenlty')

    return pathTiffs


def main(Dir, product_name, startdate, enddate, latlim, lonlim, time_conversion=False):

    print(f'|=============== {product_name} =================|')
    print('\nDownload %s data for period %s till %s' %
          (product_name, startdate, enddate))

    granule_collection = {'MOD16': 'C1000000524-LPDAAC_ECS',
                          'LAI': 'C203669720-LPDAAC_ECS',
                          'GPP': 'C203669722-LPDAAC_ECS',
                          'NPP': 'C1631984056-LPDAAC_ECS',
                          }

    collection_id = granule_collection[product_name]

    output_folder = os.path.join(Dir, product_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    args = [Dir, product_name, startdate, enddate, latlim, lonlim]

    # Step 1 - Download links
    print('\nDownloading links...')
    txtFile = cu.getLinks(args, collection_id)

    # Step 2 - Download .hdf
    print('\nDownloading HDFS...')
    hdfs, connect = dh.main(output_folder, txtFile)

    # connect = True
    # hdfs = r'C:\_WA\wasa\codes\Hydroloop_data_download\temp4\NPP\hdf'
    if connect:
        # Step 3 - Merge tiffs
        print('\nMearging and Creating Tiffs...')
        tiffs = generateTiffs(args, hdfs)
        # print(tiffs)
        # tiffs = r'/home/iwmi-wa/WA_Workshop/Data_download_tool/test/GPP/8_daily'
        # Step 4 - Time convertion
        if time_conversion:
            print('\n8-daily to Monthly convertion')
            em.Nearest_Interpolate(tiffs, startdate, enddate)

        # Step 5 - Delete hdfs and 8-daily tifs
        os.remove(txtFile)
        shutil.rmtree(hdfs)
        
        if product_name != 'NPP':
            all_tifs = glob.glob(os.path.join(tiffs, '*.tif'))
            for fh in all_tifs:
                os.remove(fh)
            shutil.rmtree(tiffs)
