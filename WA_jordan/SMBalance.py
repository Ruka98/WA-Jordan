import os
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from netCDF4 import Dataset
import numpy as np
from osgeo import gdal

# Add custom module paths (ensure these modules are in your working directory)
import sys
sys.path.append('WA_jordan')
import createNC_cmi  # Custom module for NetCDF creation
import pre_proc_sm_balance  # Custom module for rainy days calculation
from WA.model_SMBalance import run_SMBalance
from WAsheets import calculate_flux as caf
from WAsheets import hydroloop as hl
from WAsheets import model_hydroloop as mhl


class SMBalanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Soil Moisture Balance Tool")
        self.geometry("800x600")
        
        # Create widgets
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Thread control
        self.running = False

    def create_widgets(self):
        # Create main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # NC Files selection
        ttk.Label(main_frame, text="NetCDF Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.nc_files_text = scrolledtext.ScrolledText(main_frame, height=4, wrap=tk.WORD)
        self.nc_files_text.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=2)
        ttk.Button(main_frame, text="Browse", command=self.select_nc_directory).grid(row=0, column=3, padx=5)

        # Start Year
        ttk.Label(main_frame, text="Start Year:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.start_year_entry = ttk.Entry(main_frame)
        self.start_year_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)

        # End Year
        ttk.Label(main_frame, text="End Year:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.end_year_entry = ttk.Entry(main_frame)
        self.end_year_entry.grid(row=2, column=1, sticky=tk.EW, pady=2)

        # Save Location
        ttk.Label(main_frame, text="Save Location:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.save_location_entry = ttk.Entry(main_frame)
        self.save_location_entry.grid(row=3, column=1, sticky=tk.EW, pady=2)
        ttk.Button(main_frame, text="Browse", command=self.select_save_location).grid(row=3, column=3, padx=5)

        # Run Button
        self.run_button = ttk.Button(main_frame, text="Run Analysis", command=self.run_sm_balance)
        self.run_button.grid(row=4, column=1, pady=10)

        # Status Log
        ttk.Label(main_frame, text="Status Log:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.status_log = scrolledtext.ScrolledText(main_frame, height=10, wrap=tk.WORD)
        self.status_log.grid(row=5, column=1, columnspan=3, sticky=tk.EW, pady=2)

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

    def select_nc_directory(self):
        directory = filedialog.askdirectory(title="Select Directory Containing NetCDF Files")
        if directory:
            self.nc_files_text.delete(1.0, tk.END)
            nc_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.nc')]
            if nc_files:
                self.nc_files_text.insert(tk.END, "\n".join(nc_files))
            else:
                messagebox.showwarning("No NetCDF Files", "No .nc files found in the selected directory.")

    def select_save_location(self):
        directory = filedialog.askdirectory(title="Select Save Location")
        if directory:
            self.save_location_entry.delete(0, tk.END)
            self.save_location_entry.insert(0, directory)

    def validate_inputs(self):
        nc_files = self.nc_files_text.get(1.0, tk.END).strip().split("\n")
        save_location = self.save_location_entry.get().strip()
        start_year = self.start_year_entry.get().strip()
        end_year = self.end_year_entry.get().strip()

        if not nc_files or not all(os.path.isfile(f) for f in nc_files):
            messagebox.showerror("Error", "Please select a directory containing valid NetCDF files")
            return False

        if not save_location:
            messagebox.showerror("Error", "Please select a save location")
            return False

        try:
            start_year = int(start_year)
            end_year = int(end_year)
            if start_year > end_year:
                messagebox.showerror("Error", "Start year must be less than or equal to end year")
                return False
        except ValueError:
            messagebox.showerror("Error", "Please enter valid year numbers")
            return False

        return True

    def run_sm_balance(self):
        if not self.validate_inputs():
            return

        self.running = True
        self.run_button.config(state=tk.DISABLED)
        self.status_log.delete(1.0, tk.END)
        self.status_log.insert(tk.END, "Starting analysis...\n")

        # Get parameters from GUI
        nc_files = self.nc_files_text.get(1.0, tk.END).strip().split("\n")
        save_location = self.save_location_entry.get().strip()
        start_year = int(self.start_year_entry.get().strip())
        end_year = int(self.end_year_entry.get().strip())

        # Mapping from quantity in filenames to required keys
        quantity_to_key = {
            '_P_': 'P',       # Precipitation
            '_I_': 'I',       # Infiltration
            '_NRD_': 'NRD',   # Number of Rainy Days
            '_LU_': 'LU',     # Land Use
            '_ETa_': 'ET',     # Evapotranspiration
            '_SMsat_': 'SMsat',  # Saturated Soil Moisture
            '_Aridity_': 'Ari'    # Aridity Index
        }

        # Map files based on quantity in filename
        nc_files_dict = {}
        for file_path in nc_files:
            file_name = os.path.basename(file_path)
            self.log_message(f"Processing file: {file_name}")
            matched = False
            for pattern, key in quantity_to_key.items():
                if pattern in file_name:
                    nc_files_dict[key] = file_path
                    self.log_message(f"Mapped '{pattern}' to key '{key}' for file {file_name}")
                    matched = True
                    break
            if not matched:
                self.log_message(f"Unrecognized pattern in file {file_name}")

        # Check if all required keys are present
        required_keys = ['P', 'ET', 'I', 'NRD', 'LU', 'SMsat', 'Ari']
        missing_keys = [key for key in required_keys if key not in nc_files_dict]
        if missing_keys:
            self.log_message(f"Error: Missing required NetCDF files for keys: {missing_keys}")
            messagebox.showerror("Error", f"Missing required NetCDF files for keys: {missing_keys}")
            self.running = False
            self.run_button.config(state=tk.NORMAL)
            return

        # Fixed parameters
        params = {
            'f_perc': 0.9,
            'f_Smax': 0.818,
            'cf': 50,
            'f_bf': 0.095,
            'deep_perc_f': 0.905,
            'root_depth_version': '1.0',
            'chunks': [1, 100, 100]
        }

        # Start processing thread
        processing_thread = threading.Thread(
            target=self.process_data,
            args=(nc_files_dict, save_location, start_year, end_year, params),
            daemon=True
        )
        processing_thread.start()

    def process_data(self, nc_files, save_location, start_year, end_year, params):
        try:
            Tstart = time.time()
            self.log_message("Processing started...")
            
            # Debugging: Log the parameters being passed
            self.log_message(f"Parameters: {params}")
            self.log_message(f"NC Files: {nc_files}")
            self.log_message(f"Save Location: {save_location}")
            self.log_message(f"Start Year: {start_year}, End Year: {end_year}")

            # Ensure 'chunks' is a list of integers
            if isinstance(params['chunks'], list):
                params['chunks'] = [int(x) for x in params['chunks']]
            else:
                raise ValueError("'chunks' parameter must be a list of integers")

            # Run the main analysis
            nc_files_output = run_SMBalance(
                save_location,
                nc_files,
                start_year,
                end_year,
                params['f_perc'],
                params['f_Smax'],
                params['cf'],
                params['f_bf'],
                params['deep_perc_f'],
                params['root_depth_version'],
                params['chunks']
            )

            Tend = time.time()
            self.log_message(f"Processing completed in {Tend - Tstart:.2f} seconds")
            messagebox.showinfo("Success", "Analysis completed successfully!")

        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.log_message(f"Error details: {repr(e)}")  # Print detailed error information
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.running = False
            self.run_button.config(state=tk.NORMAL)

    def log_message(self, message):
        self.status_log.insert(tk.END, message + "\n")
        self.status_log.see(tk.END)
        self.update_idletasks()

    def on_close(self):
        if self.running:
            if messagebox.askokcancel("Quit", "Analysis is running! Are you sure you want to quit?"):
                self.destroy()
        else:
            self.destroy()


if __name__ == "__main__":
    app = SMBalanceApp()
    app.mainloop()