# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 10:28:31 2020

@author: p.thilina-prabhath
"""


all_ = \
[common_dates,frac,p_advec,q_in_sw,q_in_gw,q_in_desal,\
ds,et,q_outf,q_o_sw,q_out_avg_,gwr,ewr,non_recover,\
    consumed,net,rod,non_consumed]
index=['Date','frace','p_advec','q_in_sw','q_in_gw','q_in_desal','ds','q_outflow',
       'q_out_sw','q_out_avg','gwf','ewr','non_recover','consumed','net','rod',
       'non_consumed']    
all_var = dict()

all_var = {'Date':common_dates,
           'frac':frac,
           'p_advec':p_advec,
           'q_in_sw':q_in_sw,
           'q_in_gw':q_in_gw,
           'q_in_desal':q_in_desal,
           'ds':ds,
           'et':et,
           'q_outflow':q_outf,
           'q_out_sw':q_o_sw,
           'q_out_avg':q_out_avg_,
           'gwr':gwr,
           'ewr':ewr,
           'non_recover':non_recover,
           'consumed':consumed,
           'net':net,
           'rod':rod,
           'non_consumed':non_consumed}

req_var1 = {'Date':common_dates,
           'frac':frac,
           'p_advec':p_advec}

req_var1_ ={
           'q_in_sw':q_in_sw,
           'q_in_gw':q_in_gw,
           'q_in_desal':q_in_desal}

req_var2 = {
            'Date':common_dates,
           'ds':ds,
           'et':et,
           'q_outflow':q_outf,
           'q_out_sw':q_o_sw,
           'q_out_avg':q_out_avg_}

req_var3 = {
        'Date':common_dates,
           'gwr':gwr,
           'ewr':ewr,
           'non_recover':non_recover,
           'consumed':consumed,
           'net':net}

req_var4 ={
            'Date':common_dates,
            'rod':rod,
           'non_consumed':non_consumed}