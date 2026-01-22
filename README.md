# Water Accounting Analysis Tool

The Water Accounting Analysis Tool is a comprehensive desktop application designed to assist in water accounting analysis, specifically tailored for the Jordan context (`WA_jordan`). It provides a user-friendly interface to process hydrological data, run models, and generate water accounting sheets (Sheet 1 and Sheet 2).

## Features

*   **NetCDF Creation**: Converts input raster data (TIFF) into NetCDF format suitable for analysis.
*   **Rain Interception Calculation**: Computes rainfall interception based on daily precipitation and LAI.
*   **Soil Moisture Balance (SMBalance)**: Runs soil moisture balance models to estimate parameters like infiltration, runoff, and deep percolation.
*   **Hydroloop Model**: Initializes and runs the Hydroloop model to simulate water flows and stocks within a basin.
*   **Sheet Generation**: Automatically generates Water Accounting Sheet 1 and Sheet 2 in CSV and PDF formats.
*   **Workflow Management**: Supports a full end-to-end workflow or individual module execution.
*   **Progress Tracking**: Real-time logging and progress bars for long-running tasks.

## Requirements

The application is built using Python 3 and relies on several scientific and geospatial libraries. Key dependencies include:

*   **Python 3.8+**
*   **GUI**: `PyQt5`
*   **Geospatial**: `gdal` (osgeo), `rasterio`, `fiona`, `shapely`, `geopy`, `proj`
*   **Data Analysis**: `numpy`, `pandas`, `xarray`, `netCDF4`, `scipy`, `dask`, `distributed`, `h5netcdf`
*   **Visualization/Reporting**: `matplotlib`, `cairosvg`, `svglib`, `reportlab`
*   **Others**: `pyshp` (shapefile), `pillow`, `tqdm`

## Installation

It is recommended to use **Conda** to manage the environment, especially for geospatial dependencies like GDAL.

```bash
conda create -n wa_tool python=3.9
conda activate wa_tool
conda install -c conda-forge gdal rasterio fiona shapely xarray netcdf4 dask distributed numpy pandas scipy matplotlib pyqt
pip install simpledbf svglib reportlab cairosvg geopy pyshp
```

*Note: You may need to ensure `gdal-data` and `proj-data` are correctly set up in your environment variables if not handled automatically.*

## Usage

### Running from Source

To run the application directly from the source code:

1.  Activate your environment:
    ```bash
    conda activate wa_tool
    ```
2.  Run the main application script:
    ```bash
    python main_app.py
    ```

### Building the Executable

The application can be packaged into a standalone executable using `PyInstaller`. A `.spec` file is provided.

1.  Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```
2.  Run the build command:
    ```bash
    pyinstaller --noconfirm --clean WaterAccountingTool.spec
    ```
3.  The executable will be generated in the `dist/WaterAccountingTool` directory.

## Directory Structure

*   `main_app.py`: The entry point of the application and main GUI logic.
*   `app_backend.py`: Handles background processing and communication with scientific modules.
*   `ui_pages.py`: Defines the layout and logic for the various UI pages.
*   `WA_jordan/`: Contains the core scientific modules and algorithms.
*   `resources/`: Images and icons used in the GUI.
*   `gdal-data/` & `proj-data/`: Required data files for geospatial libraries.

## License

This project is licensed under the terms described in the `LICENSE.txt` file.
