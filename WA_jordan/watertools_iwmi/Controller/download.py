# -*- coding: utf-8 -*-
"""
Created on Wed Jul 27 14:07:04 2022

@author: p.thilina-prabhath
"""

import os
from watertools_iwmi.Collect import CHIRPS, GPM, MSWEP, RFE, SSEBop, WAPOR, DEM
from watertools_iwmi.Controller import route as Download
from watertools_iwmi.Functions import Calc_NDM
   
class Initialize(object):
  
    def __init__(self, Dir, products, st_date, en_date, latlim, lonlim):

        # ===========run parameters===================
        self.main_dir = Dir
        self.start_date = st_date
        self.end_date = en_date
        self.latlim = latlim
        self.lonlim = lonlim
        self.products_desc = products
        self.pcp = self.products_desc['PCP']
        self.daily = self.pcp[-1]['daily']
        self.monthly = self.pcp[-1]['monthly']
        self.et = self.products_desc['ET']
        self.lulc = self.products_desc['LCC']
        self.lai = self.products_desc['LAI'][0]        
        self.npp = self.products_desc['NPP'][0]
        self.gpp = self.products_desc['GPP'][0]
        self.ndm = self.products_desc['NDM'][0]
        self.dem = self.products_desc['DEM'][0]
        self.cores = os.cpu_count()
        
        self.pcp_dir = os.path.join(self.main_dir, 'PCP')
        self.et_dir = os.path.join(self.main_dir, 'ET')
        # self.lai_dir = os.path.join(self.main_dir, 'LAI')
        self.lcc_dir = os.path.join(self.main_dir, 'LCC')
        self.gpp_dir = os.path.join(self.main_dir, 'GPP')
        self.npp_dir = os.path.join(self.main_dir, 'NPP')
        # self.ndm_dir = os.path.join(self.main_dir, 'NDM')    

    def _PCP(self, parameter):
        
        if parameter == 'CHIRPS':            
            if self.daily:
                CHIRPS.daily(self.pcp_dir, self.start_date, self.end_date, self.latlim, self.lonlim, cores=False)
            if self.monthly:
                CHIRPS.monthly(self.pcp_dir, self.start_date, self.end_date, self.latlim, self.lonlim, cores=False)
        elif parameter == 'MSWEP':
            if self.daily:
                pass
            else:
                pass
        elif parameter == 'RFE':
            if self.daily:
                pass
            else:
                pass
        elif parameter == 'GPM':
            if self.daily:
                pass
            else:
                pass
        else:
            print(f'Currently {parameter} PCP product is not available')
    
    def _ET(self, parameter):
        
        if parameter == 'L1_AETI_M':            
            WAPOR.Get_Layer(self.et_dir, self.start_date, self.end_date, self.latlim, self.lonlim, parameter, cores=self.cores)
            
        elif parameter == 'L1_RET_M':
            WAPOR.Get_Layer(self.et_dir, self.start_date, self.end_date, self.latlim, self.lonlim, parameter, cores=self.cores)
            
        elif parameter == 'MOD16':
            Download.main(self.et_dir, parameter, self.start_date, self.end_date, self.latlim, self.lonlim, time_conversion = True)
            
            
        elif parameter == 'SSEBop':
            pass
        
        else:
            print(f'Currently {parameter} ET product is not available')
       
    def _LAI(self):
        Download.main(self.main_dir, 'LAI', self.start_date, self.end_date, self.latlim, self.lonlim, time_conversion = True)
                
    def _LCC(self, source, parameter):
        if source == 'WAPOR':   
            WAPOR.Get_Layer(self.lcc_dir, self.start_date, self.end_date, self.latlim, self.lonlim, parameter[-1])
    
    def _NPP(self):
        Download.main(self.main_dir, 'NPP', self.start_date, self.end_date, self.latlim, self.lonlim, time_conversion = False)
        
    def _GPP(self):
        Download.main(self.main_dir, 'GPP', self.start_date, self.end_date, self.latlim, self.lonlim, time_conversion = True)
        
    def _NDM(self):        
        Calc_NDM.NPP_GPP_Based(self.main_dir, self.gpp_dir, self.npp_dir, self.start_date, self.end_date)

    def _DEM(self):
        DEM.HydroSHED(self.main_dir, self.latlim, self.lonlim)
        
    def _Download(self):
                    
        if self.pcp[0]:            
            for k, v in self.pcp[1].items():
                if v:
                    self._PCP(k)
                    
        if self.et[0]:            
            for k, v in self.et[-1].items():
                if v:
                    self._ET(k)
                    
        if self.lulc[0]:
            for k, v in self.lulc[-1].items():
                if v[0]:
                    self._LCC(k, v)
            
        if self.lai:            
            self._LAI()
        
        if self.npp:
            self._NPP()
            
        if self.gpp:
            self._GPP()
            
        if self.ndm:
            self._NDM()
            
        if self.dem:
            self._DEM()
        
        
    

            