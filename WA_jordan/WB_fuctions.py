# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 20:50:04 2020

@author: esa
"""
from WAsheets import calculate_flux as cf
from WAsheets import hydroloop as hl

def SW_return_abstraction(MAIN_FOLDER, mask, aeisw, population, yearly_nc, sample_nc, supply, et_incr, sroincr, percincr):
    monthly_nc=cf.resample_to_monthly_dataset(yearly_nc, sample_nc,
                                start_month=0,
                                output=None,
                                chunksize=None)

    sw_supply_fraction_nc=hl.calc_sw_supply_fraction_by_LU(monthly_nc, aeisw)
    sw_supply_nc,gw_supply_nc=hl.split_flow(supply,
                  fraction_nc=sw_supply_fraction_nc)
    
    return_nc=hl.substract_flow(supply, et_incr, name='return')
    
    ### split return by sroincr/total_incremental ratio
    sw_return_fraction_nc=hl.calc_sw_return_fraction(sroincr, percincr)
    sw_return_nc,gw_return_nc=hl.split_flow(return_nc,fraction_nc=sw_return_fraction_nc)
    
    residential_supply_nc=hl.calc_residential_water_consumption(
            population,
            mask,
            monthly_nc,
            wcpc=110,
            flow_type='supply')
    
    return_sw_from_sw_nc,return_sw_from_gw_nc=hl.split_flow(
            sw_return_nc,fraction_nc=sw_supply_fraction_nc)
    return_gw_from_sw_nc,return_gw_from_gw_nc=hl.split_flow(
            gw_return_nc,fraction_nc=sw_supply_fraction_nc)
    
    ### split residential supply by sw/gw fraction
    f= 0.6 # residential_sw_supply_fraction
    sw_residential_supply_nc,gw_residential_supply_nc=hl.split_flow(
            residential_supply_nc,fraction=f)
    ### add residential sw/gw supply to sw/gw supply and sw/gw return
    supply_sw=hl.add_flow(
            sw_supply_nc,sw_residential_supply_nc,name='total_sw_supply')
    supply_gw=hl.add_flow(
            gw_supply_nc,gw_residential_supply_nc,name='total_gw_supply')
    
    #assume that residential supply from sw return to sw, from gw return to gw
    return_sw_from_sw=hl.add_flow(
            return_sw_from_sw_nc,sw_residential_supply_nc,name='total_return_sw_from_sw')
    return_gw_from_gw=hl.add_flow(
            return_gw_from_gw_nc,gw_residential_supply_nc,name='total_return_gw_from_gw')
    
    return_sw_from_gw=return_sw_from_gw_nc
    return_gw_from_sw=return_gw_from_sw_nc
    
    return_sw=hl.add_flow(
            return_sw_from_gw,
            return_sw_from_sw,
            name='return_sw')