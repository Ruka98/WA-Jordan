# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 17:08:23 2020

@author: ntr002

print WA+ sheets (png or svg) from csv template
"""
import os
import sys
import pandas as pd
import numpy as np
import cairosvg
import datetime
import xml.etree.ElementTree as ET
import shutil

def get_template(sheet_name,template_folder='Default'):
    '''
    
    '''
    #using default template
    if template_folder=='Default':
        module_path = os.path.abspath(__file__) #get module path
        module_folder = os.path.dirname(module_path) #get module folder
        template_folder=os.path.join(module_folder,
                                     'template',
                                     'svg') #get template folder
    #get sheet template    
    template_path=os.path.join(template_folder,
                               '{0}.svg'.format(sheet_name))
    if not os.path.exists(template_path):
        print('This template does not exist:\
              {0}'.format(template_path))
        sys.exit()
        
    return template_path

def scale_factor(scale_test):
    scale = 0
    while np.all([scale_test < 10.000, scale_test != 0.0]):
        scale_test *= 10
        scale += 1
    scale = float(np.min([2,scale]))
    return scale


def print_sheet1(basin, period, units, data, output, template=False , smart_unit = False):
    """
    Keyword arguments:
    basin -- The name of the basin
    period -- The period of analysis
    units -- The units of the data
    data -- A csv file that contains the water data. The csv file has to
            follow an specific format. A sample csv is available in the link:
            https://github.com/wateraccounting/wa/tree/master/Sheets/csv
    output -- The output path of the jpg file for the sheet.
    template -- A svg file of the sheet. Use False (default) to use the
                standard svg file.
    Example:
    from wa.Sheets import *
    create_sheet1(basin='Incomati', period='2005-2010', units='km3/year',
                  data=r'C:\Sheets\csv\Sample_sheet1.csv',
                  output=r'C:\Sheets\sheet_1.jpg')
    """
#    decimals = 1
    # Read table

    df = pd.read_csv(data, sep=';')
    
    scale = 0
    if smart_unit:
        scale_test = np.nanmax(df['VALUE'].values)
        scale = scale_factor(scale_test)
        df['VALUE'] *= 10**scale

    # Data frames

    df_i = df.loc[df.CLASS == "INFLOW"]
    df_s = df.loc[df.CLASS == "STORAGE"]
    df_o = df.loc[df.CLASS == "OUTFLOW"]

    # Inflow data

    rainfall = float(df_i.loc[(df_i.SUBCLASS == "PRECIPITATION") &
                              (df_i.VARIABLE == "Rainfall")].VALUE)
    snowfall = float(df_i.loc[(df_i.SUBCLASS == "PRECIPITATION") &
                              (df_i.VARIABLE == "Snowfall")].VALUE)
    p_recy = float(df_i.loc[(df_i.SUBCLASS == "PRECIPITATION") &
                   (df_i.VARIABLE == "Precipitation recycling")].VALUE)

    sw_mrs_i = float(df_i.loc[(df_i.SUBCLASS == "SURFACE WATER") &
                              (df_i.VARIABLE == "Main riverstem")].VALUE)
    sw_tri_i = float(df_i.loc[(df_i.SUBCLASS == "SURFACE WATER") &
                              (df_i.VARIABLE == "Tributaries")].VALUE)
    sw_usw_i = float(df_i.loc[(df_i.SUBCLASS == "SURFACE WATER") &
                     (df_i.VARIABLE == "Utilized surface water")].VALUE)
    sw_flo_i = float(df_i.loc[(df_i.SUBCLASS == "SURFACE WATER") &
                              (df_i.VARIABLE == "Flood")].VALUE)

    gw_nat_i = float(df_i.loc[(df_i.SUBCLASS == "GROUNDWATER") &
                              (df_i.VARIABLE == "Natural")].VALUE)
    gw_uti_i = float(df_i.loc[(df_i.SUBCLASS == "GROUNDWATER") &
                              (df_i.VARIABLE == "Utilized")].VALUE)

    q_desal = float(df_i.loc[(df_i.SUBCLASS == "OTHER") &
                             (df_i.VARIABLE == "Desalinized")].VALUE)

    # Storage data

    surf_sto = float(df_s.loc[(df_s.SUBCLASS == "CHANGE") &
                              (df_s.VARIABLE == "Surface storage")].VALUE)
    sto_sink = float(df_s.loc[(df_s.SUBCLASS == "CHANGE") &
                              (df_s.VARIABLE == "Storage in sinks")].VALUE)

    # Outflow data

    et_l_pr = float(df_o.loc[(df_o.SUBCLASS == "ET LANDSCAPE") &
                             (df_o.VARIABLE == "Protected")].VALUE)
    et_l_ut = float(df_o.loc[(df_o.SUBCLASS == "ET LANDSCAPE") &
                             (df_o.VARIABLE == "Utilized")].VALUE)
    et_l_mo = float(df_o.loc[(df_o.SUBCLASS == "ET LANDSCAPE") &
                             (df_o.VARIABLE == "Modified")].VALUE)
    et_l_ma = float(df_o.loc[(df_o.SUBCLASS == "ET LANDSCAPE") &
                             (df_o.VARIABLE == "Managed")].VALUE)

    et_u_pr = float(df_o.loc[(df_o.SUBCLASS == "ET UTILIZED FLOW") &
                             (df_o.VARIABLE == "Protected")].VALUE)
    et_u_ut = float(df_o.loc[(df_o.SUBCLASS == "ET UTILIZED FLOW") &
                             (df_o.VARIABLE == "Utilized")].VALUE)
    et_u_mo = float(df_o.loc[(df_o.SUBCLASS == "ET UTILIZED FLOW") &
                             (df_o.VARIABLE == "Modified")].VALUE)

    et_u_ma = float(df_o.loc[(df_o.SUBCLASS == "ET UTILIZED FLOW") &
                             (df_o.VARIABLE == "Managed")].VALUE)

    et_manmade = float(df_o.loc[(df_o.SUBCLASS == "ET INCREMENTAL") &
                                (df_o.VARIABLE == "Manmade")].VALUE)
    et_natural = float(df_o.loc[(df_o.SUBCLASS == "ET INCREMENTAL") &
                                (df_o.VARIABLE == "Natural")].VALUE)

    sw_mrs_o = float(df_o.loc[(df_o.SUBCLASS == "SURFACE WATER") &
                              (df_o.VARIABLE == "Main riverstem")].VALUE)
    sw_tri_o = float(df_o.loc[(df_o.SUBCLASS == "SURFACE WATER") &
                              (df_o.VARIABLE == "Tributaries")].VALUE)
    sw_usw_o = float(df_o.loc[(df_o.SUBCLASS == "SURFACE WATER") &
                     (df_o.VARIABLE == "Utilized surface water")].VALUE)
    sw_flo_o = float(df_o.loc[(df_o.SUBCLASS == "SURFACE WATER") &
                              (df_o.VARIABLE == "Flood")].VALUE)

    gw_nat_o = float(df_o.loc[(df_o.SUBCLASS == "GROUNDWATER") &
                              (df_o.VARIABLE == "Natural")].VALUE)
    gw_uti_o = float(df_o.loc[(df_o.SUBCLASS == "GROUNDWATER") &
                              (df_o.VARIABLE == "Utilized")].VALUE)

    basin_transfers = float(df_o.loc[(df_o.SUBCLASS == "SURFACE WATER") &
                            (df_o.VARIABLE == "Interbasin transfer")].VALUE)
    non_uti = float(df_o.loc[(df_o.SUBCLASS == "OTHER") &
                             (df_o.VARIABLE == "Non-utilizable")].VALUE)
    other_o = float(df_o.loc[(df_o.SUBCLASS == "OTHER") &
                             (df_o.VARIABLE == "Other")].VALUE)

    com_o = float(df_o.loc[(df_o.SUBCLASS == "RESERVED") &
                           (df_o.VARIABLE == "Commited")].VALUE)
    nav_o = float(df_o.loc[(df_o.SUBCLASS == "RESERVED") &
                           (df_o.VARIABLE == "Navigational")].VALUE)
    env_o = float(df_o.loc[(df_o.SUBCLASS == "RESERVED") &
                           (df_o.VARIABLE == "Environmental")].VALUE)

    # Calculations & modify svg
    if not template:        
        svg_template_path = get_template('sheet_1_cwa',
                                         template_folder='Default')
    else:
        svg_template_path = os.path.abspath(template)

    tree = ET.parse(svg_template_path)

    # Titles

    xml_txt_box = tree.findall('''.//*[@id='basin']''')[0]
    list(xml_txt_box)[0].text = 'Basin: ' + basin

    xml_txt_box = tree.findall('''.//*[@id='period']''')[0]
    list(xml_txt_box)[0].text = 'Period: ' + period

    xml_txt_box = tree.findall('''.//*[@id='units']''')[0]
    
    if np.all([smart_unit, scale > 0]):
        list(xml_txt_box)[0].text = 'Sheet 1: Resource Base ({0} {1})'.format(10**-scale, units)
    else:
        list(xml_txt_box)[0].text = 'Sheet 1: Resource Base ({0})'.format(units)

    # Grey box

    p_advec = rainfall + snowfall
    q_sw_in = sw_mrs_i + sw_tri_i + sw_usw_i + sw_flo_i
    q_gw_in = gw_nat_i + gw_uti_i

    external_in = p_advec + q_desal + q_sw_in + q_gw_in
    gross_inflow = external_in + p_recy

    delta_s = surf_sto + sto_sink
    
    # Pink box

    net_inflow = gross_inflow + delta_s
    
    p1 = {
            'external_in' : external_in,
            'p_advec' : p_advec,
            'q_desal' : q_desal,
            'q_sw_in' : q_sw_in,
            'q_gw_in' : q_gw_in,
            'p_recycled' : p_recy,
            'gross_inflow' : gross_inflow,
            'net_inflow' : net_inflow
            }
 
    for key in list(p1.keys()):
        if tree.findall(".//*[@id='{0}']".format(key)) != []:
            xml_txt_box = tree.findall(".//*[@id='{0}']".format(key))[0]
            if not pd.isnull(p1[key]):
                if p1[key] < 0.1:
                    list(xml_txt_box)[0].text = '%.1f' % 0                
                else:
                    list(xml_txt_box)[0].text = '%.1f' % p1[key]
            else:
               list(xml_txt_box)[0].text = '-'
    
    delta_s_posbox = (delta_s + abs(delta_s))/2
    delta_s_negbox = abs(delta_s - abs(delta_s))/2 
    
    st = {
            'pos_delta_s' : delta_s_posbox,
            'neg_delta_s' : delta_s_negbox
            }

    for key in list(st.keys()):
        if tree.findall(".//*[@id='{0}']".format(key)) != []:
            xml_txt_box = tree.findall(".//*[@id='{0}']".format(key))[0]
            if not pd.isnull(st[key]):
                if st[key] < 0.1:
                    list(xml_txt_box)[0].text = '%.1f' % 0
                else:
                    list(xml_txt_box)[0].text = '%.1f' % st[key]
            else:
               list(xml_txt_box)[0].text = '-'    

    # Light-green box
    land_et = et_l_pr + et_l_ut + et_l_mo + et_l_ma
    
    # landscape et
    landsc_et = land_et + et_u_pr + et_u_ut + et_u_mo #duplicate number, unneeded

    p2 = {
            'landscape_et' : landsc_et,
            'green_protected' : et_l_pr,
            'green_utilized' : et_l_ut,
            'green_modified' : et_l_mo,
            'green_managed' : et_l_ma,
            'rainfall_et' : land_et,
#            'landscape_et' : landsc_et
            }
    
    for key in list(p2.keys()):
        if tree.findall(".//*[@id='{0}']".format(key)) != []:
            xml_txt_box = tree.findall(".//*[@id='{0}']".format(key))[0]
            if not pd.isnull(p2[key]):
                if p2[key] < 0.1:
                    list(xml_txt_box)[0].text = '%.1f' % 0
                else:
                    list(xml_txt_box)[0].text = '%.1f' % p2[key]
            else:
               list(xml_txt_box)[0].text = '-'

    # Blue box (center)

    exploitable_water = net_inflow - land_et - et_u_pr - et_u_ut - et_u_mo
    reserved_outflow = max(com_o, nav_o, env_o)

    available_water = exploitable_water - non_uti - reserved_outflow

#    utilized_flow = et_u_pr + et_u_ut + et_u_mo + et_u_ma
    utilized_flow = et_u_ma    
    utilizable_outflow = available_water - utilized_flow

    inc_et = et_manmade + et_natural

    non_cons_water = utilizable_outflow + non_uti + reserved_outflow

    non_rec_flow = et_u_pr + et_u_ut + et_u_mo + et_u_ma - inc_et - other_o
    # fixing the "-0.0"
    if non_rec_flow < 0.0:
        non_rec_flow = 0.0
    
    p3 = {
            'incremental_etman' : et_manmade,
            'incremental_etnat' : et_natural,
            'exploitable_water' : exploitable_water,
            'available_water' : available_water,
            'blue_protected' : et_u_pr,
            'blue_utilized' : et_u_ut,
            'blue_modified' : et_u_mo,
            'blue_managed' : et_u_ma,
            'utilizable_outflow' : utilizable_outflow,
            'non-utilizable_outflow' : non_uti,
            'reserved_outflow_max' : reserved_outflow,
            'non-consumed_water' : non_cons_water,
            'non-recoverable_flow' : non_rec_flow
            }

    for key in list(p3.keys()):
        if tree.findall(".//*[@id='{0}']".format(key)) != []:
            xml_txt_box = tree.findall(".//*[@id='{0}']".format(key))[0]
            if not pd.isnull(p3[key]):
                if p3[key] < 0.1:
                    list(xml_txt_box)[0].text = '%.1f' % 0
                else:
                    list(xml_txt_box)[0].text = '%.1f' % p3[key]
            else:
               list(xml_txt_box)[0].text = '-'

#    xml_txt_box = tree.findall('''.//*[@id='utilized_flow']''')[0]
#    list(xml_txt_box)[0].text = '{1:.{0}f}'.format(decimals, utilized_flow)

#    xml_txt_box = tree.findall('''.//*[@id='manmade']''')[0]
#    list(xml_txt_box)[0].text = '{1:.{0}f}'.format(decimals, et_manmade)
#
#    xml_txt_box = tree.findall('''.//*[@id='natural']''')[0]
#    list(xml_txt_box)[0].text = '{1:.{0}f}'.format(decimals, et_natural)

#    xml_txt_box = tree.findall('''.//*[@id='other']''')[0]
#    list(xml_txt_box)[0].text = '{1:.{0}f}'.format(decimals, other_o)


    # Blue box (right)

    outflow = non_cons_water + non_rec_flow 

    q_sw_out = sw_mrs_o + sw_tri_o + sw_usw_o + sw_flo_o 
    q_gw_out = gw_nat_o + gw_uti_o
    
    # Dark-green box
    consumed_water = landsc_et + utilized_flow
    depleted_water = consumed_water - p_recy - non_rec_flow
    external_out = depleted_water + outflow
    
    p4 = {
            'outflow' : outflow,
            'q_sw_outlet' : q_sw_out,
            'q_sw_out' : basin_transfers,
            'q_gw_out' : q_gw_out,
            'et_recycled' : p_recy,
            'consumed_water' : consumed_water,
            'depleted_water' : depleted_water,
            'external_out' : external_out,
            'et_out' : depleted_water
            }

    for key in list(p4.keys()):
        if tree.findall(".//*[@id='{0}']".format(key)) != []:
            xml_txt_box = tree.findall(".//*[@id='{0}']".format(key))[0]
            if not pd.isnull(p4[key]):
                if p4[key] < 0.1:
                    list(xml_txt_box)[0].text = '%.1f' % 0
                else:
                    list(xml_txt_box)[0].text = '%.1f' % p4[key]
            else:
               list(xml_txt_box)[0].text = '-'

#    # Export svg to pdf
    tempout_path = output.replace('.pdf', '_temporary.svg')
    tree.write(tempout_path)    
    cairosvg.svg2pdf(url=tempout_path, write_to=output)    

    # Return
    return output

def print_sheet2(basin, period, units, data, output, template=False,
                  tolerance=0.2, smart_unit = False):
    """

    Keyword arguments:
    basin -- The name of the basin
    period -- The period of analysis
    units -- The units of the data
    data -- A csv file that contains the water data. The csv file has to
            follow an specific format. A sample csv is available in the link:
            https://github.com/wateraccounting/wa/tree/master/Sheets/csv
    output -- The output path of the jpg file for the sheet.
    template -- A svg file of the sheet. Use False (default) to use the
                standard svg file.
    tolerance -- Tolerance (in km3/year) of the difference in total ET
                 measured from (1) evaporation and transpiration and
                 (2) beneficial and non-beneficial ET.

    Example:
    from wa.Sheets import *
    create_sheet2(basin='Nile Basin', period='2010', units='km3/year',
                  data=r'C:\Sheets\csv\Sample_sheet2.csv',
                  output=r'C:\Sheets\sheet_2.jpg')
    """

    # Read table

    df = pd.read_csv(data, sep=';')

    scale = 0
    if smart_unit:
        scale_test = np.nansum(df['TRANSPIRATION'].values + 
                               df['WATER'].values + 
                               df['SOIL'].values + 
                               df['INTERCEPTION'].values)
        scale = scale_factor(scale_test)
        
        list_of_vars = [key for key in list(df.keys())]
        
        for vari in ['LAND_USE', 'CLASS']:
            idx = list_of_vars.index(vari)           
            del list_of_vars[idx]
        
        for vari in list_of_vars:
            df[vari] *= 10**scale
        
    # Data frames

    df_Pr = df.loc[df.LAND_USE == "PROTECTED"]
    df_Ut = df.loc[df.LAND_USE == "UTILIZED"]
    df_Mo = df.loc[df.LAND_USE == "MODIFIED"]
    df_Mc = df.loc[df.LAND_USE == "MANAGED CONVENTIONAL"]
    df_Mn = df.loc[df.LAND_USE == "MANAGED NON_CONVENTIONAL"]

    # Column 1: Transpiration

    c1r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].TRANSPIRATION)
    c1r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].TRANSPIRATION)
    c1r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].TRANSPIRATION)
    c1r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].TRANSPIRATION)
    c1r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].TRANSPIRATION)
    c1r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].TRANSPIRATION)
    c1r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].TRANSPIRATION)
    c1_t1_total = c1r1_t1 + c1r2_t1 + c1r3_t1 + c1r4_t1 + c1r5_t1 + \
        c1r6_t1 + c1r7_t1

    c1r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].TRANSPIRATION)
    c1r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].TRANSPIRATION)
    c1r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].TRANSPIRATION)
    c1r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].TRANSPIRATION)
    c1r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].TRANSPIRATION)
    c1r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].TRANSPIRATION)
    c1_t2_total = c1r1_t2 + c1r2_t2 + c1r3_t2 + c1r4_t2 + c1r5_t2 + c1r6_t2

    c1r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].TRANSPIRATION)
    c1r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].TRANSPIRATION)
    c1r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].TRANSPIRATION)
    c1r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].TRANSPIRATION)
    c1_t3_total = c1r1_t3 + c1r2_t3 + c1r3_t3 + c1r4_t3

    c1r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].TRANSPIRATION)
    c1r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].TRANSPIRATION)
    c1r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].TRANSPIRATION)
    c1r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].TRANSPIRATION)
    c1r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].TRANSPIRATION)
    c1_t4_total = c1r1_t4 + c1r2_t4 + c1r3_t4 + c1r4_t4 + c1r5_t4

    c1r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].TRANSPIRATION)
    c1r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].TRANSPIRATION)
    c1r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].TRANSPIRATION)
    c1r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].TRANSPIRATION)
    c1r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].TRANSPIRATION)
    c1r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].TRANSPIRATION)
    c1_t5_total = c1r1_t5 + c1r2_t5 + c1r3_t5 + c1r4_t5 + c1r5_t5 + c1r6_t5

    # Column 2: Water

    c2r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].WATER)
    c2r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].WATER)
    c2r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].WATER)
    c2r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].WATER)
    c2r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].WATER)
    c2r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].WATER)
    c2r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].WATER)
    c2_t1_total = c2r1_t1 + c2r2_t1 + c2r3_t1 + c2r4_t1 + c2r5_t1 + \
        c2r6_t1 + c2r7_t1

    c2r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].WATER)
    c2r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].WATER)
    c2r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].WATER)
    c2r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].WATER)
    c2r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].WATER)
    c2r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].WATER)
    c2_t2_total = c2r1_t2 + c2r2_t2 + c2r3_t2 + c2r4_t2 + c2r5_t2 + c2r6_t2

    c2r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].WATER)
    c2r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].WATER)
    c2r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].WATER)
    c2r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].WATER)
    c2_t3_total = c2r1_t3 + c2r2_t3 + c2r3_t3 + c2r4_t3

    c2r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].WATER)
    c2r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].WATER)
    c2r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].WATER)
    c2r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].WATER)
    c2r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].WATER)
    c2_t4_total = c2r1_t4 + c2r2_t4 + c2r3_t4 + c2r4_t4 + c2r5_t4

    c2r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].WATER)
    c2r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].WATER)
    c2r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].WATER)
    c2r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].WATER)
    c2r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].WATER)
    c2r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].WATER)
    c2_t5_total = c2r1_t5 + c2r2_t5 + c2r3_t5 + c2r4_t5 + c2r5_t5 + c2r6_t5

    # Column 3: Soil

    c3r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].SOIL)
    c3r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].SOIL)
    c3r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].SOIL)
    c3r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].SOIL)
    c3r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].SOIL)
    c3r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].SOIL)
    c3r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].SOIL)
    c3_t1_total = c3r1_t1 + c3r2_t1 + c3r3_t1 + c3r4_t1 + c3r5_t1 + \
        c3r6_t1 + c3r7_t1

    c3r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].SOIL)
    c3r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].SOIL)
    c3r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].SOIL)
    c3r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].SOIL)
    c3r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].SOIL)
    c3r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].SOIL)
    c3_t2_total = c3r1_t2 + c3r2_t2 + c3r3_t2 + c3r4_t2 + c3r5_t2 + c3r6_t2

    c3r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].SOIL)
    c3r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].SOIL)
    c3r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].SOIL)
    c3r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].SOIL)
    c3_t3_total = c3r1_t3 + c3r2_t3 + c3r3_t3 + c3r4_t3

    c3r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].SOIL)
    c3r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].SOIL)
    c3r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].SOIL)
    c3r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].SOIL)
    c3r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].SOIL)
    c3_t4_total = c3r1_t4 + c3r2_t4 + c3r3_t4 + c3r4_t4 + c3r5_t4

    c3r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].SOIL)
    c3r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].SOIL)
    c3r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].SOIL)
    c3r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].SOIL)
    c3r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].SOIL)
    c3r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].SOIL)
    c3_t5_total = c3r1_t5 + c3r2_t5 + c3r3_t5 + c3r4_t5 + c3r5_t5 + c3r6_t5

    # Column 4: INTERCEPTION

    c4r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].INTERCEPTION)
    c4r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].INTERCEPTION)
    c4r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].INTERCEPTION)
    c4r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].INTERCEPTION)
    c4r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].INTERCEPTION)
    c4r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].INTERCEPTION)
    c4r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].INTERCEPTION)
    c4_t1_total = c4r1_t1 + c4r2_t1 + c4r3_t1 + c4r4_t1 + c4r5_t1 + \
        c4r6_t1 + c4r7_t1

    c4r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].INTERCEPTION)
    c4r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].INTERCEPTION)
    c4r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].INTERCEPTION)
    c4r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].INTERCEPTION)
    c4r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].INTERCEPTION)
    c4r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].INTERCEPTION)
    c4_t2_total = c4r1_t2 + c4r2_t2 + c4r3_t2 + c4r4_t2 + c4r5_t2 + c4r6_t2

    c4r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].INTERCEPTION)
    c4r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].INTERCEPTION)
    c4r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].INTERCEPTION)
    c4r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].INTERCEPTION)
    c4_t3_total = c4r1_t3 + c4r2_t3 + c4r3_t3 + c4r4_t3

    c4r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].INTERCEPTION)
    c4r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].INTERCEPTION)
    c4r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].INTERCEPTION)
    c4r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].INTERCEPTION)
    c4r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].INTERCEPTION)
    c4_t4_total = c4r1_t4 + c4r2_t4 + c4r3_t4 + c4r4_t4 + c4r5_t4

    c4r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].INTERCEPTION)
    c4r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].INTERCEPTION)
    c4r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].INTERCEPTION)
    c4r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].INTERCEPTION)
    c4r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].INTERCEPTION)
    c4r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].INTERCEPTION)
    c4_t5_total = c4r1_t5 + c4r2_t5 + c4r3_t5 + c4r4_t5 + c4r5_t5 + c4r6_t5

    # Column 6: AGRICULTURE

    c6r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].AGRICULTURE)
    c6r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].AGRICULTURE)
    c6r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].AGRICULTURE)
    c6r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].AGRICULTURE)
    c6r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].AGRICULTURE)
    c6r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].AGRICULTURE)
    c6r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].AGRICULTURE)
    c6_t1_total = c6r1_t1 + c6r2_t1 + c6r3_t1 + c6r4_t1 + c6r5_t1 + \
        c6r6_t1 + c6r7_t1

    c6r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].AGRICULTURE)
    c6r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].AGRICULTURE)
    c6r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].AGRICULTURE)
    c6r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].AGRICULTURE)
    c6r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].AGRICULTURE)
    c6r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].AGRICULTURE)
    c6_t2_total = c6r1_t2 + c6r2_t2 + c6r3_t2 + c6r4_t2 + c6r5_t2 + c6r6_t2

    c6r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].AGRICULTURE)
    c6r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].AGRICULTURE)
    c6r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].AGRICULTURE)
    c6r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].AGRICULTURE)
    c6_t3_total = c6r1_t3 + c6r2_t3 + c6r3_t3 + c6r4_t3

    c6r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].AGRICULTURE)
    c6r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].AGRICULTURE)
    c6r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].AGRICULTURE)
    c6r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].AGRICULTURE)
    c6r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].AGRICULTURE)
    c6_t4_total = c6r1_t4 + c6r2_t4 + c6r3_t4 + c6r4_t4 + c6r5_t4

    c6r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].AGRICULTURE)
    c6r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].AGRICULTURE)
    c6r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].AGRICULTURE)
    c6r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].AGRICULTURE)
    c6r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].AGRICULTURE)
    c6r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].AGRICULTURE)
    c6_t5_total = c6r1_t5 + c6r2_t5 + c6r3_t5 + c6r4_t5 + c6r5_t5 + c6r6_t5

    # Column 7: ENVIRONMENT

    c7r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].ENVIRONMENT)
    c7r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].ENVIRONMENT)
    c7r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].ENVIRONMENT)
    c7r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].ENVIRONMENT)
    c7r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].ENVIRONMENT)
    c7r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].ENVIRONMENT)
    c7r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].ENVIRONMENT)
    c7_t1_total = c7r1_t1 + c7r2_t1 + c7r3_t1 + c7r4_t1 + c7r5_t1 + \
        c7r6_t1 + c7r7_t1

    c7r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].ENVIRONMENT)
    c7r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].ENVIRONMENT)
    c7r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].ENVIRONMENT)
    c7r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].ENVIRONMENT)
    c7r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].ENVIRONMENT)
    c7r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].ENVIRONMENT)
    c7_t2_total = c7r1_t2 + c7r2_t2 + c7r3_t2 + c7r4_t2 + c7r5_t2 + c7r6_t2

    c7r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].ENVIRONMENT)
    c7r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].ENVIRONMENT)
    c7r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].ENVIRONMENT)
    c7r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].ENVIRONMENT)
    c7_t3_total = c7r1_t3 + c7r2_t3 + c7r3_t3 + c7r4_t3

    c7r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].ENVIRONMENT)
    c7r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].ENVIRONMENT)
    c7r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].ENVIRONMENT)
    c7r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].ENVIRONMENT)
    c7r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].ENVIRONMENT)
    c7_t4_total = c7r1_t4 + c7r2_t4 + c7r3_t4 + c7r4_t4 + c7r5_t4

    c7r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].ENVIRONMENT)
    c7r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].ENVIRONMENT)
    c7r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].ENVIRONMENT)
    c7r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].ENVIRONMENT)
    c7r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].ENVIRONMENT)
    c7r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].ENVIRONMENT)
    c7_t5_total = c7r1_t5 + c7r2_t5 + c7r3_t5 + c7r4_t5 + c7r5_t5 + c7r6_t5

    # Column 8: ECONOMY

    c8r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].ECONOMY)
    c8r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].ECONOMY)
    c8r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].ECONOMY)
    c8r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].ECONOMY)
    c8r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].ECONOMY)
    c8r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].ECONOMY)
    c8r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].ECONOMY)
    c8_t1_total = c8r1_t1 + c8r2_t1 + c8r3_t1 + c8r4_t1 + c8r5_t1 + \
        c8r6_t1 + c8r7_t1

    c8r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].ECONOMY)
    c8r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].ECONOMY)
    c8r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].ECONOMY)
    c8r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].ECONOMY)
    c8r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].ECONOMY)
    c8r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].ECONOMY)
    c8_t2_total = c8r1_t2 + c8r2_t2 + c8r3_t2 + c8r4_t2 + c8r5_t2 + c8r6_t2

    c8r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].ECONOMY)
    c8r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].ECONOMY)
    c8r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].ECONOMY)
    c8r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].ECONOMY)
    c8_t3_total = c8r1_t3 + c8r2_t3 + c8r3_t3 + c8r4_t3

    c8r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].ECONOMY)
    c8r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].ECONOMY)
    c8r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].ECONOMY)
    c8r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].ECONOMY)
    c8r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].ECONOMY)
    c8_t4_total = c8r1_t4 + c8r2_t4 + c8r3_t4 + c8r4_t4 + c8r5_t4

    c8r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].ECONOMY)
    c8r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].ECONOMY)
    c8r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].ECONOMY)
    c8r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].ECONOMY)
    c8r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].ECONOMY)
    c8r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].ECONOMY)
    c8_t5_total = c8r1_t5 + c8r2_t5 + c8r3_t5 + c8r4_t5 + c8r5_t5 + c8r6_t5

    # Column 9: ENERGY

    c9r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].ENERGY)
    c9r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].ENERGY)
    c9r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].ENERGY)
    c9r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].ENERGY)
    c9r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].ENERGY)
    c9r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].ENERGY)
    c9r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].ENERGY)
    c9_t1_total = c9r1_t1 + c9r2_t1 + c9r3_t1 + c9r4_t1 + c9r5_t1 + \
        c9r6_t1 + c9r7_t1

    c9r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].ENERGY)
    c9r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].ENERGY)
    c9r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].ENERGY)
    c9r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].ENERGY)
    c9r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].ENERGY)
    c9r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].ENERGY)
    c9_t2_total = c9r1_t2 + c9r2_t2 + c9r3_t2 + c9r4_t2 + c9r5_t2 + c9r6_t2

    c9r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].ENERGY)
    c9r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].ENERGY)
    c9r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].ENERGY)
    c9r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].ENERGY)
    c9_t3_total = c9r1_t3 + c9r2_t3 + c9r3_t3 + c9r4_t3

    c9r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].ENERGY)
    c9r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].ENERGY)
    c9r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].ENERGY)
    c9r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].ENERGY)
    c9r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].ENERGY)
    c9_t4_total = c9r1_t4 + c9r2_t4 + c9r3_t4 + c9r4_t4 + c9r5_t4

    c9r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].ENERGY)
    c9r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].ENERGY)
    c9r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].ENERGY)
    c9r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].ENERGY)
    c9r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].ENERGY)
    c9r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].ENERGY)
    c9_t5_total = c9r1_t5 + c9r2_t5 + c9r3_t5 + c9r4_t5 + c9r5_t5 + c9r6_t5

    # Column 10: LEISURE

    c10r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].LEISURE)
    c10r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].LEISURE)
    c10r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].LEISURE)
    c10r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].LEISURE)
    c10r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].LEISURE)
    c10r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].LEISURE)
    c10r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].LEISURE)
    c10_t1_total = c10r1_t1 + c10r2_t1 + c10r3_t1 + c10r4_t1 + c10r5_t1 + \
        c10r6_t1 + c10r7_t1

    c10r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].LEISURE)
    c10r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].LEISURE)
    c10r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].LEISURE)
    c10r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].LEISURE)
    c10r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].LEISURE)
    c10r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].LEISURE)
    c10_t2_total = c10r1_t2 + c10r2_t2 + c10r3_t2 + c10r4_t2 + \
        c10r5_t2 + c10r6_t2

    c10r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].LEISURE)
    c10r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].LEISURE)
    c10r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].LEISURE)
    c10r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].LEISURE)
    c10_t3_total = c10r1_t3 + c10r2_t3 + c10r3_t3 + c10r4_t3

    c10r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].LEISURE)
    c10r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].LEISURE)
    c10r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].LEISURE)
    c10r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].LEISURE)
    c10r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].LEISURE)
    c10_t4_total = c10r1_t4 + c10r2_t4 + c10r3_t4 + c10r4_t4 + c10r5_t4

    c10r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].LEISURE)
    c10r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].LEISURE)
    c10r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].LEISURE)
    c10r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].LEISURE)
    c10r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].LEISURE)
    c10r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].LEISURE)
    c10_t5_total = c10r1_t5 + c10r2_t5 + c10r3_t5 + c10r4_t5 + \
        c10r5_t5 + c10r6_t5

    # Column 11: NON_BENEFICIAL

    c11r1_t1 = float(df_Pr.loc[df_Pr.CLASS == "Forest"].NON_BENEFICIAL)
    c11r2_t1 = float(df_Pr.loc[df_Pr.CLASS == "Shrubland"].NON_BENEFICIAL)
    c11r3_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural grasslands"].NON_BENEFICIAL)
    c11r4_t1 = float(df_Pr.loc[df_Pr.CLASS == "Natural water bodies"].NON_BENEFICIAL)
    c11r5_t1 = float(df_Pr.loc[df_Pr.CLASS == "Wetlands"].NON_BENEFICIAL)
    c11r6_t1 = float(df_Pr.loc[df_Pr.CLASS == "Glaciers"].NON_BENEFICIAL)
    c11r7_t1 = float(df_Pr.loc[df_Pr.CLASS == "Others"].NON_BENEFICIAL)
    c11_t1_total = c11r1_t1 + c11r2_t1 + c11r3_t1 + c11r4_t1 + c11r5_t1 + \
        c11r6_t1 + c11r7_t1

    c11r1_t2 = float(df_Ut.loc[df_Ut.CLASS == "Forest"].NON_BENEFICIAL)
    c11r2_t2 = float(df_Ut.loc[df_Ut.CLASS == "Shrubland"].NON_BENEFICIAL)
    c11r3_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural grasslands"].NON_BENEFICIAL)
    c11r4_t2 = float(df_Ut.loc[df_Ut.CLASS == "Natural water bodies"].NON_BENEFICIAL)
    c11r5_t2 = float(df_Ut.loc[df_Ut.CLASS == "Wetlands"].NON_BENEFICIAL)
    c11r6_t2 = float(df_Ut.loc[df_Ut.CLASS == "Others"].NON_BENEFICIAL)
    c11_t2_total = c11r1_t2 + c11r2_t2 + c11r3_t2 + c11r4_t2 + \
        c11r5_t2 + c11r6_t2

    c11r1_t3 = float(df_Mo.loc[df_Mo.CLASS == "Rainfed crops"].NON_BENEFICIAL)
    c11r2_t3 = float(df_Mo.loc[df_Mo.CLASS == "Forest plantations"].NON_BENEFICIAL)
    c11r3_t3 = float(df_Mo.loc[df_Mo.CLASS == "Settlements"].NON_BENEFICIAL)
    c11r4_t3 = float(df_Mo.loc[df_Mo.CLASS == "Others"].NON_BENEFICIAL)
    c11_t3_total = c11r1_t3 + c11r2_t3 + c11r3_t3 + c11r4_t3

    c11r1_t4 = float(df_Mc.loc[df_Mc.CLASS == "Irrigated crops"].NON_BENEFICIAL)
    c11r2_t4 = float(df_Mc.loc[df_Mc.CLASS == "Managed water bodies"].NON_BENEFICIAL)
    c11r3_t4 = float(df_Mc.loc[df_Mc.CLASS == "Residential"].NON_BENEFICIAL)
    c11r4_t4 = float(df_Mc.loc[df_Mc.CLASS == "Industry"].NON_BENEFICIAL)
    c11r5_t4 = float(df_Mc.loc[df_Mc.CLASS == "Others"].NON_BENEFICIAL)
    c11_t4_total = c11r1_t4 + c11r2_t4 + c11r3_t4 + c11r4_t4 + c11r5_t4

    c11r1_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor domestic"].NON_BENEFICIAL)
    c11r2_t5 = float(df_Mn.loc[df_Mn.CLASS == "Indoor industry"].NON_BENEFICIAL)
    c11r3_t5 = float(df_Mn.loc[df_Mn.CLASS == "Greenhouses"].NON_BENEFICIAL)
    c11r4_t5 = float(df_Mn.loc[df_Mn.CLASS == "Livestock and husbandry"].NON_BENEFICIAL)
    c11r5_t5 = float(df_Mn.loc[df_Mn.CLASS == "Power and energy"].NON_BENEFICIAL)
    c11r6_t5 = float(df_Mn.loc[df_Mn.CLASS == "Others"].NON_BENEFICIAL)
    c11_t5_total = c11r1_t5 + c11r2_t5 + c11r3_t5 + c11r4_t5 + \
        c11r5_t5 + c11r6_t5

    # Check if left and right side agree

    # Table 1
    r1_t1_bene = c6r1_t1 + c7r1_t1 + c8r1_t1 + c9r1_t1 + c10r1_t1
    r2_t1_bene = c6r2_t1 + c7r2_t1 + c8r2_t1 + c9r2_t1 + c10r2_t1
    r3_t1_bene = c6r3_t1 + c7r3_t1 + c8r3_t1 + c9r3_t1 + c10r3_t1
    r4_t1_bene = c6r4_t1 + c7r4_t1 + c8r4_t1 + c9r4_t1 + c10r4_t1
    r5_t1_bene = c6r5_t1 + c7r5_t1 + c8r5_t1 + c9r5_t1 + c10r5_t1
    r6_t1_bene = c6r6_t1 + c7r6_t1 + c8r6_t1 + c9r6_t1 + c10r6_t1
    r7_t1_bene = c6r7_t1 + c7r7_t1 + c8r7_t1 + c9r7_t1 + c10r7_t1

    c5r1_t1_left = c1r1_t1 + c2r1_t1 + c3r1_t1 + c4r1_t1
    c5r2_t1_left = c1r2_t1 + c2r2_t1 + c3r2_t1 + c4r2_t1
    c5r3_t1_left = c1r3_t1 + c2r3_t1 + c3r3_t1 + c4r3_t1
    c5r4_t1_left = c1r4_t1 + c2r4_t1 + c3r4_t1 + c4r4_t1
    c5r5_t1_left = c1r5_t1 + c2r5_t1 + c3r5_t1 + c4r5_t1
    c5r6_t1_left = c1r6_t1 + c2r6_t1 + c3r6_t1 + c4r6_t1
    c5r7_t1_left = c1r7_t1 + c2r7_t1 + c3r7_t1 + c4r7_t1

    c5r1_t1_right = r1_t1_bene + c11r1_t1
    c5r2_t1_right = r2_t1_bene + c11r2_t1
    c5r3_t1_right = r3_t1_bene + c11r3_t1
    c5r4_t1_right = r4_t1_bene + c11r4_t1
    c5r5_t1_right = r5_t1_bene + c11r5_t1
    c5r6_t1_right = r6_t1_bene + c11r6_t1
    c5r7_t1_right = r7_t1_bene + c11r7_t1

    # Table 2
    r1_t2_bene = c6r1_t2 + c7r1_t2 + c8r1_t2 + c9r1_t2 + c10r1_t2
    r2_t2_bene = c6r2_t2 + c7r2_t2 + c8r2_t2 + c9r2_t2 + c10r2_t2
    r3_t2_bene = c6r3_t2 + c7r3_t2 + c8r3_t2 + c9r3_t2 + c10r3_t2
    r4_t2_bene = c6r4_t2 + c7r4_t2 + c8r4_t2 + c9r4_t2 + c10r4_t2
    r5_t2_bene = c6r5_t2 + c7r5_t2 + c8r5_t2 + c9r5_t2 + c10r5_t2
    r6_t2_bene = c6r6_t2 + c7r6_t2 + c8r6_t2 + c9r6_t2 + c10r6_t2

    c5r1_t2_left = c1r1_t2 + c2r1_t2 + c3r1_t2 + c4r1_t2
    c5r2_t2_left = c1r2_t2 + c2r2_t2 + c3r2_t2 + c4r2_t2
    c5r3_t2_left = c1r3_t2 + c2r3_t2 + c3r3_t2 + c4r3_t2
    c5r4_t2_left = c1r4_t2 + c2r4_t2 + c3r4_t2 + c4r4_t2
    c5r5_t2_left = c1r5_t2 + c2r5_t2 + c3r5_t2 + c4r5_t2
    c5r6_t2_left = c1r6_t2 + c2r6_t2 + c3r6_t2 + c4r6_t2

    c5r1_t2_right = r1_t2_bene + c11r1_t2
    c5r2_t2_right = r2_t2_bene + c11r2_t2
    c5r3_t2_right = r3_t2_bene + c11r3_t2
    c5r4_t2_right = r4_t2_bene + c11r4_t2
    c5r5_t2_right = r5_t2_bene + c11r5_t2
    c5r6_t2_right = r6_t2_bene + c11r6_t2

    # Table 3
    r1_t3_bene = c6r1_t3 + c7r1_t3 + c8r1_t3 + c9r1_t3 + c10r1_t3
    r2_t3_bene = c6r2_t3 + c7r2_t3 + c8r2_t3 + c9r2_t3 + c10r2_t3
    r3_t3_bene = c6r3_t3 + c7r3_t3 + c8r3_t3 + c9r3_t3 + c10r3_t3
    r4_t3_bene = c6r4_t3 + c7r4_t3 + c8r4_t3 + c9r4_t3 + c10r4_t3

    c5r1_t3_left = c1r1_t3 + c2r1_t3 + c3r1_t3 + c4r1_t3
    c5r2_t3_left = c1r2_t3 + c2r2_t3 + c3r2_t3 + c4r2_t3
    c5r3_t3_left = c1r3_t3 + c2r3_t3 + c3r3_t3 + c4r3_t3
    c5r4_t3_left = c1r4_t3 + c2r4_t3 + c3r4_t3 + c4r4_t3

    c5r1_t3_right = r1_t3_bene + c11r1_t3
    c5r2_t3_right = r2_t3_bene + c11r2_t3
    c5r3_t3_right = r3_t3_bene + c11r3_t3
    c5r4_t3_right = r4_t3_bene + c11r4_t3

    # Table 4
    r1_t4_bene = c6r1_t4 + c7r1_t4 + c8r1_t4 + c9r1_t4 + c10r1_t4
    r2_t4_bene = c6r2_t4 + c7r2_t4 + c8r2_t4 + c9r2_t4 + c10r2_t4
    r3_t4_bene = c6r3_t4 + c7r3_t4 + c8r3_t4 + c9r3_t4 + c10r3_t4
    r4_t4_bene = c6r4_t4 + c7r4_t4 + c8r4_t4 + c9r4_t4 + c10r4_t4
    r5_t4_bene = c6r5_t4 + c7r5_t4 + c8r5_t4 + c9r5_t4 + c10r5_t4

    c5r1_t4_left = c1r1_t4 + c2r1_t4 + c3r1_t4 + c4r1_t4
    c5r2_t4_left = c1r2_t4 + c2r2_t4 + c3r2_t4 + c4r2_t4
    c5r3_t4_left = c1r3_t4 + c2r3_t4 + c3r3_t4 + c4r3_t4
    c5r4_t4_left = c1r4_t4 + c2r4_t4 + c3r4_t4 + c4r4_t4
    c5r5_t4_left = c1r5_t4 + c2r5_t4 + c3r5_t4 + c4r5_t4

    c5r1_t4_right = r1_t4_bene + c11r1_t4
    c5r2_t4_right = r2_t4_bene + c11r2_t4
    c5r3_t4_right = r3_t4_bene + c11r3_t4
    c5r4_t4_right = r4_t4_bene + c11r4_t4
    c5r5_t4_right = r5_t4_bene + c11r5_t4

    # Table 5
    r1_t5_bene = c6r1_t5 + c7r1_t5 + c8r1_t5 + c9r1_t5 + c10r1_t5
    r2_t5_bene = c6r2_t5 + c7r2_t5 + c8r2_t5 + c9r2_t5 + c10r2_t5
    r3_t5_bene = c6r3_t5 + c7r3_t5 + c8r3_t5 + c9r3_t5 + c10r3_t5
    r4_t5_bene = c6r4_t5 + c7r4_t5 + c8r4_t5 + c9r4_t5 + c10r4_t5
    r5_t5_bene = c6r5_t5 + c7r5_t5 + c8r5_t5 + c9r5_t5 + c10r5_t5
    r6_t5_bene = c6r6_t5 + c7r6_t5 + c8r6_t5 + c9r6_t5 + c10r6_t5

    c5r1_t5_left = c1r1_t5 + c2r1_t5 + c3r1_t5 + c4r1_t5
    c5r2_t5_left = c1r2_t5 + c2r2_t5 + c3r2_t5 + c4r2_t5
    c5r3_t5_left = c1r3_t5 + c2r3_t5 + c3r3_t5 + c4r3_t5
    c5r4_t5_left = c1r4_t5 + c2r4_t5 + c3r4_t5 + c4r4_t5
    c5r5_t5_left = c1r5_t5 + c2r5_t5 + c3r5_t5 + c4r5_t5
    c5r6_t5_left = c1r6_t5 + c2r6_t5 + c3r6_t5 + c4r6_t5

    c5r1_t5_right = r1_t5_bene + c11r1_t5
    c5r2_t5_right = r2_t5_bene + c11r2_t5
    c5r3_t5_right = r3_t5_bene + c11r3_t5
    c5r4_t5_right = r4_t5_bene + c11r4_t5
    c5r5_t5_right = r5_t5_bene + c11r5_t5
    c5r6_t5_right = r6_t5_bene + c11r6_t5

    # t1
    if abs(c5r1_t1_left - c5r1_t1_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('PROTECTED', 'Forest'))
    elif abs(c5r2_t1_left - c5r2_t1_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('PROTECTED', 'Shrubland'))
    elif abs(c5r3_t1_left - c5r3_t1_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('PROTECTED',
                                               'Natural grasslands'))
    elif abs(c5r4_t1_left - c5r4_t1_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('PROTECTED',
                                               'Natural water bodies'))
    elif abs(c5r5_t1_left - c5r5_t1_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('PROTECTED', 'Wetlands'))
    elif abs(c5r6_t1_left - c5r6_t1_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('PROTECTED', 'Glaciers'))
    elif abs(c5r7_t1_left - c5r7_t1_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('PROTECTED', 'Others'))

    # t2
    elif abs(c5r1_t2_left - c5r1_t2_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('UTILIZED', 'Forest'))
    elif abs(c5r2_t2_left - c5r2_t2_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('UTILIZED', 'Shrubland'))
    elif abs(c5r3_t2_left - c5r3_t2_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('UTILIZED',
                                               'Natural grasslands'))
    elif abs(c5r4_t2_left - c5r4_t2_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('UTILIZED',
                                               'Natural water bodies'))
    elif abs(c5r5_t2_left - c5r5_t2_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('UTILIZED', 'Wetlands'))
    elif abs(c5r6_t2_left - c5r6_t2_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('UTILIZED', 'Others'))

    # t3
    elif abs(c5r1_t3_left - c5r1_t3_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MODIFIED', 'Rainfed crops'))
    elif abs(c5r2_t3_left - c5r2_t3_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MODIFIED',
                                               'Forest plantations'))
    elif abs(c5r3_t3_left - c5r3_t3_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MODIFIED', 'Settlements'))
    elif abs(c5r4_t3_left - c5r4_t3_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MODIFIED', 'Others'))

    # t4
    elif abs(c5r1_t4_left - c5r1_t4_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED CONVENTIONAL',
                                               'Irrigated crops'))
    elif abs(c5r2_t4_left - c5r2_t4_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED CONVENTIONAL',
                                               'Managed water bodies'))
    elif abs(c5r3_t4_left - c5r3_t4_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED CONVENTIONAL',
                                               'Residential'))
    elif abs(c5r4_t4_left - c5r4_t4_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED CONVENTIONAL',
                                               'Industry'))
    elif abs(c5r5_t4_left - c5r5_t4_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED CONVENTIONAL',
                                               'Others'))

    # t5
    elif abs(c5r1_t5_left - c5r1_t5_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED NON_CONVENTIONAL',
                                               'Indoor domestic'))
    elif abs(c5r2_t5_left - c5r2_t5_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED NON_CONVENTIONAL',
                                               'Indoor industrial'))
    elif abs(c5r3_t5_left - c5r3_t5_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED NON_CONVENTIONAL',
                                               'Greenhouses'))
    elif abs(c5r4_t5_left - c5r4_t5_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED NON_CONVENTIONAL',
                                               'Livestock and husbandry'))
    elif abs(c5r5_t5_left - c5r5_t5_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED NON_CONVENTIONAL',
                                               'Power and energy'))
    elif abs(c5r6_t5_left - c5r6_t5_right) > tolerance:
        raise ValueError('The left and rigth sides \
                          do not add up ({0} table \
                          and {1} row)'.format('MANAGED NON_CONVENTIONAL',
                                               'Others'))

    # Calculations & modify svg
    if not template:
        svg_template_path = get_template('sheet_2',
                                         template_folder='Default')
    else:
        svg_template_path = os.path.abspath(template)

    tree = ET.parse(svg_template_path)

    # Titles

    xml_txt_box = tree.findall('''.//*[@id='basin']''')[0]
    xml_txt_box.getchildren()[0].text = 'Basin: ' + basin

    xml_txt_box = tree.findall('''.//*[@id='period']''')[0]
    xml_txt_box.getchildren()[0].text = 'Period: ' + period

    xml_txt_box = tree.findall('''.//*[@id='units']''')[0]
    
    
    if np.all([smart_unit, scale > 0]):
        xml_txt_box.getchildren()[0].text = 'Sheet 2: Evapotranspiration ({0} {1})'.format(10**-scale, units)
    else:
        xml_txt_box.getchildren()[0].text = 'Sheet 2: Evapotranspiration ({0})'.format(units)

    # Total ET
    total_et_t1 = c5r1_t1_left + c5r2_t1_left + c5r3_t1_left + c5r4_t1_left + \
        c5r5_t1_left + c5r6_t1_left + c5r7_t1_left
    total_et_t2 = c5r1_t2_left + c5r2_t2_left + c5r3_t2_left + c5r4_t2_left + \
        c5r5_t2_left + c5r6_t2_left
    total_et_t3 = c5r1_t3_left + c5r2_t3_left + c5r3_t3_left + c5r4_t3_left
    total_et_t4 = c5r1_t4_left + c5r2_t4_left + c5r3_t4_left + c5r4_t4_left + \
        c5r5_t4_left
    total_et_t5 = c5r1_t5_left + c5r2_t5_left + c5r3_t5_left + c5r4_t5_left + \
        c5r5_t5_left + c5r6_t5_left

    total_et = total_et_t1 + total_et_t2 + total_et_t3 + \
        total_et_t4 + total_et_t5
        
    

    et_total_managed_lu = total_et_t4 + total_et_t5
    et_total_managed = total_et_t3 + et_total_managed_lu

    t_total_managed_lu = c1_t4_total + c1_t5_total

    xml_txt_box = tree.findall('''.//*[@id='total_et']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_et

    xml_txt_box = tree.findall('''.//*[@id='non-manageble']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_et_t1

    xml_txt_box = tree.findall('''.//*[@id='manageble']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_et_t2

    xml_txt_box = tree.findall('''.//*[@id='managed']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % et_total_managed

    # Totals land use

    xml_txt_box = tree.findall('''.//*[@id='protected_lu_et']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_et_t1

    xml_txt_box = tree.findall('''.//*[@id='protected_lu_t']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1_t1_total

    xml_txt_box = tree.findall('''.//*[@id='utilized_lu_et']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_et_t2

    xml_txt_box = tree.findall('''.//*[@id='utilized_lu_t']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1_t2_total

    xml_txt_box = tree.findall('''.//*[@id='modified_lu_et']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_et_t3

    xml_txt_box = tree.findall('''.//*[@id='modified_lu_t']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1_t3_total

    xml_txt_box = tree.findall('''.//*[@id='managed_lu_et']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % et_total_managed_lu

    xml_txt_box = tree.findall('''.//*[@id='managed_lu_t']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % t_total_managed_lu

    # Table 1
    xml_txt_box = tree.findall('''.//*[@id='plu_et_forest']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r1_t1_left

    xml_txt_box = tree.findall('''.//*[@id='plu_t_forest']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r1_t1

    xml_txt_box = tree.findall('''.//*[@id='plu_et_shrubland']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r2_t1_left

    xml_txt_box = tree.findall('''.//*[@id='plu_t_shrubland']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r2_t1

    xml_txt_box = tree.findall('''.//*[@id='plu_et_grasslands']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r3_t1_left

    xml_txt_box = tree.findall('''.//*[@id='plu_t_grasslands']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r3_t1

    xml_txt_box = tree.findall('''.//*[@id='plu_et_waterbodies']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r4_t1_left

    xml_txt_box = tree.findall('''.//*[@id='plu_t_waterbodies']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r4_t1

    xml_txt_box = tree.findall('''.//*[@id='plu_et_wetlands']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r5_t1_left

    xml_txt_box = tree.findall('''.//*[@id='plu_t_wetlands']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r5_t1

    xml_txt_box = tree.findall('''.//*[@id='plu_et_glaciers']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r6_t1_left

    xml_txt_box = tree.findall('''.//*[@id='plu_t_glaciers']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r6_t1

    xml_txt_box = tree.findall('''.//*[@id='plu_et_others']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r7_t1_left

    xml_txt_box = tree.findall('''.//*[@id='plu_t_others']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r7_t1

    # Table 2
    xml_txt_box = tree.findall('''.//*[@id='ulu_et_forest']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r1_t2_left

    xml_txt_box = tree.findall('''.//*[@id='ulu_t_forest']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r1_t2

    xml_txt_box = tree.findall('''.//*[@id='ulu_et_shrubland']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r2_t2_left

    xml_txt_box = tree.findall('''.//*[@id='ulu_t_shrubland']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r2_t2

    xml_txt_box = tree.findall('''.//*[@id='ulu_et_grasslands']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r3_t2_left

    xml_txt_box = tree.findall('''.//*[@id='ulu_t_grasslands']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r3_t2

    xml_txt_box = tree.findall('''.//*[@id='ulu_et_waterbodies']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r4_t2_left

    xml_txt_box = tree.findall('''.//*[@id='ulu_t_waterbodies']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r4_t2

    xml_txt_box = tree.findall('''.//*[@id='ulu_et_wetlands']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r5_t2_left

    xml_txt_box = tree.findall('''.//*[@id='ulu_t_wetlands']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r5_t2

    xml_txt_box = tree.findall('''.//*[@id='ulu_et_others']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r6_t2_left

    xml_txt_box = tree.findall('''.//*[@id='ulu_t_others']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r6_t2

    # Table 3
    xml_txt_box = tree.findall('''.//*[@id='molu_et_rainfed']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r1_t3_left

    xml_txt_box = tree.findall('''.//*[@id='molu_t_rainfed']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r1_t3

    xml_txt_box = tree.findall('''.//*[@id='molu_et_forest']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r2_t3_left

    xml_txt_box = tree.findall('''.//*[@id='molu_t_forest']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r2_t3

    xml_txt_box = tree.findall('''.//*[@id='molu_et_settlements']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r3_t3_left

    xml_txt_box = tree.findall('''.//*[@id='molu_t_settlements']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r3_t3

    xml_txt_box = tree.findall('''.//*[@id='molu_et_others']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r4_t3_left

    xml_txt_box = tree.findall('''.//*[@id='molu_t_others']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r4_t3

    # Table 4
    xml_txt_box = tree.findall('''.//*[@id='malu_et_crops']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r1_t4_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_crops']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r1_t4

    xml_txt_box = tree.findall('''.//*[@id='malu_et_waterbodies']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r2_t4_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_waterbodies']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r2_t4

    xml_txt_box = tree.findall('''.//*[@id='malu_et_residential']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r3_t4_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_residential']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r3_t4

    xml_txt_box = tree.findall('''.//*[@id='malu_et_industry']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r4_t4_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_industry']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r4_t4

    xml_txt_box = tree.findall('''.//*[@id='malu_et_others1']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r5_t4_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_others1']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r5_t4

    # Table 5
    xml_txt_box = tree.findall('''.//*[@id='malu_et_idomestic']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r1_t5_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_idomestic']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r1_t5

    xml_txt_box = tree.findall('''.//*[@id='malu_et_iindustry']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r2_t5_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_iindustry']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r2_t5

    xml_txt_box = tree.findall('''.//*[@id='malu_et_greenhouses']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r3_t5_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_greenhouses']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r3_t5

    xml_txt_box = tree.findall('''.//*[@id='malu_et_livestock']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r4_t5_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_livestock']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r4_t5

    xml_txt_box = tree.findall('''.//*[@id='malu_et_powerandenergy']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r5_t5_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_powerandenergy']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r5_t5

    xml_txt_box = tree.findall('''.//*[@id='malu_et_others2']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c5r6_t5_left

    xml_txt_box = tree.findall('''.//*[@id='malu_t_others2']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % c1r6_t5

    # Right box
    total_t = c1_t1_total + c1_t2_total + c1_t3_total + \
        c1_t4_total + c1_t5_total
    total_e = total_et - total_t

    total_water = c2_t1_total + c2_t2_total + c2_t3_total + \
        c2_t4_total + c2_t5_total
    total_soil = c3_t1_total + c3_t2_total + c3_t3_total + \
        c3_t4_total + c3_t5_total
    total_interception = c4_t1_total + c4_t2_total + c4_t3_total + \
        c4_t4_total + c4_t5_total

    xml_txt_box = tree.findall('''.//*[@id='evaporation']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_e

    xml_txt_box = tree.findall('''.//*[@id='transpiration']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_t

    xml_txt_box = tree.findall('''.//*[@id='water']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_water

    xml_txt_box = tree.findall('''.//*[@id='soil']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_soil

    xml_txt_box = tree.findall('''.//*[@id='interception']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_interception

    total_agr = c6_t1_total + c6_t2_total + c6_t3_total + \
        c6_t4_total + c6_t5_total
    total_env = c7_t1_total + c7_t2_total + c7_t3_total + \
        c7_t4_total + c7_t5_total
    total_eco = c8_t1_total + c8_t2_total + c8_t3_total + \
        c8_t4_total + c8_t5_total
    total_ene = c9_t1_total + c9_t2_total + c9_t3_total + \
        c9_t4_total + c9_t5_total
    total_lei = c10_t1_total + c10_t2_total + c10_t3_total + \
        c10_t4_total + c10_t5_total

    total_bene = total_agr + total_env + total_eco + total_ene + total_lei
    total_non_bene = c11_t1_total + c11_t2_total + c11_t3_total + \
        c11_t4_total + c11_t5_total

    xml_txt_box = tree.findall('''.//*[@id='non-beneficial']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_non_bene

    xml_txt_box = tree.findall('''.//*[@id='beneficial']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_bene

    xml_txt_box = tree.findall('''.//*[@id='agriculture']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_agr

    xml_txt_box = tree.findall('''.//*[@id='environment']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_env

    xml_txt_box = tree.findall('''.//*[@id='economy']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_eco

    xml_txt_box = tree.findall('''.//*[@id='energy']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_ene

    xml_txt_box = tree.findall('''.//*[@id='leisure']''')[0]
    xml_txt_box.getchildren()[0].text = '%.1f' % total_lei

    # Export svg to png
    tempout_path = output.replace('.pdf', '_temporary.svg')
    tree.write(tempout_path)    
    cairosvg.svg2pdf(url=tempout_path, write_to=output)    
    os.remove(tempout_path)


    # Return
    return output

def print_sheet3(basin, period, units, data, output, template=False):
    '''
    print sheet 3 png
    '''
    # Read table
    df = pd.read_csv(data, sep=';')
    # Read csv file part 1
    crop_r01c01 = np.nansum([float(df.loc[(df.SEASON == "Kharif") &
                        (df.TYPE == "RAIN")].ET_RAINFALL),
                    float(df.loc[(df.SEASON == "Kharif") &
                        (df.TYPE == "RAIN")].ET_INCREMENTAL)])
    crop_r01c02 = np.nansum([float(df.loc[(df.SEASON == "Rabi") &
                        (df.TYPE == "RAIN")].ET_RAINFALL),
                    float(df.loc[(df.SEASON == "Rabi") &
                        (df.TYPE == "RAIN")].ET_INCREMENTAL)])
    crop_r01c03 = np.nansum([float(df.loc[(df.SEASON == "Zaid") &
                        (df.TYPE == "RAIN")].ET_RAINFALL),
                    float(df.loc[(df.SEASON == "Zaid") &
                        (df.TYPE == "RAIN")].ET_INCREMENTAL)])
    crop_r01c04 = np.nansum([float(df.loc[(df.SEASON == "Double/Triple Crop") &
                        (df.TYPE == "RAIN")].ET_RAINFALL),
                    float(df.loc[(df.SEASON == "Double/Triple Crop") &
                        (df.TYPE == "RAIN")].ET_INCREMENTAL)])
    crop_r01c05 = np.nansum([float(df.loc[(df.SEASON == "Forest plantation") &
                        (df.TYPE == "RAIN")].ET_RAINFALL),
                    float(df.loc[(df.SEASON == "Forest plantation") &
                        (df.TYPE == "RAIN")].ET_INCREMENTAL)])
    crop_r01 = np.nansum([crop_r01c01,crop_r01c02,
                         crop_r01c03,crop_r01c04,crop_r01c05])
    
    crop_r02c01=float(df.loc[(df.SEASON == "Kharif") &
                        (df.TYPE == "IRRI")].ET_RAINFALL)
    crop_r02c02=float(df.loc[(df.SEASON == "Rabi") &
                        (df.TYPE == "IRRI")].ET_RAINFALL)
    crop_r02c03=float(df.loc[(df.SEASON == "Zaid") &
                        (df.TYPE == "IRRI")].ET_RAINFALL)
    crop_r02c04=float(df.loc[(df.SEASON == "Double/Triple Crop") &
                        (df.TYPE == "IRRI")].ET_RAINFALL)
    crop_r02c05=float(df.loc[(df.SEASON == "Forest plantation") &
                        (df.TYPE == "IRRI")].ET_RAINFALL)
    crop_r02=np.nansum([crop_r02c01,crop_r02c02,
                       crop_r02c03,crop_r02c04,crop_r02c05])
    
    crop_r03c01=float(df.loc[(df.SEASON == "Kharif") &
                        (df.TYPE == "IRRI")].ET_INCREMENTAL)
    crop_r03c02=float(df.loc[(df.SEASON == "Rabi") &
                        (df.TYPE == "IRRI")].ET_INCREMENTAL)
    crop_r03c03=float(df.loc[(df.SEASON == "Zaid") &
                        (df.TYPE == "IRRI")].ET_INCREMENTAL)
    crop_r03c04=float(df.loc[(df.SEASON == "Double/Triple Crop") &
                        (df.TYPE == "IRRI")].ET_INCREMENTAL)
    crop_r03c05=float(df.loc[(df.SEASON == "Forest plantation") &
                        (df.TYPE == "IRRI")].ET_INCREMENTAL)
    crop_r03=np.nansum([crop_r03c01,crop_r03c02,
                        crop_r03c03,crop_r03c04,crop_r03c05])
    
    crop_r04c01=crop_r02c01+crop_r03c01
    crop_r04c02=crop_r02c02+crop_r03c02
    crop_r04c03=crop_r02c03+crop_r03c03
    crop_r04c04=crop_r02c04+crop_r03c04
    crop_r04c05=crop_r02c05+crop_r03c05
    crop_r04=crop_r02+crop_r03
    
    ag_water_cons=crop_r04+crop_r01
    # Read csv file part 2
    lp_r01c01=float(df.loc[(df.SEASON == "Kharif") &
                        (df.TYPE == "RAIN")].LAND_PRODUCTIVITY)
    lp_r01c02=float(df.loc[(df.SEASON == "Rabi") &
                        (df.TYPE == "RAIN")].LAND_PRODUCTIVITY)
    lp_r01c03=float(df.loc[(df.SEASON == "Zaid") &
                        (df.TYPE == "RAIN")].LAND_PRODUCTIVITY)
    lp_r01c04=float(df.loc[(df.SEASON == "Double/Triple Crop") &
                        (df.TYPE == "RAIN")].LAND_PRODUCTIVITY)
    lp_r01c05=float(df.loc[(df.SEASON == "Forest plantation") &
                        (df.TYPE == "RAIN")].LAND_PRODUCTIVITY)
    
    lp_r02c01=float(df.loc[(df.SEASON == "Kharif") &
                        (df.TYPE == "IRRI")].LAND_PRODUCTIVITY)
    lp_r02c02=float(df.loc[(df.SEASON == "Rabi") &
                        (df.TYPE == "IRRI")].LAND_PRODUCTIVITY)
    lp_r02c03=float(df.loc[(df.SEASON == "Zaid") &
                        (df.TYPE == "IRRI")].LAND_PRODUCTIVITY)
    lp_r02c04=float(df.loc[(df.SEASON == "Double/Triple Crop") &
                        (df.TYPE == "IRRI")].LAND_PRODUCTIVITY)
    lp_r02c05=float(df.loc[(df.SEASON == "Forest plantation") &
                        (df.TYPE == "IRRI")].LAND_PRODUCTIVITY)
    
    wp_r01c01=float(df.loc[(df.SEASON == "Kharif") &
                        (df.TYPE == "RAIN")].WATER_PRODUCTIVITY)
    wp_r01c02=float(df.loc[(df.SEASON == "Rabi") &
                        (df.TYPE == "RAIN")].WATER_PRODUCTIVITY)
    wp_r01c03=float(df.loc[(df.SEASON == "Zaid") &
                        (df.TYPE == "RAIN")].WATER_PRODUCTIVITY)
    wp_r01c04=float(df.loc[(df.SEASON == "Double/Triple Crop") &
                        (df.TYPE == "RAIN")].WATER_PRODUCTIVITY)
    wp_r01c05=float(df.loc[(df.SEASON == "Forest plantation") &
                        (df.TYPE == "RAIN")].WATER_PRODUCTIVITY)
    
    wp_r02c01=float(df.loc[(df.SEASON == "Kharif") &
                        (df.TYPE == "IRRI")].WATER_PRODUCTIVITY)
    wp_r02c02=float(df.loc[(df.SEASON == "Rabi") &
                        (df.TYPE == "IRRI")].WATER_PRODUCTIVITY)
    wp_r02c03=float(df.loc[(df.SEASON == "Zaid") &
                        (df.TYPE == "IRRI")].WATER_PRODUCTIVITY)
    wp_r02c04=float(df.loc[(df.SEASON == "Double/Triple Crop") &
                        (df.TYPE == "IRRI")].WATER_PRODUCTIVITY)
    wp_r02c05=float(df.loc[(df.SEASON == "Forest plantation") &
                        (df.TYPE == "IRRI")].WATER_PRODUCTIVITY)
    # Calculations & modify svgs
    if not template:
        svg_template = get_template('sheet_3',
                                         template_folder='Default')
    else:
        svg_template = os.path.abspath(template)
    tree = ET.parse(svg_template)

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Titles

    xml_txt_box = tree.findall('''.//*[@id='basin']''')[0]
    xml_txt_box.getchildren()[0].text = 'Basin: ' + basin

    xml_txt_box = tree.findall('''.//*[@id='period']''')[0]
    xml_txt_box.getchildren()[0].text = 'Period: ' + period

    xml_txt_box = tree.findall('''.//*[@id='units']''')[0]
    xml_txt_box.getchildren()[0].text = 'Part 1: Agricultural water consumption (' + units[0] + ')'

    xml_txt_box = tree.findall('''.//*[@id='units2']''')[0]
    xml_txt_box.getchildren()[0].text = 'Part 2: Land productivity (' + units[1] + ') and water productivity (' + units[2] + ')'

    ### Part 1
    ## row 1
    xml_txt_box = tree.findall('''.//*[@id='crop_r01c01']''')[0]
    if not pd.isnull(crop_r01c01):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r01c01
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r01c02']''')[0]
    if not pd.isnull(crop_r01c02):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r01c02
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r01c03']''')[0]
    if not pd.isnull(crop_r01c03):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r01c03
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r01c04']''')[0]
    if not pd.isnull(crop_r01c04):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r01c04
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r01c05']''')[0]
    if not pd.isnull(crop_r01c05):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r01c05
    else:
        xml_txt_box.getchildren()[0].text = '-'
    
    xml_txt_box = tree.findall('''.//*[@id='crop_r01']''')[0]
    if not pd.isnull(crop_r01):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r01
    else:
        xml_txt_box.getchildren()[0].text = '-'
    ## row 2
    xml_txt_box = tree.findall('''.//*[@id='crop_r02c01']''')[0]
    if not pd.isnull(crop_r02c01):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r02c01
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r02c02']''')[0]
    if not pd.isnull(crop_r02c02):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r02c02
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r02c03']''')[0]
    if not pd.isnull(crop_r02c03):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r02c03
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r02c04']''')[0]
    if not pd.isnull(crop_r02c04):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r02c04
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r02c05']''')[0]
    if not pd.isnull(crop_r02c05):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r02c05
    else:
        xml_txt_box.getchildren()[0].text = '-'
        
    xml_txt_box = tree.findall('''.//*[@id='crop_r02']''')[0]
    if not pd.isnull(crop_r02):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r02
    else:
        xml_txt_box.getchildren()[0].text = '-'
    ## row 3
    xml_txt_box = tree.findall('''.//*[@id='crop_r03c01']''')[0]
    if not pd.isnull(crop_r03c01):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r03c01
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r03c02']''')[0]
    if not pd.isnull(crop_r03c02):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r03c02
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r03c03']''')[0]
    if not pd.isnull(crop_r03c03):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r03c03
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r03c04']''')[0]
    if not pd.isnull(crop_r03c04):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r03c04
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r03c05']''')[0]
    if not pd.isnull(crop_r03c05):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r03c05
    else:
        xml_txt_box.getchildren()[0].text = '-'

    xml_txt_box = tree.findall('''.//*[@id='crop_r03']''')[0]
    if not pd.isnull(crop_r03):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r03
    else:
        xml_txt_box.getchildren()[0].text = '-'
    ## row 4
    xml_txt_box = tree.findall('''.//*[@id='crop_r04c01']''')[0]
    if not pd.isnull(crop_r04c01):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r04c01
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r04c02']''')[0]
    if not pd.isnull(crop_r04c02):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r04c02
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r04c03']''')[0]
    if not pd.isnull(crop_r04c03):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r04c03
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r04c04']''')[0]
    if not pd.isnull(crop_r04c04):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r04c04
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='crop_r04c05']''')[0]
    if not pd.isnull(crop_r04c05):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r04c05
    else:
        xml_txt_box.getchildren()[0].text = '-'
    
    xml_txt_box = tree.findall('''.//*[@id='crop_r04']''')[0]
    if not pd.isnull(crop_r04):
        xml_txt_box.getchildren()[0].text = '%.2f' % crop_r04
    else:
        xml_txt_box.getchildren()[0].text = '-'
        
    xml_txt_box = tree.findall('''.//*[@id='ag_water_cons']''')[0]
    if not pd.isnull(ag_water_cons):
        xml_txt_box.getchildren()[0].text = '%.2f' % ag_water_cons
    else:
        xml_txt_box.getchildren()[0].text = '-'

    ### Part 2
    ## LP row 1
    xml_txt_box = tree.findall('''.//*[@id='lp_r01c01']''')[0]
    if not pd.isnull(lp_r01c01):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r01c01
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='lp_r01c02']''')[0]
    if not pd.isnull(lp_r01c02):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r01c02
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='lp_r01c03']''')[0]
    if not pd.isnull(lp_r01c03):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r01c03
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='lp_r01c04']''')[0]
    if not pd.isnull(lp_r01c04):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r01c04
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='lp_r01c05']''')[0]
    if not pd.isnull(lp_r01c05):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r01c05
    else:
        xml_txt_box.getchildren()[0].text = '-'
    ## LP row 2
    xml_txt_box = tree.findall('''.//*[@id='lp_r02c01']''')[0]
    if not pd.isnull(lp_r02c01):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r02c01
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='lp_r02c02']''')[0]
    if not pd.isnull(lp_r02c02):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r02c02
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='lp_r02c03']''')[0]
    if not pd.isnull(lp_r02c03):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r02c03
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='lp_r02c04']''')[0]
    if not pd.isnull(lp_r02c04):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r02c04
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='lp_r02c05']''')[0]
    if not pd.isnull(lp_r02c05):
        xml_txt_box.getchildren()[0].text = '%.0f' % lp_r02c05
    else:
        xml_txt_box.getchildren()[0].text = '-'
    ## WP row 1
    xml_txt_box = tree.findall('''.//*[@id='wp_r01c01']''')[0]
    if not pd.isnull(wp_r01c01):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r01c01
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='wp_r01c02']''')[0]
    if not pd.isnull(wp_r01c02):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r01c02
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='wp_r01c03']''')[0]
    if not pd.isnull(wp_r01c03):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r01c03
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='wp_r01c04']''')[0]
    if not pd.isnull(wp_r01c04):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r01c04
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='wp_r01c05']''')[0]
    if not pd.isnull(wp_r01c05):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r01c05
    else:
        xml_txt_box.getchildren()[0].text = '-'
    ## WP row 2
    xml_txt_box = tree.findall('''.//*[@id='wp_r02c01']''')[0]
    if not pd.isnull(wp_r02c01):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r02c01
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='wp_r02c02']''')[0]
    if not pd.isnull(wp_r02c02):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r02c02
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='wp_r02c03']''')[0]
    if not pd.isnull(wp_r02c03):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r02c03
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='wp_r02c04']''')[0]
    if not pd.isnull(wp_r02c04):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r02c04
    else:
        xml_txt_box.getchildren()[0].text = '-'
    xml_txt_box = tree.findall('''.//*[@id='wp_r02c05']''')[0]
    if not pd.isnull(wp_r02c05):
        xml_txt_box.getchildren()[0].text = '%.2f' % wp_r02c05
    else:
        xml_txt_box.getchildren()[0].text = '-'


    # Export svg to png
    tempout_path = output.replace('.pdf', '_temporary.svg')
    tree.write(tempout_path)    
    cairosvg.svg2pdf(url=tempout_path, write_to=output)    
#    os.remove(tempout_path)
    

    return output

def print_sheet4(basin, period, units, data, output, template=False, margin = 0.01, smart_unit = True):
    """
    Create sheet 4 of the Water Accounting Plus framework.
    
    Parameters
    ----------
    basin : str
        The name of the basin.
    period : str
        The period of analysis.
    units : list
        A list with strings of the units of the data on sheet 4a and 4b
        respectively.
    data : list
        List with two values pointing to csv files that contains the water data. The csv file has to
        follow an specific format. A sample csv is available here:
        https://github.com/wateraccounting/wa/tree/master/Sheets/csv
    output : list
        Filehandles pointing to the jpg files to be created.
    template : list or boolean, optional
        A list with two entries of the svg files of the sheet. False
        uses the standard svg files. Default is False.

    Examples
    --------
    >>> from wa.Sheets import *
    >>> create_sheet3(basin='Helmand', period='2007-2011',
                  units = ['km3/yr', 'km3/yr'],
                  data = [r'C:\Sheets\csv\Sample_sheet4_part1.csv',
                          r'C:\Sheets\csv\Sample_sheet4_part2.csv'],
                  output = [r'C:\Sheets\sheet_4_part1.jpg',
                            r'C:\Sheets\sheet_4_part2.jpg'])
    """
    if data[0] is not None:
        df1 = pd.read_csv(data[0], sep=';')
    if data[1] is not None:
        df2 = pd.read_csv(data[1], sep=';')
    
    scale = 0.
    if smart_unit:
        scale_test = pd.np.nanmax([
        
        pd.np.nansum([pd.np.nansum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].SUPPLY_GROUNDWATER)]),
                        pd.np.nansum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].SUPPLY_SURFACEWATER)])]),
        
        pd.np.nansum([pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].SUPPLY_GROUNDWATER)]),
                    pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].SUPPLY_SURFACEWATER)])])
        ])
        
        scale = scale_factor(scale_test)
        
        for df in [df1, df2]:
            for column in ['SUPPLY_GROUNDWATER', 'NON_RECOVERABLE_GROUNDWATER', 'SUPPLY_SURFACEWATER',
                           'NON_CONVENTIONAL_ET', 'RECOVERABLE_GROUNDWATER', 'CONSUMED_OTHER', 'CONSUMED_ET',
                           'DEMAND', 'RECOVERABLE_SURFACEWATER', 'NON_RECOVERABLE_SURFACEWATER']:
                
                df[column] *= 10**scale

    # Read csv part 1
    if data[0] is not None:
        p1 = dict()
        p1['sp_r01_c01'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].SUPPLY_SURFACEWATER),
                                   float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].SUPPLY_GROUNDWATER)])
        p1['sp_r02_c01'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].SUPPLY_SURFACEWATER),
                                   float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].SUPPLY_GROUNDWATER)])
        p1['sp_r03_c01'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].SUPPLY_SURFACEWATER),
                                   float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].SUPPLY_GROUNDWATER)])
        p1['sp_r04_c01'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].SUPPLY_SURFACEWATER),
                                   float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].SUPPLY_GROUNDWATER)])
        p1['sp_r05_c01'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].SUPPLY_SURFACEWATER),
                                   float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].SUPPLY_GROUNDWATER)])
        p1['sp_r06_c01'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].SUPPLY_SURFACEWATER),
                                   float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].SUPPLY_GROUNDWATER)])
        p1['sp_r07_c01'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].SUPPLY_SURFACEWATER),
                                   float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].SUPPLY_GROUNDWATER)])
        p1['sp_r08_c01'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Other")].SUPPLY_SURFACEWATER),
                                   float(df1.loc[(df1.LANDUSE_TYPE == "Other")].SUPPLY_GROUNDWATER)])
        
        p1['dm_r01_c01'] = float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].DEMAND)
        p1['dm_r02_c01'] = float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].DEMAND) 
        p1['dm_r03_c01'] = float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].DEMAND) 
        p1['dm_r04_c01'] = float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].DEMAND) 
        p1['dm_r05_c01'] = float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].DEMAND) 
        p1['dm_r06_c01'] = float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].DEMAND) 
        p1['dm_r07_c01'] = float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].DEMAND) 
        p1['dm_r08_c01'] = float(df1.loc[(df1.LANDUSE_TYPE == "Other")].DEMAND)
        
        p1['sp_r01_c02'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].CONSUMED_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].CONSUMED_OTHER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].NON_CONVENTIONAL_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].NON_RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].NON_RECOVERABLE_SURFACEWATER)])
        p1['sp_r02_c02'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].CONSUMED_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].CONSUMED_OTHER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].NON_CONVENTIONAL_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].NON_RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].NON_RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r03_c02'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].CONSUMED_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].CONSUMED_OTHER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].NON_CONVENTIONAL_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].NON_RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].NON_RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r04_c02'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].CONSUMED_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].CONSUMED_OTHER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].NON_CONVENTIONAL_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].NON_RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].NON_RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r05_c02'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].CONSUMED_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].CONSUMED_OTHER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].NON_CONVENTIONAL_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].NON_RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].NON_RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r06_c02'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].CONSUMED_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].CONSUMED_OTHER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].NON_CONVENTIONAL_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].NON_RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].NON_RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r07_c02'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].CONSUMED_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].CONSUMED_OTHER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].NON_CONVENTIONAL_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].NON_RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].NON_RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r08_c02'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Other")].CONSUMED_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Other")].CONSUMED_OTHER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Other")].NON_CONVENTIONAL_ET),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Other")].NON_RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Other")].NON_RECOVERABLE_SURFACEWATER)]) 
    
        p1['sp_r01_c03'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].RECOVERABLE_SURFACEWATER)])
        p1['sp_r02_c03'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r03_c03'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r04_c03'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r05_c03'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r06_c03'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r07_c03'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].RECOVERABLE_SURFACEWATER)]) 
        p1['sp_r08_c03'] = pd.np.sum([float(df1.loc[(df1.LANDUSE_TYPE == "Other")].RECOVERABLE_GROUNDWATER),
                                         float(df1.loc[(df1.LANDUSE_TYPE == "Other")].RECOVERABLE_SURFACEWATER)])
        
#        assert pd.np.any([np.isnan(p1['sp_r01_c01']), pd.np.all([p1['sp_r01_c01'] <= (1 + margin) * (p1['sp_r01_c02'] + p1['sp_r01_c03']), 
#                          p1['sp_r01_c01'] >= (1 - margin) * (p1['sp_r01_c02'] + p1['sp_r01_c03'])])])
#        assert pd.np.any([np.isnan(p1['sp_r02_c01']), pd.np.all([p1['sp_r02_c01'] <= (1 + margin) * (p1['sp_r02_c02'] + p1['sp_r02_c03']), 
#                          p1['sp_r02_c01'] >= (1 - margin) * (p1['sp_r02_c02'] + p1['sp_r02_c03'])])])
#        assert pd.np.any([np.isnan(p1['sp_r03_c01']), pd.np.all([p1['sp_r03_c01'] <= (1 + margin) * (p1['sp_r03_c02'] + p1['sp_r03_c03']), 
#                          p1['sp_r03_c01'] >= (1 - margin) * (p1['sp_r03_c02'] + p1['sp_r03_c03'])])])
#        assert pd.np.any([np.isnan(p1['sp_r04_c01']), pd.np.all([p1['sp_r04_c01'] <= (1 + margin) * (p1['sp_r04_c02'] + p1['sp_r04_c03']), 
#                          p1['sp_r04_c01'] >= (1 - margin) * (p1['sp_r04_c02'] + p1['sp_r04_c03'])])])
#        assert pd.np.any([np.isnan(p1['sp_r05_c01']), pd.np.all([p1['sp_r05_c01'] <= (1 + margin) * (p1['sp_r05_c02'] + p1['sp_r05_c03']), 
#                          p1['sp_r05_c01'] >= (1 - margin) * (p1['sp_r05_c02'] + p1['sp_r05_c03'])])])
#        assert pd.np.any([np.isnan(p1['sp_r07_c01']), pd.np.all([p1['sp_r07_c01'] <= (1 + margin) * (p1['sp_r07_c02'] + p1['sp_r07_c03']), 
#                          p1['sp_r07_c01'] >= (1 - margin) * (p1['sp_r07_c02'] + p1['sp_r07_c03'])])])
#        assert pd.np.any([np.isnan(p1['sp_r06_c01']), pd.np.all([p1['sp_r06_c01'] <= (1 + margin) * (p1['sp_r06_c02'] + p1['sp_r06_c03']), 
#                          p1['sp_r06_c01'] >= (1 - margin) * (p1['sp_r06_c02'] + p1['sp_r06_c03'])])])
#        assert pd.np.any([np.isnan(p1['sp_r08_c01']), pd.np.all([p1['sp_r08_c01'] <= (1 + margin) * (p1['sp_r08_c02'] + p1['sp_r08_c03']), 
#                          p1['sp_r08_c01'] >= (1 - margin) * (p1['sp_r08_c02'] + p1['sp_r08_c03'])])])
        
        p1['wd_r01_c01'] = pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].SUPPLY_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].SUPPLY_GROUNDWATER)])
        
        p1['wd_r02_c01'] = pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].SUPPLY_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].SUPPLY_SURFACEWATER)])
                               
        p1['wd_r03_c01'] = pd.np.nansum([p1['wd_r01_c01'],p1['wd_r02_c01']])
        
        p1['sp_r01_c04'] = pd.np.nansum([p1['sp_r01_c02'],p1['sp_r02_c02'],p1['sp_r03_c02'],p1['sp_r04_c02'],p1['sp_r05_c02'],p1['sp_r06_c02'],p1['sp_r07_c02'],p1['sp_r08_c02']])
        
        p1['of_r03_c02'] = pd.np.nansum([p1['sp_r01_c03'],p1['sp_r02_c03'],p1['sp_r03_c03'],p1['sp_r04_c03'],p1['sp_r05_c03'],p1['sp_r06_c03'],p1['sp_r07_c03'],p1['sp_r08_c03']])
        
        p1['of_r02_c01'] = pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].RECOVERABLE_SURFACEWATER)])
                               
        p1['of_r04_c01'] = pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].RECOVERABLE_GROUNDWATER)])
                               
        p1['of_r03_c01'] = pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].NON_RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].NON_RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].NON_RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].NON_RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].NON_RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].NON_RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].NON_RECOVERABLE_SURFACEWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].NON_RECOVERABLE_SURFACEWATER)])
                               
        p1['of_r05_c01'] = pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].NON_RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].NON_RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].NON_RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].NON_RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].NON_RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].NON_RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].NON_RECOVERABLE_GROUNDWATER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].NON_RECOVERABLE_GROUNDWATER)])
                               
        p1['of_r04_c02'] = pd.np.nansum([p1['of_r05_c01'],p1['of_r03_c01']])
        
        p1['sp_r02_c04'] = pd.np.nansum([p1['of_r02_c01'],p1['of_r04_c01']])
        
        p1['of_r09_c02'] = pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].CONSUMED_OTHER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].CONSUMED_OTHER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].CONSUMED_OTHER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].CONSUMED_OTHER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].CONSUMED_OTHER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].CONSUMED_OTHER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].CONSUMED_OTHER),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].CONSUMED_OTHER)])
    
        p1['of_r02_c02'] = pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].NON_CONVENTIONAL_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].NON_CONVENTIONAL_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].NON_CONVENTIONAL_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].NON_CONVENTIONAL_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].NON_CONVENTIONAL_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].NON_CONVENTIONAL_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].NON_CONVENTIONAL_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].NON_CONVENTIONAL_ET)])
                               
        p1['of_r01_c02'] = pd.np.nansum([float(df1.loc[(df1.LANDUSE_TYPE == "Irrigated crops")].CONSUMED_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Managed water bodies")].CONSUMED_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Industry")].CONSUMED_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Aquaculture")].CONSUMED_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Residential")].CONSUMED_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Greenhouses")].CONSUMED_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Power and Energy")].CONSUMED_ET),
                               float(df1.loc[(df1.LANDUSE_TYPE == "Other")].CONSUMED_ET)])
                               
        p1['of_r01_c01'] = pd.np.nansum([p1['of_r02_c02'],p1['of_r01_c02']])
    
    # Read csv part 2
    if data[1] is not None:
        p2 = dict()
        p2['sp_r01_c02'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].CONSUMED_ET),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].CONSUMED_OTHER)])
        p2['sp_r02_c02'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].CONSUMED_ET),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].CONSUMED_OTHER)])
        p2['sp_r03_c02'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].CONSUMED_ET),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].CONSUMED_OTHER)])
        p2['sp_r04_c02'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].CONSUMED_ET),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].CONSUMED_OTHER)])
        p2['sp_r05_c02'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].CONSUMED_ET),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].CONSUMED_OTHER)])
        p2['sp_r06_c02'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].CONSUMED_ET),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].CONSUMED_OTHER)])
        p2['sp_r07_c02'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].CONSUMED_ET),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].CONSUMED_OTHER)])
        p2['sp_r08_c02'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].CONSUMED_ET),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].CONSUMED_OTHER)])
        
        p2['sp_r01_c03'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].RECOVERABLE_GROUNDWATER)])
        p2['sp_r02_c03'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].RECOVERABLE_GROUNDWATER)])
        p2['sp_r03_c03'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].RECOVERABLE_GROUNDWATER)])
        p2['sp_r04_c03'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].RECOVERABLE_GROUNDWATER)])
        p2['sp_r05_c03'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].RECOVERABLE_GROUNDWATER)])
        p2['sp_r06_c03'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].RECOVERABLE_GROUNDWATER)])
        p2['sp_r07_c03'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].RECOVERABLE_GROUNDWATER)])
        p2['sp_r08_c03'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].RECOVERABLE_GROUNDWATER)])
        
        p2['sp_r01_c01'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].SUPPLY_GROUNDWATER)])
        p2['sp_r02_c01'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].SUPPLY_GROUNDWATER)])
        p2['sp_r03_c01'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].SUPPLY_GROUNDWATER)])
        p2['sp_r04_c01'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].SUPPLY_GROUNDWATER)])
        p2['sp_r05_c01'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].SUPPLY_GROUNDWATER)])
        p2['sp_r06_c01'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].SUPPLY_GROUNDWATER)])
        p2['sp_r07_c01'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].SUPPLY_GROUNDWATER)])
        p2['sp_r08_c01'] = pd.np.sum([float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].SUPPLY_GROUNDWATER)])
        
#        assert pd.np.any([np.isnan(p2['sp_r01_c01']), pd.np.all([p2['sp_r01_c01'] <= (1 + margin) * (p2['sp_r01_c02'] + p2['sp_r01_c03']), 
#                          p2['sp_r01_c01'] >= (1 - margin) * (p2['sp_r01_c02'] + p2['sp_r01_c03'])])])
#        assert pd.np.any([np.isnan(p2['sp_r02_c01']), pd.np.all([p2['sp_r02_c01'] <= (1 + margin) * (p2['sp_r02_c02'] + p2['sp_r02_c03']), 
#                          p2['sp_r02_c01'] >= (1 - margin) * (p2['sp_r02_c02'] + p2['sp_r02_c03'])])])
#        assert pd.np.any([np.isnan(p2['sp_r03_c01']), pd.np.all([p2['sp_r03_c01'] <= (1 + margin) * (p2['sp_r03_c02'] + p2['sp_r03_c03']), 
#                          p2['sp_r03_c01'] >= (1 - margin) * (p2['sp_r03_c02'] + p2['sp_r03_c03'])])])
#        assert pd.np.any([np.isnan(p2['sp_r04_c01']), pd.np.all([p2['sp_r04_c01'] <= (1 + margin) * (p2['sp_r04_c02'] + p2['sp_r04_c03']), 
#                          p2['sp_r04_c01'] >= (1 - margin) * (p2['sp_r04_c02'] + p2['sp_r04_c03'])])])
#        assert pd.np.any([np.isnan(p2['sp_r05_c01']), pd.np.all([p2['sp_r05_c01'] <= (1 + margin) * (p2['sp_r05_c02'] + p2['sp_r05_c03']), 
#                          p2['sp_r05_c01'] >= (1 - margin) * (p2['sp_r05_c02'] + p2['sp_r05_c03'])])])
#        assert pd.np.any([np.isnan(p2['sp_r06_c01']), pd.np.all([p2['sp_r06_c01'] <= (1 + margin) * (p2['sp_r06_c02'] + p2['sp_r06_c03']), 
#                          p2['sp_r06_c01'] >= (1 - margin) * (p2['sp_r06_c02'] + p2['sp_r06_c03'])])])
#        assert pd.np.any([np.isnan(p2['sp_r07_c01']), pd.np.all([p2['sp_r07_c01'] <= (1 + margin) * (p2['sp_r07_c02'] + p2['sp_r07_c03']), 
#                          p2['sp_r07_c01'] >= (1 - margin) * (p2['sp_r07_c02'] + p2['sp_r07_c03'])])])
#        assert pd.np.any([np.isnan(p2['sp_r08_c01']), pd.np.all([p2['sp_r08_c01'] <= (1 + margin) * (p2['sp_r08_c02'] + p2['sp_r08_c03']), 
#                          p2['sp_r08_c01'] >= (1 - margin) * (p2['sp_r08_c02'] + p2['sp_r08_c03'])])])
        
        
        p2['dm_r01_c01'] = float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].DEMAND)
        p2['dm_r02_c01'] = float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].DEMAND)
        p2['dm_r03_c01'] = float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].DEMAND)
        p2['dm_r04_c01'] = float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].DEMAND)
        p2['dm_r05_c01'] = float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].DEMAND)
        p2['dm_r06_c01'] = float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].DEMAND)
        p2['dm_r07_c01'] = float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].DEMAND)
        p2['dm_r08_c01'] = float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].DEMAND)
        
        p2['wd_r01_c01'] = pd.np.nansum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].SUPPLY_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].SUPPLY_GROUNDWATER)])
        
        p2['wd_r03_c01'] = pd.np.nansum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].SUPPLY_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].SUPPLY_SURFACEWATER)])
        
        p2['wd_r02_c01'] = pd.np.nansum([p2['wd_r01_c01'],p2['wd_r03_c01']])
        
        p2['sp_r01_c04'] = pd.np.nansum([p2['sp_r01_c02'],
                                   p2['sp_r02_c02'],
                                   p2['sp_r03_c02'],
                                   p2['sp_r04_c02'],
                                   p2['sp_r05_c02'],
                                   p2['sp_r06_c02'],
                                   p2['sp_r07_c02'],
                                   p2['sp_r08_c02']])
                                   
        p2['of_r03_c02'] = p2['sp_r02_c04'] = pd.np.nansum([p2['sp_r01_c03'],
                                   p2['sp_r02_c03'],
                                   p2['sp_r03_c03'],
                                   p2['sp_r04_c03'],
                                   p2['sp_r05_c03'],
                                   p2['sp_r06_c03'],
                                   p2['sp_r07_c03'],
                                   p2['sp_r08_c03']])
                                   
        p2['of_r01_c01'] = p2['of_r01_c02'] = pd.np.nansum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].CONSUMED_ET),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].CONSUMED_ET),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].CONSUMED_ET),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].CONSUMED_ET),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].CONSUMED_ET),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].CONSUMED_ET),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].CONSUMED_ET),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].CONSUMED_ET)])
        
        p2['of_r02_c02'] = pd.np.nansum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].CONSUMED_OTHER),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].CONSUMED_OTHER),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].CONSUMED_OTHER),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].CONSUMED_OTHER),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].CONSUMED_OTHER),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].CONSUMED_OTHER),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].CONSUMED_OTHER),
                                                float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].CONSUMED_OTHER)])
        
        
        p2['of_r03_c01'] = pd.np.nansum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].RECOVERABLE_SURFACEWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].RECOVERABLE_SURFACEWATER)]) 
        
        p2['of_r02_c01'] = pd.np.nansum([float(df2.loc[(df2.LANDUSE_TYPE == "Forests")].RECOVERABLE_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Shrubland")].RECOVERABLE_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Rainfed Crops")].RECOVERABLE_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Forest Plantations")].RECOVERABLE_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Water Bodies")].RECOVERABLE_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Wetlands")].RECOVERABLE_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Natural Grasslands")].RECOVERABLE_GROUNDWATER),
                                   float(df2.loc[(df2.LANDUSE_TYPE == "Other (Non-Manmade)")].RECOVERABLE_GROUNDWATER)]) 

    # Calculations & modify svgs
    if not template:
        svg_template_path_1 = get_template('sheet_4_part1', 
                                         template_folder='Default')
        svg_template_path_2 = get_template('sheet_4_part2',
                                         template_folder='Default')

    else:
        svg_template_path_1 = os.path.abspath(template[0])
        svg_template_path_2 = os.path.abspath(template[1])

        
    if data[0] is not None:
        tree1 = ET.parse(svg_template_path_1)
        xml_txt_box = tree1.findall('''.//*[@id='basin1']''')[0]
        xml_txt_box.getchildren()[0].text = 'Basin: ' + basin
        
        xml_txt_box = tree1.findall('''.//*[@id='period1']''')[0]
        xml_txt_box.getchildren()[0].text = 'Period: ' + period
        
        xml_txt_box = tree1.findall('''.//*[@id='units1']''')[0]
        #xml_txt_box.getchildren()[0].text = 'Part 1: Manmade ({0})'.format(units[0])

        # if np.all([smart_unit, scale > 0]):
        #     xml_txt_box.getchildren()[0].text = 'Part 1: Manmade ({0} {1})'.format(10.**-scale, units[1])
        # else:
        #     xml_txt_box.getchildren()[0].text = 'Part 1: Manmade ({0})'.format(units[1])
            
        # request Marloes (remove Part 1 from title)
        if np.all([smart_unit, scale > 0]):
            xml_txt_box.getchildren()[0].text = '({0} {1})'.format(10.**-scale, units[1])
        else:
            xml_txt_box.getchildren()[0].text = '({0})'.format(units[1])
        

        for key in list(p1.keys()):
            xml_txt_box = tree1.findall(".//*[@id='{0}']".format(key))[0]
            if not pd.isnull(p1[key]):
                xml_txt_box.getchildren()[0].text = '%.2f' % p1[key]
            else:
                xml_txt_box.getchildren()[0].text = '-'
                
    if data[1] is not None:
        tree2 = ET.parse(svg_template_path_2)
        xml_txt_box = tree2.findall('''.//*[@id='basin2']''')[0]
        xml_txt_box.getchildren()[0].text = 'Basin: ' + basin
        
        xml_txt_box = tree2.findall('''.//*[@id='period2']''')[0]
        xml_txt_box.getchildren()[0].text = 'Period: ' + period
        
        xml_txt_box = tree2.findall('''.//*[@id='units2']''')[0]
        #xml_txt_box.getchildren()[0].text = 'Part 2: Natural Landuse ({0})'.format(units[1])

        if np.all([smart_unit, scale > 0]):
            xml_txt_box.getchildren()[0].text = 'Part 2: Natural Landuse ({0} {1})'.format(10**-scale, units[1])
        else:
            xml_txt_box.getchildren()[0].text = 'Part 2: Natural Landuse ({0})'.format(units[1])
            
        for key in list(p2.keys()):
            xml_txt_box = tree2.findall(".//*[@id='{0}']".format(key))[0]
            if not pd.isnull(p2[key]):
                xml_txt_box.getchildren()[0].text = '%.2f' % p2[key]
            else:
                xml_txt_box.getchildren()[0].text = '-'    
    # Export svg to png    
    if data[0] is not None:
        tempout_path = output[0].replace('.pdf', '_temporary.svg')
        tree1.write(tempout_path)
        cairosvg.svg2pdf(url=tempout_path, write_to=output[0])
#        os.remove(tempout_path)
       
    if data[1] is not None:
        tempout_path = output[1].replace('.pdf', '_temporary.svg')
        tree2.write(tempout_path)
        cairosvg.svg2pdf(url=tempout_path, write_to=output[1])
#        os.remove(tempout_path)

def sheet_5_dynamic_arrows(dico_in, dico_out, test_svg, outpath):
    normal_arrow = {}
    straight_out = {}
    straight_in = {}
    join_one_below = {}
    join_one_top = {}
    lower_arrow = {}
    lower_join_one_below = {}

#    element1 = '<ns0:path d="M 63.071871,264.267 V 271.30428 H 78.457001 V 154.10108 L 85.774098,154.10077 V 156.582 L 87.774096,157.531 89.773756,156.582 89.774174,150.12138 74.457001,150.12171 V 267.32467 L 67.07187,267.32475 67.072128,264.267 65.08986,265.203 Z" id="normal_arrow" style="fill:#73b7d1;fill-opacity:1;stroke:#fbfbfb;stroke-width:0.55299997px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccccccccccc" ns1:connector-curvature="0" ns1:label="#path8251" />'
#    element1 = 'ns0:path d="M 63.071871,264.267 V 271.30428 H 78.457001 V 154.10108 L 85.774098,154.10077 V 156.582 L 87.774096,157.531 89.773756,156.582 89.774174,150.12138 74.457001,150.12171 V 267.32467 L 67.07187,267.32475 67.072128,264.267 65.08986,265.203 Z" id="normal_arrow" style="fill:#73b7d1;fill-opacity:1;stroke:#fbfbfb;stroke-width:0.55299997px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccccccccccc" ns1:connector-curvature="0" ns1:label="#path8251" '
#    element2 = 'ns0:path d="M 63.154,271.035 H 86 V 267.455 L 66.6,267.45471 V 264.7052 L 64.872,265.528 63.154476,264.71131" id="low_bar" style="opacity:1;fill:#73b7d1;fill-opacity:1;stroke:none;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccc" ns1:connector-curvature="0" ns1:label="#path8255" '
#    element3 = 'ns0:path d="M 62.851212,148.62795 62.853138,156.5571 64.853137,157.71202 66.852797,156.5571 66.853215,148.69463 64.85134,149.76798 Z" id="top_in" style="opacity:1;fill:#73b7d1;fill-opacity:1;stroke:#ffffff;stroke-width:0.55299997;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccc" ns1:connector-curvature="0" ns1:label="#path8255" '
#    element4 = 'ns0:path d="M 66.872,264.29 66.873585,272.19258 64.873925,273.3475 62.873926,272.19258 62.872,264.29 64.872128,265.203 Z" id="bottom_out" style="fill:#73b7d1;fill-opacity:1;stroke:#ffffff;stroke-width:0.55299997;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccc" ns1:connector-curvature="0" ns1:label="#path8274" '
#    element5 = 'ns0:path d="M 67.468749,150.121 74.457001,150.12171 89.774172,150.12138 89.773754,156.582 87.774094,157.531 85.774098,156.582 V 154.10077 L 67.468748,154.101 Z" id="top_connect_1" style="fill:#73b7d1;fill-opacity:1;stroke:#fcfcfc;stroke-width:0.55299997;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccccc" ns1:connector-curvature="0" ns1:label="#path8250" />\n<ns0:path d="M 69.297345,150.399 H 65.921953 L 65.911237,153.823 H 69.279 Z" id="top_connect_2" style="fill:#73b7d1;fill-opacity:1;stroke:none;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccc" ns1:connector-curvature="0" ns1:label="#path8262" '
#    element6 = '<ns0:rect height="3.4260001" id="rect_join_mask" style="stroke-width:0.25686634;fill:#73b7d1;fill-opacity:1" transform="translate(%.2f)" width="1.9203489" x="62.342754" y="150.399" ns1:label="#rect3787" /> '
#    element7 = '<ns0:rect height="3.4300554" id="rect_low_mask" style="fill:#73b7d1;fill-opacity:1;stroke-width:0.26458332"  transform="translate(%.2f)" width="1.4658357" x="66.373032" y="267.59995" ns1:label="#rect8273" />'

    element1 = '<path d="M 63.071871,264.267 V 271.30428 H 78.457001 V 154.10108 L 85.774098,154.10077 V 156.582 L 87.774096,157.531 89.773756,156.582 89.774174,150.12138 74.457001,150.12171 V 267.32467 L 67.07187,267.32475 67.072128,264.267 65.08986,265.203 Z" id="normal_arrow" style="fill:#73b7d1;fill-opacity:1;stroke:#fbfbfb;stroke-width:0.55299997px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccccccccccc" ns1:connector-curvature="0" ns1:label="#path8251" />'
    element1 = 'path d="M 63.071871,264.267 V 271.30428 H 78.457001 V 154.10108 L 85.774098,154.10077 V 156.582 L 87.774096,157.531 89.773756,156.582 89.774174,150.12138 74.457001,150.12171 V 267.32467 L 67.07187,267.32475 67.072128,264.267 65.08986,265.203 Z" id="normal_arrow" style="fill:#73b7d1;fill-opacity:1;stroke:#fbfbfb;stroke-width:0.55299997px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccccccccccc" ns1:connector-curvature="0" ns1:label="#path8251" '
    element2 = 'path d="M 63.154,271.035 H 86 V 267.455 L 66.6,267.45471 V 264.7052 L 64.872,265.528 63.154476,264.71131" id="low_bar" style="opacity:1;fill:#73b7d1;fill-opacity:1;stroke:none;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccc" ns1:connector-curvature="0" ns1:label="#path8255" '
    element3 = 'path d="M 62.851212,148.62795 62.853138,156.5571 64.853137,157.71202 66.852797,156.5571 66.853215,148.69463 64.85134,149.76798 Z" id="top_in" style="opacity:1;fill:#73b7d1;fill-opacity:1;stroke:#ffffff;stroke-width:0.55299997;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccc" ns1:connector-curvature="0" ns1:label="#path8255" '
    element4 = 'path d="M 66.872,264.29 66.873585,272.19258 64.873925,273.3475 62.873926,272.19258 62.872,264.29 64.872128,265.203 Z" id="bottom_out" style="fill:#73b7d1;fill-opacity:1;stroke:#ffffff;stroke-width:0.55299997;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccc" ns1:connector-curvature="0" ns1:label="#path8274" '
    element5 = 'path d="M 67.468749,150.121 74.457001,150.12171 89.774172,150.12138 89.773754,156.582 87.774094,157.531 85.774098,156.582 V 154.10077 L 67.468748,154.101 Z" id="top_connect_1" style="fill:#73b7d1;fill-opacity:1;stroke:#fcfcfc;stroke-width:0.55299997;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccccccc" ns1:connector-curvature="0" ns1:label="#path8250" />\n<path d="M 69.297345,150.399 H 65.921953 L 65.911237,153.823 H 69.279 Z" id="top_connect_2" style="fill:#73b7d1;fill-opacity:1;stroke:none;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" transform="translate(%.2f)" ns2:nodetypes="ccccc" ns1:connector-curvature="0" ns1:label="#path8262" '
    element6 = '<rect height="3.4260001" id="rect_join_mask" style="stroke-width:0.25686634;fill:#73b7d1;fill-opacity:1" transform="translate(%.2f)" width="1.9203489" x="62.342754" y="150.399" ns1:label="#rect3787" /> '
    element7 = '<rect height="3.4300554" id="rect_low_mask" style="fill:#73b7d1;fill-opacity:1;stroke-width:0.26458332"  transform="translate(%.2f)" width="1.4658357" x="66.373032" y="267.59995" ns1:label="#rect8273" />'

    expected_nb_arrows = np.sum([len(dico_out[k]) for k in list(dico_out.keys())]) + np.sum([0 in dico_in[k] for k in list(dico_in.keys())])

    dico_in_b = {}
    for k in list(dico_in.keys()):
        dico_in_b[k] = [dico_in[k][j] for j in range(len(dico_in[k])) if dico_in[k][j] != 0]
    dico_out_b = {}
    for k in list(dico_in.keys()):
        dico_out_b[k] = [dico_out[k][j] for j in range(len(dico_out[k])) if dico_out[k][j] != 0]

    for sb in list(dico_out.keys()):
        if len(dico_out_b[sb]) == 1:
            if (len(dico_in_b[dico_out_b[sb][0]]) == 1) & (dico_out_b[sb] == sb+1):
                normal_arrow[sb] = 1
            else:
                prev_list = [i for i in range(dico_out_b[sb][0]-len(dico_in_b[dico_out_b[sb][0]]), dico_out_b[sb][0])]
                contrib = dico_in_b[dico_out_b[sb][0]]
                if (prev_list == contrib) & (contrib != []):
                    normal_arrow[np.max(contrib)] = 1
                    contrib_2 = [i for i in contrib if i != (np.max(contrib))]
                    for i in range(len(contrib_2)):
                        join_one_below[contrib_2[i]] = 1
               # else to add in later with extra levels of complexity
        elif len(dico_out_b[sb]) > 0:
            going_to = dico_out_b[sb]
            next_list = [i for i in range(sb+1, sb+1+len(dico_out_b[sb]))]
            if going_to == next_list:
                normal_arrow[sb] = 1
                going_to_2 = [i for i in going_to if i != (np.max(going_to))]
                for j in range(len(going_to_2)):
                    join_one_top[going_to_2[j]] = 1

    for sb in list(dico_out.keys()):
        if 0 in dico_out[sb]:
            straight_out[sb] = 1
    for sb in list(dico_in.keys()):
        if 0 in dico_in[sb]:
            straight_in[sb] = 1

    actual_nb_arrows = len(normal_arrow) + len(straight_out) + len(straight_in) \
                        + len(join_one_below) + len(join_one_top)\
                        + len(lower_arrow) + len(lower_join_one_below)

    if expected_nb_arrows == actual_nb_arrows:
        tree = ET.parse(test_svg)
        off1 = 22.66
        for n in list(normal_arrow.keys()):
            offset = (n - 1) * off1
            child = ET.Element(element1 %offset)
            layer = tree.findall('''*[@id='layer1']''')[0]
            layer.append(child)

        for j in list(straight_in.keys()):
            offset = (j - 1) * off1 + .22
            child = ET.Element(element3 %offset)
            layer = tree.findall('''*[@id='layer1']''')[0]
            layer.append(child)

        for j in list(straight_out.keys()):
            offset = (j - 1) * off1 + .22
            child = ET.Element(element4 %offset)
            layer = tree.findall('''*[@id='layer1']''')[0]
            layer.append(child)

        for j in list(join_one_top.keys()):
            offset = (j - 1) * off1
            child = ET.Element(element5 %(offset, offset))
            layer = tree.findall('''*[@id='layer1']''')[0]
            layer.append(child)

        for j in list(join_one_below.keys()):
            offset = (j - 1) * off1 +.22
            child = ET.Element(element2 %offset)
            layer = tree.findall('''*[@id='layer1']''')[0]
            layer.append(child)

        for j in list(straight_in.keys()):
            if len(dico_in[j]) > 1:
                offset = (j - 1) * off1
                child = ET.Element(element6 %offset)
                layer = tree.findall('''*[@id='layer1']''')[0]
                layer.append(child)

        for j in list(straight_out.keys()):
            if len(dico_out[j]) > 1:
                offset = (j - 1) * off1
                child = ET.Element(element7 %offset)
                layer = tree.findall('''*[@id='layer1']''')[0]
                layer.append(child)
        tree.write(outpath)
    else:
        shutil.copyfile(test_svg, outpath)
        print('ERROR: unexpected number of arrows.\n      Basin structure too complex to generate Sheet 5 arrows automatically.\
               \n      Standard template returned as output.')
    return outpath


def print_sheet5(basin, sb_codes, dico_in, dico_out, period, units, data, output, template=False, smart_unit=False):

    df = pd.read_csv(data, sep=';')
    scale = 0
    if smart_unit:
        scale_test = np.nanmax(df['VALUE'].values)
        scale = scale_factor(scale_test)
        df['VALUE'] *= 10**scale
    if not template:
        svg_template_path=get_template('sheet_5',
                                         template_folder='Default')
    else:
        svg_template_path = os.path.abspath(template)
        
    #Add arrows to template when possible (dependent on subbasin structure)
    wrong_path = os.path.join(*output.split('\\')[:-1])
    output_folder = wrong_path[:2]+'\\'+wrong_path[2:]
    svg_template_path = sheet_5_dynamic_arrows(dico_in, dico_out, svg_template_path,
                                          os.path.join(output_folder, 'temp_sheet5.svg'))

    tree = ET.parse(svg_template_path)

    xml_txt_box = tree.findall('''.//*[@id='unit']''')[0]
    if np.all([smart_unit, scale > 0]):
        list(xml_txt_box)[0].text = 'Sheet 5b: Surface Water ({0} {1})'.format(10**-scale,units)
    else:
        list(xml_txt_box)[0].text = 'Sheet 5b: Surface Water ({0})'.format(units)

    xml_txt_box = tree.findall('''.//*[@id='basin']''')[0]
    list(xml_txt_box)[0].text = 'Basin: ' + basin.replace('_', ' ')

    xml_txt_box = tree.findall('''.//*[@id='period']''')[0]
    list(xml_txt_box)[0].text = 'Period: ' + period.replace('_', '-')

    line_id0 = [31633, 30561, 30569, 30577, 30585, 30905, 30913, 30921, 30929,
                31873, 31993, 32001, 32026, 32189, 32197, 32318, 32465, 32609,
                31273, 31281, 31289, 31297, 32817]
    line_lengths = [1, 4, 4, 4, 4, 4, 4, 4, 4, 1, 2, 2, 1, 2, 2, 1, 1, 1, 4, 4, 4, 4, 1]
    line_names = ['Inflow',
                  'Fast Runoff: PROTECTED', 'Fast Runoff: UTILIZED',
                  'Fast Runoff: MODIFIED', 'Fast Runoff: MANAGED',
                  'Slow Runoff: PROTECTED', 'Slow Runoff: UTILIZED',
                  'Slow Runoff: MODIFIED', 'Slow Runoff: MANAGED',
                  'Total Runoff',
                  'SW withdr. manmade', 'SW withdr. natural',
                  'SW withdr. total',
                  'Return Flow SW', 'Return Flow GW',
                  'Total Return Flow',
                  'Interbasin Transfer', 'SW storage change',
                  'Outflow: Committed', 'Outflow: Non Recoverable',
                  'Outflow: Non Utilizable', 'Outflow: Utilizable',
                  'Outflow: Total']
    current_variables = ['Inflow',
                         'Fast Runoff: PROTECTED', 'Fast Runoff: UTILIZED',
                         'Fast Runoff: MODIFIED', 'Fast Runoff: MANAGED',
                         'Slow Runoff: PROTECTED', 'Slow Runoff: UTILIZED',
                         'Slow Runoff: MODIFIED', 'Slow Runoff: MANAGED',
                         'SW withdr. manmade', 'SW withdr. natural',
                         'SW withdr. total',
                         'Return Flow SW', 'Return Flow GW', 'Total Return Flow',
                         'Total Runoff', 'Outflow: Committed', 'Outflow: Non Recoverable',
                         'Outflow: Non Utilizable', 'Outflow: Utilizable',
                         'Outflow: Total',
                         'Interbasin Transfer',
                         'SW storage change'
                        ]
#    current_variables = line_names
    for var1 in current_variables:
        line_nb = [i for i in range(len(line_names)) if line_names[i] == var1][0]
        line_0 = line_id0[line_nb]
        line_len = line_lengths[line_nb]
        df_var = df.loc[df.VARIABLE == var1]
        sb_order = sb_codes
        value_sum = 0
        for sb in sb_order:
            df_sb = df_var.loc[df_var.SUBBASIN == str(sb)]
            cell_id = 'g' + str(line_0 + 8*(sb-1)*line_len)
            xml_txt_box = tree.findall('''.//*[@id='{0}']'''.format(cell_id))[0]
            # fixing the -0.0 in DeltaS by increasing numb of digits
            if var1 == 'SW storage change':
                xml_txt_box[0].text = '%.2f' %(df_sb.VALUE)
            else:
                xml_txt_box[0].text = '%.1f' %(df_sb.VALUE)
            #xml_txt_box[0].text = '%.1f' %(df_sb.VALUE)
            value_sum += float(df_sb.VALUE)

        cell_id = 'g' + str(line_0 + 8*9*line_len)
        df_sb = df_var.loc[df_var.SUBBASIN == 'basin']
        xml_txt_box = tree.findall('''.//*[@id='{0}']'''.format(cell_id))[0]
        # fixing the -0.0 in DeltaS by increasing numb of digits
        if var1 == 'SW storage change':
            xml_txt_box[0].text = '%.2f' %(df_sb.VALUE)
        else:
            xml_txt_box[0].text = '%.1f' %(df_sb.VALUE)
        #xml_txt_box[0].text = '%.1f' %(df_sb.VALUE)

    tempout_path = output.replace('.pdf', '_temporary.svg')
    tree.write(tempout_path)    
    cairosvg.svg2pdf(url=tempout_path, write_to=output)    
#    os.remove(tempout_path)

    return
        
def print_sheet6(basin, period, units, data, output, template=False, decimal = 1, smart_unit = False):
    """
    Create sheet 6 of the Water Accounting Plus framework.
    
    Parameters
    ----------
    basin : str
        The name of the basin.
    period : str
        The period of analysis.
    units : str
        the unit of the data on sheet 6.
    data : str
        csv file that contains the water data. The csv file has to
        follow an specific format. A sample csv is available here:
        https://github.com/wateraccounting/wa/tree/master/Sheets/csv
    output : list
        Filehandles pointing to the jpg files to be created.
    template : str or boolean, optional
        the svg file of the sheet. False
        uses the standard svg files. Default is False.
        
    Returns
    -------
    p1 : dict
        Dictionary with all values present on sheet 6.

    Examples
    --------
    >>> from wa.Sheets import *
    >>> create_sheet6(basin='Helmand', period='2007-2011',
                  units = 'km3/yr',
                  data = r'C:\Sheets\csv\Sample_sheet6.csv',
                  output = r'C:\Sheets\sheet_6.pdf')
    """
    df1 = pd.read_csv(data, sep=';')
    
    scale = 0
    if smart_unit:
        scale_test = np.nanmax([pd.np.nansum(df1.loc[(df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE),
                  pd.np.nansum([pd.np.nansum(df1.loc[(df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE), 
                                float(df1.loc[(df1.SUBTYPE == 'ManagedAquiferRecharge')].VALUE)])])
        
        scale = scale_factor(scale_test)
        
        df1['VALUE'] *= 10**scale
    
    p1 = dict()
    
    p1['VR_forest'] = float(df1.loc[(df1.TYPE == 'Forests') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_shrubland'] = float(df1.loc[(df1.TYPE == 'Shrubland') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_naturalgrassland'] = float(df1.loc[(df1.TYPE == 'Natural Grasslands') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_naturalwaterbodies'] = float(df1.loc[(df1.TYPE == 'Natural Water Bodies') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_wetlands'] = float(df1.loc[(df1.TYPE == 'Wetlands') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_rainfedcrops'] = float(df1.loc[(df1.TYPE == 'Rainfed Crops') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_forestplantations'] = float(df1.loc[(df1.TYPE == 'Forest Plantations') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_irrigatedcrops'] = float(df1.loc[(df1.TYPE == 'Irrigated crops') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_managedwaterbodies'] = float(df1.loc[(df1.TYPE == 'Managed water bodies') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_residential'] = float(df1.loc[(df1.TYPE == 'Residential') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_industry'] = float(df1.loc[(df1.TYPE == 'Industry') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_other'] = float(df1.loc[(df1.TYPE == 'Other (Non-Manmade)') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE) 
    + float(df1.loc[(df1.TYPE == 'Other') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VR_managedaquiferrecharge'] = float(df1.loc[(df1.TYPE == 'NON_LU_SPECIFIC') & (df1.SUBTYPE == 'ManagedAquiferRecharge')].VALUE)
    p1['VR_glaciers'] = float(df1.loc[(df1.TYPE == 'Glaciers') & (df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    
    p1['VGW_forest'] = float(df1.loc[(df1.TYPE == 'Forests') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_shrubland'] = float(df1.loc[(df1.TYPE == 'Shrubland') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_rainfedcrops'] = float(df1.loc[(df1.TYPE == 'Rainfed Crops') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_forestplantations'] = float(df1.loc[(df1.TYPE == 'Forest Plantations') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_wetlands'] = float(df1.loc[(df1.TYPE == 'Wetlands') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_naturalgrassland'] = float(df1.loc[(df1.TYPE == 'Natural Grasslands') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_othernatural'] = float(df1.loc[(df1.TYPE == 'Other (Non-Manmade)') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_irrigatedcrops'] = float(df1.loc[(df1.TYPE == 'Irrigated crops') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_industry'] = float(df1.loc[(df1.TYPE == 'Industry') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_aquaculture'] = float(df1.loc[(df1.TYPE == 'Aquaculture') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_residential'] = float(df1.loc[(df1.TYPE == 'Residential') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_greenhouses'] = float(df1.loc[(df1.TYPE == 'Greenhouses') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    p1['VGW_othermanmade'] = float(df1.loc[(df1.TYPE == 'Other') & (df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)

    p1['RFG_forest'] = float(df1.loc[(df1.TYPE == 'Forests') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_shrubland'] = float(df1.loc[(df1.TYPE == 'Shrubland') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_rainfedcrops'] = float(df1.loc[(df1.TYPE == 'Rainfed Crops') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_forestplantations'] = float(df1.loc[(df1.TYPE == 'Forest Plantations') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_wetlands'] = float(df1.loc[(df1.TYPE == 'Wetlands') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_naturalgrassland'] = float(df1.loc[(df1.TYPE == 'Natural Grasslands') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_othernatural'] = float(df1.loc[(df1.TYPE == 'Other (Non-Manmade)') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    
    p1['RFG_irrigatedcrops'] = float(df1.loc[(df1.TYPE == 'Irrigated crops') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_industry'] = float(df1.loc[(df1.TYPE == 'Industry') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_aquaculture'] = float(df1.loc[(df1.TYPE == 'Aquaculture') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_residential'] = float(df1.loc[(df1.TYPE == 'Residential') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_greenhouses'] = float(df1.loc[(df1.TYPE == 'Greenhouses') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    p1['RFG_other'] = float(df1.loc[(df1.TYPE == 'Other') & (df1.SUBTYPE == 'RETURN_FLOW_GROUNDWATER')].VALUE)
    
    p1['RFS_forest'] = float(df1.loc[(df1.TYPE == 'Forests') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_shrubland'] = float(df1.loc[(df1.TYPE == 'Shrubland') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_rainfedcrops'] = float(df1.loc[(df1.TYPE == 'Rainfed Crops') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_forestplantations'] = float(df1.loc[(df1.TYPE == 'Forest Plantations') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_wetlands'] = float(df1.loc[(df1.TYPE == 'Wetlands') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_naturalgrassland'] = float(df1.loc[(df1.TYPE == 'Natural Grasslands') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_othernatural'] = float(df1.loc[(df1.TYPE == 'Other (Non-Manmade)') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_irrigatedcrops'] = float(df1.loc[(df1.TYPE == 'Irrigated crops') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_industry'] = float(df1.loc[(df1.TYPE == 'Industry') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_aquaculture'] = float(df1.loc[(df1.TYPE == 'Aquaculture') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_residential'] = float(df1.loc[(df1.TYPE == 'Residential') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_greenhouses'] = float(df1.loc[(df1.TYPE == 'Greenhouses') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    p1['RFS_othermanmade'] = float(df1.loc[(df1.TYPE == 'Other') & (df1.SUBTYPE == 'RETURN_FLOW_SURFACEWATER')].VALUE)
    
    for key, value in list(p1.items()):
        p1[key] = np.round(value, decimals = decimal)
    
    p1['VRtotal_natural'] = pd.np.nansum(df1.loc[(df1.SUBTYPE == 'VERTICAL_RECHARGE')].VALUE)
    p1['VRtotal_manmade'] = float(df1.loc[(df1.SUBTYPE == 'ManagedAquiferRecharge')].VALUE)
    p1['VRtotal'] = pd.np.nansum([p1['VRtotal_natural'], p1['VRtotal_manmade']])
    
    p1['CRtotal'] = float(df1.loc[(df1.SUBTYPE == 'CapillaryRise')].VALUE)
    #p1['delta_S'] = float(df1.loc[(df1.SUBTYPE == 'DeltaS')].VALUE)
    
    p1['VGWtotal_natural'] = pd.np.nansum([p1['VGW_forest'], p1['VGW_shrubland'], p1['VGW_rainfedcrops'], p1['VGW_forestplantations'], p1['VGW_wetlands'], p1['VGW_naturalgrassland'], p1['VGW_othernatural']])
    p1['VGWtotal_manmade'] = pd.np.nansum([p1['VGW_irrigatedcrops'],p1['VGW_industry'],p1['VGW_aquaculture'],p1['VGW_residential'],p1['VGW_greenhouses'],p1['VGW_othermanmade']])
    p1['VGWtotal'] = pd.np.nansum(df1.loc[(df1.SUBTYPE == 'VERTICAL_GROUNDWATER_WITHDRAWALS')].VALUE)
    
    p1['RFGtotal_manmade'] = pd.np.nansum([p1['RFG_irrigatedcrops'],
                                                        p1['RFG_industry'], 
                                                        p1['RFG_aquaculture'], 
                                                        p1['RFG_residential'], 
                                                        p1['RFG_greenhouses'], 
                                                        p1['RFG_other']])
    p1['RFGtotal_natural'] = pd.np.nansum([p1['RFG_forest'], p1['RFG_shrubland'],
                                          p1['RFG_rainfedcrops'], p1['RFG_forestplantations'],
                                          p1['RFG_wetlands'], p1['RFG_naturalgrassland'], p1['RFG_othernatural']])
    p1['RFGtotal'] = pd.np.nansum([p1['RFGtotal_natural'], p1['RFGtotal_manmade']])
    p1['RFStotal_natural'] = pd.np.nansum([p1['RFS_forest'], p1['RFS_shrubland'], p1['RFS_rainfedcrops'], p1['RFS_forestplantations'], p1['RFS_wetlands'], p1['RFS_naturalgrassland'], p1['RFS_othernatural']])
    
    p1['RFStotal_manmade'] = pd.np.nansum([p1['RFS_irrigatedcrops'],p1['RFS_industry'],p1['RFS_aquaculture'],p1['RFS_residential'],p1['RFS_greenhouses'],p1['RFS_othermanmade']])
    
    p1['RFStotal'] = pd.np.nansum([p1['RFStotal_natural'], p1['RFStotal_manmade']])
    
    p1['HGI'] = float(df1.loc[(df1.TYPE == 'NON_LU_SPECIFIC') & (df1.SUBTYPE == 'GWInflow')].VALUE)
    p1['HGO'] = float(df1.loc[(df1.TYPE == 'NON_LU_SPECIFIC') & (df1.SUBTYPE == 'GWOutflow')].VALUE)
    p1['baseflow'] = float(df1.loc[(df1.TYPE == 'NON_LU_SPECIFIC') & (df1.SUBTYPE == 'Baseflow')].VALUE)
    
    p1['delta_S'] = p1['VRtotal'] - p1['CRtotal'] - p1['VGWtotal'] + p1['RFGtotal'] + p1['RFStotal'] - p1['baseflow']
    #p1['CRtotal'] = p1['VRtotal'] - p1['VGWtotal'] + p1['RFGtotal_manmade'] + p1['RFStotal'] - p1['baseflow'] - p1['delta_S']

    

    for key, value in list(p1.items()):
        p1[key] = np.round(value, decimals = decimal)
        
    if not template:
        svg_template_path_1 = get_template('sheet_6',
                                         template_folder='Default')
    else:
        svg_template_path_1 = os.path.abspath(template)
    
    tree1 = ET.parse(svg_template_path_1)
    xml_txt_box = tree1.findall('''.//*[@id='basin']''')[0]
    xml_txt_box.getchildren()[0].text = 'Basin: ' + basin
    
    xml_txt_box = tree1.findall('''.//*[@id='period']''')[0]
    xml_txt_box.getchildren()[0].text = 'Period: ' + period
    
    xml_txt_box = tree1.findall('''.//*[@id='unit']''')[0]
    xml_txt_box.getchildren()[0].text = 'Sheet 6: Groundwater ({0})'.format(units)

    if np.all([smart_unit, scale > 0]):
        xml_txt_box.getchildren()[0].text = 'Sheet 6: Groundwater ({0} {1})'.format(10**-scale, units)
    else:
        xml_txt_box.getchildren()[0].text = 'Sheet 6: Groundwater ({0})'.format(units)
        
    for key in list(p1.keys()):
        xml_txt_box = tree1.findall(".//*[@id='{0}']".format(key))[0]
        if not pd.isnull(p1[key]):
            xml_txt_box.getchildren()[0].text = '{1:.{0}f}'.format(decimal, p1[key])
        else:
            xml_txt_box.getchildren()[0].text = '-'
    
    # Export svg to png    
    tempout_path = output.replace('.pdf', '_temporary.svg')
    tree1.write(tempout_path)    
    cairosvg.svg2pdf(url=tempout_path, write_to=output)    
#    os.remove(tempout_path)