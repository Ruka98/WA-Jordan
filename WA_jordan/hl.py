import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import time
import threading
import traceback
from uuid import uuid4
import xarray as xr
import numpy as np

# Function to get resource path for PyInstaller
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# Set up path for custom modules
wa_jordan_path = resource_path('WA_jordan')
sys.path.append(wa_jordan_path)

# Import required modules
try:
    from WAsheets import model_hydroloop as mhl
    from WAsheets import calculate_flux as cf
    from WAsheets import hydroloop as hl
except ImportError:
    print(f"Could not import WAsheets modules. Ensure WA_jordan folder is in {wa_jordan_path}")
    sys.exit(1)

class HydroloopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hydroloop Processor")
        self.root.geometry("900x800")
        
        # Initialize variables
        self.inputs = {
            'nc_dir': tk.StringVar(),
            'static_data_dir': tk.StringVar(),
            'result_dir': tk.StringVar(),
            'mask_path': tk.StringVar(),
            'dem_path': tk.StringVar(),
            'aeisw_path': tk.StringVar(),
            'population_path': tk.StringVar(),
            'wpl_path': tk.StringVar(),
            'ewr_path': tk.StringVar(),
            'basin_name': tk.StringVar(value="Amman_zarqa"),
            'inflow': tk.StringVar(value="AZ_Imports_2019_2022.csv"),
            'outflow': tk.StringVar(value="AZ_Outflow_2019_2022.csv"),
            'consumption': tk.StringVar(value="AZ_Total_water_Consumption_2019_2022.csv"),
            'tww': tk.StringVar(value="AZ_Total_TWW_2019_2022.csv"),
            'hydro_year': tk.IntVar(value=10),
            'unit_conversion': tk.DoubleVar(value=1e3)
        }
        
        self.result_status = tk.StringVar(value="Ready to process")
        self.BASIN = None
        self.current_input_index = 0
        self.current_process_step = 0
        self.processing_complete = False
        self.nc_time_dims = {}  # Store time dimensions for validation
        
        self.input_fields = [
            ('nc_dir', "NetCDF Files Directory", True),
            ('static_data_dir', "Static Data Directory", True),
            ('result_dir', "Results Directory", True),
            ('mask_path', "Basin Mask File", True),
            ('dem_path', "DEM File", True),
            ('aeisw_path', "AEISW File", True),
            ('population_path', "Population File", True),
            ('wpl_path', "WPL File", True),
            ('ewr_path', "Environmental Water Requirement File", True),
            ('basin_name', "Basin Name", False),
            ('inflow', "Inflow File", False),
            ('outflow', "Outflow File", False),
            ('consumption', "Total Water Consumption File", False),
            ('tww', "Treated Waste Water File", False),
            ('hydro_year', "Hydro Year End Month", False),
            ('unit_conversion', "Unit Conversion Factor", False)
        ]
        
        # Define processing steps
        self.process_steps = [
            ('resample_lu', "Resample Land Use", self.run_resample_lu),
            ('split_et', "Split ET", self.run_split_et),
            ('split_supply', "Split Supply", self.run_split_supply),
            ('calc_demand', "Calculate Demand", self.run_calc_demand),
            ('calc_return', "Calculate Return", self.run_calc_return),
            ('calc_residential_supply', "Calculate Residential Supply", self.run_calc_residential_supply),
            ('calc_total_supply', "Calculate Total Supply", self.run_calc_total_supply),
            ('calc_fraction', "Calculate Fraction", self.run_calc_fraction),
            ('calc_time_series', "Calculate Time Series", self.run_calc_time_series)
        ]
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_tab = ttk.Frame(self.notebook)
        self.process_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.setup_tab, text="Setup")
        self.notebook.add(self.process_tab, text="Process")
        self.notebook.add(self.log_tab, text="Log")
        
        # Setup tab contents
        self.create_setup_tab()
        
        # Process tab contents
        self.create_process_tab()
        
        # Log tab contents
        self.create_log_tab()
        
        # Disable process tab initially
        self.notebook.tab(1, state="disabled")
        
    def create_setup_tab(self):
        main_frame = ttk.Frame(self.setup_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding="10")
        self.input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        canvas = tk.Canvas(self.input_frame)
        scrollbar = ttk.Scrollbar(self.input_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for i, (key, label, is_file) in enumerate(self.input_fields):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=f"{label}:", width=25).pack(side=tk.LEFT, padx=5)
            
            if key == 'hydro_year':
                ttk.Spinbox(frame, from_=1, to=12, textvariable=self.inputs[key], width=10).pack(side=tk.LEFT)
            elif key == 'unit_conversion':
                ttk.Entry(frame, textvariable=self.inputs[key], width=15).pack(side=tk.LEFT, padx=5)
            else:
                ttk.Entry(frame, textvariable=self.inputs[key], width=50).pack(side=tk.LEFT, padx=5)
                
                if is_file:
                    ttk.Button(frame, text="Browse", command=lambda k=key: self.browse_file(k)).pack(side=tk.LEFT)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Cleanup Processed Files", 
                  command=self.cleanup_resampled_files).pack(side=tk.LEFT, padx=5)
        
        self.init_button = ttk.Button(button_frame, text="Initialize Hydroloop", 
                                     command=self.initialize_hydroloop)
        self.init_button.pack(side=tk.RIGHT, padx=5)
        
    def create_process_tab(self):
        main_frame = ttk.Frame(self.process_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        process_frame = ttk.LabelFrame(main_frame, text="Processing Steps", padding="10")
        process_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        canvas = tk.Canvas(process_frame)
        scrollbar = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.process_buttons = {}
        self.progress_bars = {}
        
        for key, label, _ in self.process_steps:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=f"{label}:", width=25).pack(side=tk.LEFT, padx=5)
            
            button = ttk.Button(frame, text="Run", command=lambda k=key: self.run_process_step(k))
            button.pack(side=tk.LEFT, padx=5)
            self.process_buttons[key] = button
            
            progress = ttk.Progressbar(frame, length=200, mode='indeterminate')
            progress.pack(side=tk.LEFT, padx=5)
            self.progress_bars[key] = progress
    
    def create_log_tab(self):
        log_frame = ttk.Frame(self.log_tab, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=20, width=80, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        save_frame = ttk.Frame(self.log_tab)
        save_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(save_frame, text="Save Log", command=self.save_log).pack(side=tk.RIGHT, padx=10)
        
    def save_log(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, "w") as file:
                file.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Log saved to {filename}")
    
    def browse_file(self, key):
        if key in ['nc_dir', 'static_data_dir', 'result_dir']:
            directory = filedialog.askdirectory(title=f"Select {next((label for k, label, _ in self.input_fields if k == key), '')}")
            if directory:
                self.inputs[key].set(directory)
        else:
            filename = filedialog.askopenfilename(title=f"Select {next((label for k, label, _ in self.input_fields if k == key), '')}")
            if filename:
                self.inputs[key].set(filename)
    
    def log(self, message):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def validate_inputs(self):
        for key, label, is_file in self.input_fields:
            value = self.inputs[key].get()
            
            if is_file and not value:
                messagebox.showerror("Error", f"Please select {label}")
                return False
                
            if is_file and value and not os.path.exists(value):
                messagebox.showerror("Error", f"{label} does not exist")
                return False
                
            if key == 'hydro_year' and not 1 <= self.inputs[key].get() <= 12:
                messagebox.showerror("Error", "Hydro year end month must be between 1 and 12")
                return False
                
            if key == 'unit_conversion' and self.inputs[key].get() <= 0:
                messagebox.showerror("Error", "Unit conversion factor must be positive")
                return False
        
        if not os.path.exists(self.inputs['result_dir'].get()):
            try:
                os.makedirs(self.inputs['result_dir'].get())
                self.log(f"Created results directory: {self.inputs['result_dir'].get()}")
            except Exception as ex:
                messagebox.showerror("Error", f"Could not create results directory: {str(ex)}")
                return False
        
        for csv_key in ['inflow', 'outflow', 'consumption', 'tww']:
            csv_file = os.path.join(self.inputs['static_data_dir'].get(), self.inputs[csv_key].get())
            if not os.path.exists(csv_file):
                messagebox.showerror("Error", f"File not found: {csv_file}")
                return False
        
        return True
    
    def collect_nc_files(self):
        nc_files = {}
        self.nc_time_dims = {}  # Reset time dimensions
        nc_dir = self.inputs['nc_dir'].get()
        if not os.path.exists(nc_dir):
            self.log(f"NetCDF directory does not exist: {nc_dir}")
            return {}
        
        for filename in os.listdir(nc_dir):
            if filename.endswith('.nc'):
                full_path = os.path.join(nc_dir, filename)
                try:
                    with xr.open_dataset(full_path) as ds:
                        time_dim = ds.sizes.get('time', None)
                        self.nc_time_dims[filename] = time_dim
                        self.log(f"NC file {filename}: time dimension = {time_dim}")
                except Exception as e:
                    self.log(f"Error reading {filename}: {str(e)}")
                    continue
                
                if 'ETa_V6' in filename:
                    nc_files['ET'] = full_path
                    self.log(f"Found NC file for ET: {filename}")
                elif 'P_CHIRPS' in filename and 'dailyP' not in filename:
                    nc_files['P'] = full_path
                    self.log(f"Found NC file for P: {filename}")
                elif 'ETref' in filename:
                    nc_files['ETref'] = full_path
                    self.log(f"Found NC file for ETref: {filename}")
                elif 'LAI' in filename:
                    nc_files['LAI'] = full_path
                    self.log(f"Found NC file for LAI: {filename}")
                elif 'LU_WA_resampled_monthly' in filename:
                    nc_files['LU'] = full_path
                    self.log(f"Found NC file for LU (pre-resampled): {filename}")
                elif 'LU' in filename:
                    if 'LU' not in nc_files:
                        nc_files['LU'] = full_path
                        self.log(f"Found NC file for LU: {filename}")
                elif 'NDM' in filename:
                    nc_files['ProbaV'] = full_path
                    self.log(f"Found NC file for ProbaV: {filename}")
                elif 'i_monthly' in filename:
                    nc_files['I'] = full_path
                    self.log(f"Found NC file for I: {filename}")
                elif 'nRD' in filename:
                    nc_files['NRD'] = full_path
                    self.log(f"Found NC file for NRD: {filename}")
                elif 'bf_monthly' in filename:
                    nc_files['BF'] = full_path
                    self.log(f"Found NC file for BF: {filename}")
                elif 'supply_monthly' in filename:
                    nc_files['Supply'] = full_path
                    self.log(f"Found NC file for Supply: {filename}")
                elif 'etincr_monthly' in filename:
                    nc_files['ETB'] = full_path
                    self.log(f"Found NC file for ETB: {filename}")
                elif 'etrain_monthly' in filename:
                    nc_files['ETG'] = full_path
                    self.log(f"Found NC file for ETG: {filename}")
                elif 'sro_monthly' in filename and 'd_sro_monthly' not in filename:
                    nc_files['SRO'] = full_path
                    self.log(f"Found NC file for SRO: {filename}")
                elif 'perco_monthly' in filename and 'd_perco_monthly' not in filename:
                    nc_files['PERC'] = full_path
                    self.log(f"Found NC file for PERC: {filename}")
                elif 'd_sro_monthly' in filename:
                    nc_files['ISRO'] = full_path
                    self.log(f"Found NC file for ISRO: {filename}")
                elif 'd_perco_monthly' in filename:
                    nc_files['DPERC'] = full_path
                    self.log(f"Found NC file for DPERC: {filename}")
        
        required_vars = ['P', 'ET', 'ETref', 'I', 'NRD', 'ProbaV', 'LU', 'SRO', 'PERC', 'BF', 'Supply', 'ETB', 'ETG', 'LAI']
        optional_vars = ['ISRO', 'DPERC']
        
        missing_required = [var for var in required_vars if var not in nc_files]
        if missing_required:
            error_msg = f"Missing required NC files: {', '.join(missing_required)}"
            self.log(f"Error: {error_msg}")
            return {}
        
        for var in optional_vars:
            if var not in nc_files:
                nc_files[var] = None
                self.log(f"Optional NC file {var} not found, set to None")
        
        monthly_vars = ['P', 'ET', 'ETref', 'I', 'ProbaV', 'SRO', ' PERC', 'BF', 'Supply', 'ETB', 'ETG', 'LAI']
        time_dims = {}
        for var in monthly_vars:
            if var in nc_files and nc_files[var]:
                filename = os.path.basename(nc_files[var])
                time_dims[var] = self.nc_time_dims.get(filename, None)
        
        monthly_time_dims = [td for td in time_dims.values() if td is not None]
        if monthly_time_dims and not all(td == monthly_time_dims[0] for td in monthly_time_dims):
            error_msg = f"Inconsistent time dimensions for monthly variables: {time_dims}"
            self.log(f"Error: {error_msg}")
            return {}
        
        lu_file = os.path.basename(nc_files.get('LU', ''))
        lu_time = self.nc_time_dims.get(lu_file, None)
        expected_monthly = monthly_time_dims[0] if monthly_time_dims else 48
        if lu_time not in [None, 4, expected_monthly]:
            error_msg = f"LU time dimension ({lu_time}) incompatible with monthly data ({expected_monthly})"
            self.log(f"Error: {error_msg}")
            return {}
        
        nrd_file = os.path.basename(nc_files.get('NRD', ''))
        nrd_time = self.nc_time_dims.get(nrd_file, None)
        if nrd_time not in [None, 1461, expected_monthly]:
            error_msg = f"NRD time dimension ({nrd_time}) incompatible with expected daily (1461) or monthly ({expected_monthly})"
            self.log(f"Error: {error_msg}")
            return {}
        
        return nc_files
    
    def cleanup_resampled_files(self):
        if not os.path.exists(self.inputs['result_dir'].get()):
            self.log("Results directory doesn't exist")
            return
        
        try:
            result_dir = self.inputs['result_dir'].get()
            files_to_check = [
                'LU_WA_resampled_monthly.nc',
                'ETa_Incremental.nc',
                'ETa_Green.nc'
            ]
            
            found_files = []
            for file in files_to_check:
                file_path = os.path.join(result_dir, file)
                if os.path.exists(file_path):
                    found_files.append(file)
            
            if found_files:
                message = f"Found {len(found_files)} existing processed files that may cause conflicts:\n"
                message += "\n".join(found_files)
                message += "\n\nDo you want to delete these files?"
                
                if messagebox.askyesno("Clean up files", message):
                    for file in files_to_check:
                        file_path = os.path.join(result_dir, file)
                        try:
                            os.remove(file_path)
                            self.log(f"Deleted file: {file}")
                        except Exception as e:
                            self.log(f"Failed to delete {file}: {str(e)}")
                    self.log("Cleanup completed")
                else:
                    self.log("Cleanup cancelled")
            else:
                self.log("No processed files found to clean up")
        
        except Exception as e:
            self.log(f"Error during cleanup: {str(e)}")
    
    def initialize_hydroloop(self):
        if not self.validate_inputs():
            return
        
        self.result_status.set("Initializing hydroloop...")
        self.init_button.config(state=tk.DISABLED)
        
        threading.Thread(target=self._initialize_hydroloop_thread, daemon=True).start()
    
    def _initialize_hydroloop_thread(self):
        try:
            start_time = time.time()
            self.log("Starting initialization...")
            
            nc_files = self.collect_nc_files()
            if not nc_files:
                error_msg = "No valid NetCDF files found or time dimensions are inconsistent"
                self.log(f"Error: {error_msg}")
                self.root.after(0, lambda: self._handle_error(error_msg))
                return
            
            table_data = mhl.collect_tables(
                self.inputs['static_data_dir'].get(),
                self.inputs['inflow'].get(),
                self.inputs['outflow'].get(),
                self.inputs['consumption'].get(),
                self.inputs['tww'].get()
            )
            self.log("Table data collected successfully")
            
            metadata = mhl.create_metadata(
                basin_name=self.inputs['basin_name'].get(),
                hydro_year=int(self.inputs['hydro_year'].get()),
                output_folder=self.inputs['result_dir'].get(),
                basin_mask=self.inputs['mask_path'].get(),
                dem=self.inputs['dem_path'].get(),
                aeisw=self.inputs['aeisw_path'].get(),
                population=self.inputs['population_path'].get(),
                wpl=self.inputs['wpl_path'].get(),
                environ_water_req=self.inputs['ewr_path'].get(),
                unit_conversion=float(self.inputs['unit_conversion'].get()),
                chunksize=[1, 300, 300]
            )
            
            self.log(f"Initializing with metadata: {metadata}")
            self.log(f"NC files found: {list(nc_files.keys())}")
            
            self.log("Initializing hydroloop...")
            self.BASIN = mhl.initialize_hydroloop(metadata, nc_files, table_data)
            self.log("Hydroloop initialized successfully")
            
            end_time = time.time()
            self.log(f"Initialization completed in {end_time - start_time:.2f} seconds")
            
            self.root.after(0, self._initialization_complete)
            
        except Exception as ex:
            error_details = traceback.format_exc()
            error_msg = f"Initialization failed: {str(ex)}\n\nDetails:\n{error_details}"
            self.log(f"Error: {error_msg}")
            self.root.after(0, lambda: self._handle_error(error_msg))
    
    def _initialization_complete(self):
        self.result_status.set("Initialization completed successfully. Ready for processing.")
        self.init_button.config(state=tk.NORMAL)
        self.notebook.tab(1, state="normal")
        self.notebook.select(1)
        messagebox.showinfo("Successrzew", "Hydroloop has been initialized successfully. You can now proceed with processing steps.")
    
    def _handle_error(self, message):
        self.result_status.set("Error occurred")
        self.init_button.config(state=tk.NORMAL)
        messagebox.showerror("Error", message)
    
    def run_process_step(self, step_key):
        if self.BASIN is None:
            messagebox.showerror("Error", "Hydroloop not initialized. Please initialize first.")
            return
        
        # Find the processing function
        for key, _, func in self.process_steps:
            if key == step_key:
                self.process_buttons[step_key].config(state=tk.DISABLED)
                self.progress_bars[step_key].start()
                threading.Thread(target=self._run_process_step_thread, args=(step_key, func), daemon=True).start()
                break
    
    def _run_process_step_thread(self, step_key, process_func):
        try:
            start_time = time.time()
            self.log(f"Starting {step_key}...")
            
            # Run the processing step
            self.BASIN = process_func(self.BASIN)
            
            end_time = time.time()
            self.log(f"{step_key} completed in {end_time - start_time:.2f} seconds")
            
            self.root.after(0, lambda: self._process_step_complete(step_key))
            
        except Exception as ex:
            error_details = traceback.format_exc()
            error_msg = f"{step_key} failed: {str(ex)}\n\nDetails:\n{error_details}"
            self.log(f"Error: {error_msg}")
            self.root.after(0, lambda: self._process_step_error(step_key, error_msg))
    
    def _process_step_complete(self, step_key):
        self.progress_bars[step_key].stop()
        self.process_buttons[step_key].config(state=tk.NORMAL)
        self.result_status.set(f"{step_key} completed successfully")
        messagebox.showinfo("Success", f"{step_key} completed successfully")
    
    def _process_step_error(self, step_key, message):
        self.progress_bars[step_key].stop()
        self.process_buttons[step_key].config(state=tk.NORMAL)
        self.result_status.set(f"Error in {step_key}")
        messagebox.showerror("Error", message)
    
    def run_resample_lu(self, basin):
        try:
            # Validate time dimensions before resampling
            nc_files = self.collect_nc_files()
            lu_file = nc_files.get('LU', '')
            if not lu_file:
                raise ValueError("No LU file found in NetCDF files")
            
            expected_monthly = 48  # Expected time dimension for monthly data (4 years)
            with xr.open_dataset(lu_file) as ds:
                lu_time = ds.sizes.get('time', 1)
                self.log(f"LU dataset time dimension: {lu_time}")
            
            # Get a sample monthly dataset for time alignment
            sample_file = nc_files.get('P', '')  # Use precipitation as sample
            if not sample_file:
                raise ValueError("No precipitation file found for time alignment")
            
            with xr.open_dataset(sample_file) as ds:
                sample_time = ds.sizes.get('time', None)
                sample_time_coords = ds['time'].values
                self.log(f"Sample dataset time dimension: {sample_time}")
            
            if sample_time != expected_monthly:
                self.log(f"Warning: Sample time dimension ({sample_time}) does not match expected ({expected_monthly})")
            
            # Attempt original resampling
            basin = mhl.resample_lu(basin)
            
            # Verify the resampled dataset
            resampled_file = os.path.join(self.inputs['result_dir'].get(), 'LU_WA_resampled_monthly.nc')
            if os.path.exists(resampled_file):
                with xr.open_dataset(resampled_file) as ds:
                    resampled_time = ds.sizes.get('time', None)
                    self.log(f"Resampled LU time dimension: {resampled_time}")
                    if resampled_time != expected_monthly:
                        self.log(f"Warning: Resampled time dimension ({resampled_time}) does not match expected ({expected_monthly}). Attempting correction...")
                        # Fallback: Adjust time dimension
                        ds = ds.sel(time=ds['time'][:expected_monthly]).reindex(time=sample_time_coords[:expected_monthly])
                        ds.to_netcdf(resampled_file + '.corrected.nc')
                        self.log(f"Saved corrected resampled file: {resampled_file}.corrected.nc")
                        os.rename(resampled_file + '.corrected.nc', resampled_file)
                        self.log(f"Corrected resampled file replaced original")
            
            return basin
            
        except Exception as e:
            self.log(f"Error in resample_lu: {str(e)}")
            # Fallback resampling method
            try:
                self.log("Attempting fallback resampling...")
                yearly_nc = xr.open_dataset(lu_file)
                sample_nc = xr.open_dataset(sample_file)
                
                # Create a new dataset with the correct time dimension
                monthly_data = yearly_nc.reindex(time=sample_nc['time'][:expected_monthly], method='nearest')
                monthly_data.to_netcdf(os.path.join(self.inputs['result_dir'].get(), 'LU_WA_resampled_monthly.nc'))
                self.log("Fallback resampling completed successfully")
                
                # Reload the basin with the corrected file
                nc_files['LU'] = os.path.join(self.inputs['result_dir'].get(), 'LU_WA_resampled_monthly.nc')
                basin = mhl.initialize_hydroloop(basin.metadata, nc_files, basin.table_data)
                return basin
                
            except Exception as fallback_e:
                raise Exception(f"Fallback resampling failed: {str(fallback_e)}") from e
    
    def run_split_et(self, basin):
        return mhl.split_et(basin)
    
    def run_split_supply(self, basin):
        return mhl.split_supply(basin)
    
    def run_calc_demand(self, basin):
        return mhl.calc_demand(basin)
    
    def run_calc_return(self, basin):
        return mhl.calc_return(basin)
    
    def run_calc_residential_supply(self, basin):
        return mhl.calc_residential_supply(basin)
    
    def run_calc_total_supply(self, basin):
        return mhl.calc_total_supply(basin)
    
    def run_calc_fraction(self, basin):
        return mhl.calc_fraction(basin)
    
    def run_calc_time_series(self, basin):
        return mhl.calc_time_series(basin)

if __name__ == "__main__":
    # Ensure the app can be launched from another executable
    root = tk.Tk()
    app = HydroloopApp(root)
    root.mainloop()