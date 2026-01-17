# -*- coding: utf-8 -*-
"""
Created on Fri Aug 12 13:30:16 2022

@author: p.thilina-prabhath
"""

import os
import requests
import concurrent.futures as cf
import watertools_iwmi.Functions.Random.WaitbarConsole as WaitbarConsole


def collect_data(granule):
    links  = []
    x = granule.json()
    data = x['feed']['entry']
    
    for fh in data:
        link = fh['links'][0]['href']
        links.append(link)
    
    return links

def getLinks(args, collection_id, page_size = 2000):
 
    [Dir, product_name, startdate, enddate, latlim, lonlim] = args
    
    output_file = os.path.join(Dir, product_name, 'download_urls.txt')
    bounding_box =  '%d,%d,%d,%d' % (lonlim[0], latlim[0], lonlim[1], latlim[1])
    # bounding_box = '-20,-36,60,38' # lower left longitude, lower left latitude, upper right longitude, upper right latitude.
    # collection_id=C1000000524-LPDAAC_ECS
    url = f'https://cmr.earthdata.nasa.gov/search/granules.json?echo_collection_id={collection_id}&page_size={page_size}&temporal={startdate}T00:00:00Z,{enddate}T23:59:59Z&bounding_box[]={bounding_box}&pretty=true' 
    
    granules = []
    all_links = []
    
    y = requests.get(url)
    total = int(y.headers['CMR-Hits'])        
    
    if total > page_size:
        granules.append(y)  
        iteration = round(total/page_size)
        amount = 1
        total_amount = iteration + 1        
        
        for i in range(iteration):             
            search_after = y.headers['CMR-Search-After']
            y = requests.get(url, headers={"CMR-Search-After": search_after})
            granules.append(y)  
            
            amount += 1
            WaitbarConsole.printWaitBar(amount, total_amount, prefix = 'Progress:', suffix = 'Complete', length = 50)
            
    else:
        granules.append(y)  
        amount = 100
        total_amount = 100
        WaitbarConsole.printWaitBar(amount, total_amount, prefix = 'Progress:', suffix = 'Complete', length = 50)
   
    
    with cf.ThreadPoolExecutor(os.cpu_count()) as executor:
        # send in the tasks
        futures = [executor.submit(collect_data, granule) for granule in granules]
        cf.wait(futures)
                        
        for future in futures:
            all_links.extend(future.result())
            
    with open(output_file, 'w') as f:
        for link in all_links:
            # f.write(f"{link}\n")            
            f.write(str(link) + "\n")
            
    return output_file
                
