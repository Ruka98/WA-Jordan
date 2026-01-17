# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files
import os
import distributed

block_cipher = None

# --- Custom Logic to find distributed.yaml ---
# Ensure distributed.yaml is explicitly included in the correct location
dist_loc = os.path.dirname(distributed.__file__)
dist_yaml_path = os.path.join(dist_loc, 'distributed.yaml')
dist_schema_path = os.path.join(dist_loc, 'distributed-schema.yaml')

# Initialize datas with project specific files
# Using (source, dest) format
datas = [
    ('resources', 'resources'),
    ('proj-data', 'proj-data'),
    ('gdal-data', 'gdal-data'),
    ('WA_jordan', 'WA_jordan'),
    ('app_backend.py', '.'),
    ('ui_pages.py', '.'),
    ('license_page.py', '.'),
    ('LICENSE.txt', '.')
]

# Add distributed config files manually to be safe
if os.path.exists(dist_yaml_path):
    datas.append((dist_yaml_path, 'distributed'))
if os.path.exists(dist_schema_path):
    datas.append((dist_schema_path, 'distributed'))

# --- Collect dependencies ---
# collect_all returns (datas, binaries, hiddenimports)
# We merge them into our lists.

binaries = []
hiddenimports = [
    'shapefile', 'cairosvg', 'osr', 'ogr', 'svglib.svglib', 'svg2rlg',
    'reportlab.graphics', 'renderPDF', 'gdal', 'geopy.distance', 'fiona',
    'geopy', 'matplotlib', 'netCDF4', 'numpy', 'pandas', 'pillow',
    'rasterio', 'scipy', 'xarray', 'tqdm', 'shapely', 'sklearn',
    'tkinter', 'ttk', 'filedialog', 'messagebox', 'scrolledtext',
    'IPython', 'subprocess', 'glob', 'pdf2image', 'h5py', 'h5netcdf'
]

# Collect distributed
tmp_datas, tmp_binaries, tmp_hidden = collect_all('distributed')
datas += tmp_datas
binaries += tmp_binaries
hiddenimports += tmp_hidden

# Collect dask
tmp_datas, tmp_binaries, tmp_hidden = collect_all('dask')
datas += tmp_datas
binaries += tmp_binaries
hiddenimports += tmp_hidden

# Collect osgeo
tmp_datas, tmp_binaries, tmp_hidden = collect_all('osgeo')
datas += tmp_datas
binaries += tmp_binaries
hiddenimports += tmp_hidden


a = Analysis(
    ['main_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WaterAccountingTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WaterAccountingTool',
)
