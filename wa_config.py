import os

# Dataset configuration for NetCDF creation
dataset_config = {
    'P': {
        'subdir': os.path.join('P', 'Monthly'),
        'dims': ('time', 'latitude', 'longitude'),
        'attrs': {'units': 'mm/month', 'source': 'CHIRPS', 'quantity': 'P', 'temporal_resolution': 'monthly'}
    },
    'dailyP': {
        'subdir': os.path.join('P', 'Daily'),
        'dims': ('time', 'latitude', 'longitude'),
        'attrs': {'units': 'mm/d', 'source': 'CHIRPS', 'quantity': 'dailyP', 'temporal_resolution': 'daily'}
    },
    'ET': {
        'subdir': 'ET',
        'dims': ('time', 'latitude', 'longitude'),
        'attrs': {'units': 'mm/month', 'source': 'V6', 'quantity': 'ETa', 'temporal_resolution': 'monthly'}
    },
    'LAI': {
        'subdir': 'LAI',
        'dims': ('time', 'latitude', 'longitude'),
        'attrs': {'units': 'None', 'source': 'MOD15', 'quantity': 'LAI', 'temporal_resolution': 'monthly'}
    },
    'SMsat': {
        'subdir': 'ThetaSat',
        'dims': ('time', 'latitude', 'longitude'),
        'attrs': {'units': 'None', 'source': 'HiHydroSoils', 'quantity': 'SMsat', 'temporal_resolution': 'monthly'}
    },
    'Ari': {
        'subdir': 'Aridity',
        'dims': ('time', 'latitude', 'longitude'),
        'attrs': {'units': 'None', 'source': 'CHIRPS_GLEAM', 'quantity': 'Aridity', 'temporal_resolution': 'monthly'}
    },
    'LU': {
        'subdir': 'LUWA',
        'dims': ('time', 'latitude', 'longitude'),
        'attrs': {'units': 'None', 'source': 'WA', 'quantity': 'LU', 'temporal_resolution': 'static'}
    },
    'ProbaV': {
        'subdir': 'NDM',
        'dims': ('time', 'latitude', 'longitude'),
        'attrs': {'units': 'None', 'source': 'ProbaV', 'quantity': 'NDM', 'temporal_resolution': 'monthly'}
    },
    'ETref': {
        'subdir': 'ETref',
        'dims': ('time', 'latitude', 'longitude'),
        'attrs': {'units': 'None', 'source': 'L1_RET', 'quantity': 'ETref', 'temporal_resolution': 'monthly'}
    }
}

# Heuristic patterns for file detection
# Key is the UI entry key, Value is a list of patterns to match (case-insensitive glob)
file_patterns = {
    'shapefile': ['*.shp'],
    'template_mask': ['*template*.tif', '*mask*.tif', '*basin*.tif'],
    'dem_path': ['*dem*.tif', '*elevation*.tif'],
    'aeisw_path': ['*aeisw*.tif', '*actual*evap*.tif'],
    'population_path': ['*pop*.tif', '*population*.tif'],
    'wpl_path': ['*wpl*.tif'],
    'ewr_path': ['*ewr*.*', '*environment*.*'],
    'inflow': ['*inflow*.csv'],
    'outflow': ['*outflow*.csv'],
    'tww': ['*tww*.csv', '*waste*water*.csv'],
    'cw_do': ['*cw_do*.csv', '*consumption*.csv', '*domestic*.csv']
}
