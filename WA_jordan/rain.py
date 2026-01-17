import os
import sys
import numpy as np
from netCDF4 import Dataset

def calculate_rainy_days(daily_precip_nc):
    """
    Calculate the number of rainy days per month.
    A rainy day is defined as a day with precipitation > 0.1 mm.
    """
    with Dataset(daily_precip_nc, 'r') as daily_nc:
        daily_precip = daily_nc.variables['dailyP'][:]
        time = daily_nc.variables['time'][:]
        lat = daily_nc.variables['latitude'][:]
        lon = daily_nc.variables['longitude'][:]
        
        # Calculate rainy days directly
        rainy_days = np.sum(daily_precip > 0.1, axis=0)
        
        return rainy_days, lat, lon, time

def calculate_interception(lai_nc, monthly_precip_nc):
    """
    Calculate interception using LAI and monthly precipitation.
    Interception is calculated as: I = LAI * P * 0.2
    """
    with Dataset(lai_nc, 'r') as lai_nc, Dataset(monthly_precip_nc, 'r') as monthly_nc:
        lai = lai_nc.variables['LAI'][:]
        monthly_precip = monthly_nc.variables['P'][:]
        
        # Calculate interception
        interception = lai * monthly_precip * 0.2
        
        return interception

def save_results(output_dir, rainy_days, interception, lat, lon, time, name="Amman_zarqa"):
    """
    Save the calculated rainy days and interception as NetCDF files.
    """
    rainy_days_nc = os.path.join(output_dir, f"{name}_NRD_CHIRPS.nc")
    with Dataset(rainy_days_nc, 'w') as nc:
        nc.createDimension('time', len(time))
        nc.createDimension('latitude', len(lat))
        nc.createDimension('longitude', len(lon))

        nc.createVariable('time', 'f4', ('time',))[:] = time
        nc.createVariable('latitude', 'f4', ('latitude',))[:] = lat
        nc.createVariable('longitude', 'f4', ('longitude',))[:] = lon

        nrd_var = nc.createVariable('NRD', 'f4', ('time', 'latitude', 'longitude'))
        nrd_var.units = "days/month"
        nrd_var.source = "CHIRPS"
        nrd_var.description = "Number of Rainy Days"
        nrd_var[:] = rainy_days

    interception_nc = os.path.join(output_dir, f"{name}_I_CHIRPS_MOD15.nc")
    with Dataset(interception_nc, 'w') as nc:
        nc.createDimension('time', len(time))
        nc.createDimension('latitude', len(lat))
        nc.createDimension('longitude', len(lon))

        nc.createVariable('time', 'f4', ('time',))[:] = time
        nc.createVariable('latitude', 'f4', ('latitude',))[:] = lat
        nc.createVariable('longitude', 'f4', ('longitude',))[:] = lon

        i_var = nc.createVariable('I', 'f4', ('time', 'latitude', 'longitude'))
        i_var.units = "mm/month"
        i_var.source = "CHIRPS_MOD15"
        i_var.description = "Interception"
        i_var[:] = interception

def main(output_dir):
    """
    Main function to calculate rainy days and interception.
    """
    daily_precip_nc = os.path.join(output_dir, "Amman_zarqa_dailyP_CHIRPS.nc")
    monthly_precip_nc = os.path.join(output_dir, "Amman_zarqa_P_CHIRPS.nc")
    lai_nc = os.path.join(output_dir, "Amman_zarqa_LAI_MOD15.nc")

    if not all(os.path.exists(f) for f in [daily_precip_nc, monthly_precip_nc, lai_nc]):
        print("Error: Missing input NetCDF files.")
        sys.exit(1)

    print("Calculating rainy days...")
    rainy_days, lat, lon, time = calculate_rainy_days(daily_precip_nc)

    print("Calculating interception...")
    interception = calculate_interception(lai_nc, monthly_precip_nc)

    print("Saving results...")
    save_results(output_dir, rainy_days, interception, lat, lon, time)

    print("Process completed successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rain.py <output_directory>")
        sys.exit(1)

    output_dir = sys.argv[1]
    if not os.path.isdir(output_dir):
        print(f"Error: {output_dir} is not a valid directory.")
        sys.exit(1)

    main(output_dir)
