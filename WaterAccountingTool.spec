# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('resources', 'resources'), ('proj-data', 'proj-data'), ('gdal-data', 'gdal-data'), ('WA_jordan', 'WA_jordan'), ('app_backend.py', '.'), ('ui_pages.py', '.')]
datas += collect_data_files('distributed')
datas += collect_data_files('dask')


a = Analysis(
    ['main_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['dask', 'distributed', 'cairosvg', 'osgeo', 'osr', 'ogr', 'svglib.svglib', 'svg2rlg', 'reportlab.graphics', 'renderPDF', 'gdal', 'geopy.distance', 'fiona', 'geopy', 'matplotlib', 'netCDF4', 'numpy', 'pandas', 'pillow', 'rasterio', 'scipy', 'xarray', 'tqdm', 'shapely', 'sklearn', 'IPython', 'pdf2image', 'h5py', 'h5netcdf'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WaterAccountingTool',
)
