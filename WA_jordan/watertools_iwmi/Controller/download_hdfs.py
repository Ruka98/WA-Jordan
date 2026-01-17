# -*- coding: utf-8 -*-
"""
Created on Fri Aug 12 16:02:26 2022

@author: p.thilina-prabhath
"""


import os
import concurrent.futures as cf
import subprocess
import requests
from watertools_iwmi import Functions as fn

def serverStatus(link):
    username, password = fn.Random.Get_Username_PWD.GET('NASA')
    payload={'username': username,'password': password}
    url = link[:-1]
    r= requests.get(url, data=payload)
    status = r.status_code
    return status
    
def download(fh):
    # print(fh)
    cookies = "/home/iwmi-wa/.urs_cookies"
    cmd = f"curl --silent -O -b {cookies} -c {cookies} -L -n {fh}"    
    # cmd = f"curl -n -c {cookies} -b {cookies} -LJO --url {fh}"
    # cmd = f"wget --load-cookies {cookies} --save-cookies {cookies} --keep-session-cookies {fh}"
    # os.system(cmd)
    subprocess.check_output(cmd, shell=True)
    
def main(Dir, textfile):

    output_folder = os.path.join(Dir, 'hdf')
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    os.chdir(output_folder)
    
    with open(textfile) as f:
        links =   [line for line in f.readlines()]
            
    # status = serverStatus(links[0])    
    connection = False
    status = 200
    if status == 200:  
        
        connection = True        
        amount = 0
        total_amount = len(links)
        
        exector = cf.ThreadPoolExecutor(max_workers=os.cpu_count())
        futures = [exector.submit(download, link[:-1]) for link in links]
        
        for future in cf.as_completed(futures):
            amount += 1
            fn.Random.WaitbarConsole.printWaitBar(amount, total_amount, prefix = 'Progress:', suffix = 'Complete', length = 50)
        
    else:
        print("ERROR: Was not able to connect to NASA server")
        
        
    return output_folder, connection
     
     
    