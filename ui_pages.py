from PyQt5.QtWidgets import (QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
                             QComboBox, QHBoxLayout, QVBoxLayout, QWidget,
                             QSizePolicy, QScrollArea, QFrame, QStackedLayout, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QFont, QIcon
import os
import sys
import subprocess
import glob
import re
from datetime import datetime
from collections import defaultdict

class UIPages:
    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        path = os.path.join(base_path, relative_path)
        
        # For PyInstaller, we need to check if the path exists
        # If not, try the original path (for development)
        if not os.path.exists(path):
            path = os.path.abspath(os.path.join(".", relative_path))
        
        return path
    
    dataset_config = {
        'P': {
            'subdir': os.path.join('P', 'monthly'),
            'attrs': {'units': 'mm/month', 'source': 'CHIRPS', 'quantity': 'P', 'temporal_resolution': 'monthly'},
            'display_name': 'Monthly Precipitation'
        },
        'dailyP': {
            'subdir': os.path.join('P', 'Daily'),
            'attrs': {'units': 'mm/d', 'source': 'CHIRPS', 'quantity': 'dailyP', 'temporal_resolution': 'daily'},
            'display_name': 'Daily Precipitation'
        },
        'ET': {
            'subdir': 'ET',
            'attrs': {'units': 'mm/month', 'source': 'V6', 'quantity': 'ETa', 'temporal_resolution': 'monthly'},
            'display_name': 'Actual Evapotranspiration'
        },
        'LAI': {
            'subdir': 'LAI',
            'attrs': {'units': 'None', 'source': 'MOD15', 'quantity': 'LAI', 'temporal_resolution': 'monthly'},
            'display_name': 'Leaf Area Index'
        },
        'SMsat': {
            'subdir': 'ThetaSat',
            'attrs': {'units': 'None', 'source': 'HiHydroSoils', 'quantity': 'SMsat', 'temporal_resolution': 'monthly'},
            'display_name': 'ThetaSat'
        },
        'Ari': {
            'subdir': 'Aridity',
            'attrs': {'units': 'None', 'source': 'CHIRPS_GLEAM', 'quantity': 'Aridity', 'temporal_resolution': 'monthly'},
            'display_name': 'Aridity'
        },
        'LU': {
            'subdir': 'LUWA',
            'attrs': {'units': 'None', 'source': 'WA', 'quantity': 'LU', 'temporal_resolution': 'static'},
            'display_name': 'Land Use Water Accounting'
        },
        'ProbaV': {
            'subdir': 'NDM',
            'attrs': {'units': 'None', 'source': 'ProbaV', 'quantity': 'NDM', 'temporal_resolution': 'monthly'},
            'display_name': 'NDM'
        },
        'ETref': {
            'subdir': 'ETref',
            'attrs': {'units': 'None', 'source': 'L1_RET', 'quantity': 'ETref', 'temporal_resolution': 'monthly'},
            'display_name': 'Reference Evapotranspiration'
        }
    }

    def _ensure_sync_flags(self):
        if not hasattr(self, "_syncing_basin_name"):
            self._syncing_basin_name = False
        if not hasattr(self, "_syncing_netcdf_dir"):
            self._syncing_netcdf_dir = False
        if not hasattr(self, "basin_display_labels"):
            self.basin_display_labels = []

    def register_basin_display_label(self, label, prefix="Basin Name:"):
        """Track labels that mirror the selected basin name."""
        self._ensure_sync_flags()
        if not any(lbl is label for lbl, _ in self.basin_display_labels):
            self.basin_display_labels.append((label, prefix))
        self.update_basin_display_labels()

    def update_basin_display_labels(self):
        self._ensure_sync_flags()
        current = getattr(self, 'selected_basin_name', "") or "Not set"
        for label, prefix in self.basin_display_labels:
            label.setText(f"{prefix} {current}")

    def sync_basin_name(self, text, source=None):
        self._ensure_sync_flags()
        if self._syncing_basin_name:
            return

        value = text or ""
        self._syncing_basin_name = True
        self.selected_basin_name = value

        if hasattr(self, 'basin_name_entry') and self.basin_name_entry and source != 'analysis':
            if self.basin_name_entry.text() != value:
                self.basin_name_entry.setText(value)

        self.update_basin_display_labels()

        self._syncing_basin_name = False

    def sync_netcdf_directory(self, path, source=None):
        self._ensure_sync_flags()
        if self._syncing_netcdf_dir:
            return

        value = path or ""
        self._syncing_netcdf_dir = True
        self.selected_netcdf_dir = value

        def set_line_edit(entry):
            if entry and isinstance(entry, QLineEdit) and entry.text() != value:
                entry.setText(value)

        if hasattr(self, 'netcdf_entries') and isinstance(getattr(self, 'netcdf_entries', None), dict):
            if source != 'netcdf_output':
                set_line_edit(self.netcdf_entries.get('output_dir'))

        if hasattr(self, 'full_entries') and isinstance(getattr(self, 'full_entries', None), dict):
            if source != 'full_output':
                set_line_edit(self.full_entries.get('output_dir'))
            set_line_edit(self.full_entries.get('sm_input'))
            set_line_edit(self.full_entries.get('nc_dir'))

        if hasattr(self, 'sm_entries') and isinstance(getattr(self, 'sm_entries', None), dict):
            set_line_edit(self.sm_entries.get('sm_input'))

        if hasattr(self, 'hydro_entries') and isinstance(getattr(self, 'hydro_entries', None), dict):
            set_line_edit(self.hydro_entries.get('nc_dir'))

        if hasattr(self, 'rain_input') and isinstance(self.rain_input, QLineEdit):
            if source != 'rain_page_input':
                set_line_edit(self.rain_input)

        self._syncing_netcdf_dir = False

    def create_section_card(self, title, subtitle=None):
        """Create a rounded card container with a header and optional subtitle."""
        card = QFrame()
        card.setObjectName("sectionCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(14)

        header = QLabel(title)
        header.setObjectName("sectionTitle")
        layout.addWidget(header)

        if subtitle:
            sublabel = QLabel(subtitle)
            sublabel.setObjectName("sectionSubtitle")
            sublabel.setWordWrap(True)
            layout.addWidget(sublabel)

        return card, layout

    def create_form_row(self, label_text, field_widget, browse_button=None):
        """Create a consistently styled horizontal row for form inputs."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 6, 0, 6)
        row.setSpacing(12)

        label = QLabel(label_text)
        label.setObjectName("formLabel")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setMinimumWidth(220)
        row.addWidget(label)

        if hasattr(field_widget, "setMinimumHeight"):
            field_widget.setMinimumHeight(34)
        if hasattr(field_widget, "setSizePolicy"):
            field_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row.addWidget(field_widget)

        if browse_button:
            browse_button.setObjectName("browseButton")
            browse_button.setCursor(Qt.PointingHandCursor)
            browse_button.setMinimumHeight(34)
            row.addWidget(browse_button)

        return row

    def create_header(self, title_text="Water Accounting Tool"):
        """Create consistent header with IWMI and SIWA logos and title"""
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(20)  # Add some spacing between elements

        # IWMI Logo
        iwmi_label = QLabel()
        iwmi_path = self.resource_path(os.path.join("resources", "iwmi.png"))
        if os.path.exists(iwmi_path):
            iwmi_pixmap = QPixmap(iwmi_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            iwmi_label.setPixmap(iwmi_pixmap)
        iwmi_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header_layout.addWidget(iwmi_label)

        # Title Container
        title_container = QWidget()
        title_container_layout = QVBoxLayout()
        title_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Title
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 30px; font-weight: bold; color: #4FC3F7;")
        title.setAlignment(Qt.AlignCenter)
        title_container_layout.addWidget(title)
        
        # Optional Subtitle (only for intro page)
        if title_text == "WA+ Water Accounting Tool":
            subtitle = QLabel("Comprehensive Hydrological Analysis Solution")
            subtitle.setStyleSheet("font-size: 16px; color: #BDBDBD;")
            subtitle.setAlignment(Qt.AlignCenter)
            title_container_layout.addWidget(subtitle)
        
        title_container.setLayout(title_container_layout)
        header_layout.addWidget(title_container, stretch=1)  # Allow title to expand

        # SIWA Logo
        siwa_label = QLabel()
        siwa_path = self.resource_path(os.path.join("resources", "siwa.png"))
        if os.path.exists(siwa_path):
            siwa_pixmap = QPixmap(siwa_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            siwa_label.setPixmap(siwa_pixmap)
        siwa_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header_layout.addWidget(siwa_label)

        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet("""
            background-color: #f5f5f5; 
            border-bottom: 1px solid #ddd;
            padding: 10px;
        """)
        header_widget.setFixedHeight(120)  # Fixed height for consistency
        return header_widget

    def create_footer(self):
        """Create consistent footer (e.g., copyright or navigation)"""
        footer_widget = QWidget()
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 10, 10, 10)

        # Example footer content: Copyright and version
        copyright_label = QLabel("© 2025 WA+ Tool | Powered by IWMI")
        copyright_label.setStyleSheet("font-size: 12px; color: #666;")
        footer_layout.addWidget(copyright_label)
        footer_layout.addStretch()

        footer_widget.setLayout(footer_layout)
        footer_widget.setStyleSheet("background-color: #f5f5f5; border-top: 1px solid #ddd;")
        return footer_widget

    def browse_directory(self, key, entries):
        # Safety: some keys are actually files; route them to file dialog
        file_filters = {
            "shapefile": "Shapefile (*.shp)",
            "template_mask": "GeoTIFF Files (*.tif *.tiff);;All Files (*)",
            "dem_path": "GeoTIFF Files (*.tif *.tiff);;All Files (*)",
            "aeisw_path": "GeoTIFF Files (*.tif *.tiff);;All Files (*)",
            "population_path": "GeoTIFF Files (*.tif *.tiff);;All Files (*)",
            "wpl_path": "GeoTIFF Files (*.tif *.tiff);;All Files (*)",
            "ewr_path": "All Files (*)",
            "inflow": "CSV Files (*.csv);;All Files (*)",
            "outflow": "CSV Files (*.csv);;All Files (*)",
            "tww": "CSV Files (*.csv);;All Files (*)",
            "cw_do": "CSV Files (*.csv);;All Files (*)"
        }
        if key in file_filters:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filters[key])
            if path:
                entries[key].setText(path)
            return

        # Default: directory selection
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            entries[key].setText(path)
            if key == "output_dir":
                if entries is getattr(self, 'netcdf_entries', None):
                    self.sync_netcdf_directory(path, source='netcdf_output')
                elif entries is getattr(self, 'full_entries', None):
                    self.sync_netcdf_directory(path, source='full_output')
            elif key == "sm_input" and entries is getattr(self, 'full_entries', None):
                self.sync_netcdf_directory(path, source='full_output')
            elif key == "nc_dir" and entries is getattr(self, 'full_entries', None):
                self.sync_netcdf_directory(path, source='full_output')
            elif key == "sm_input" and entries is getattr(self, 'sm_entries', None):
                self.sync_netcdf_directory(path, source='sm_input')
            elif key == "nc_dir" and entries is getattr(self, 'hydro_entries', None):
                self.sync_netcdf_directory(path, source='hydro_nc_dir')
            if key == "input_tifs":
                if entries == getattr(self, 'netcdf_entries', None):
                    self.update_tiff_counts()
                elif entries == getattr(self, 'full_entries', None):
                    self.update_tiff_counts_full()

    def browse_working_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if path:
            self.working_dir_entry.setText(path)
            netcdf_path = os.path.join(path, "NetCDF")
            results_path = os.path.join(path, "Results")
            os.makedirs(netcdf_path, exist_ok=True)
            os.makedirs(results_path, exist_ok=True)

            self.sync_netcdf_directory(netcdf_path, source='working_dir')

            # Update paths in all relevant pages
            if hasattr(self, 'netcdf_entries'):
                self.netcdf_entries['output_dir'].setText(netcdf_path)

            if hasattr(self, 'full_entries'):
                self.full_entries['output_dir'].setText(netcdf_path)
                self.full_entries['nc_dir'].setText(netcdf_path)
                self.full_entries['result_dir'].setText(results_path)
                self.full_entries['sm_input'].setText(netcdf_path)

            if hasattr(self, 'sm_entries'):
                self.sm_entries['sm_input'].setText(netcdf_path)

            if hasattr(self, 'hydro_entries'):
                self.hydro_entries['nc_dir'].setText(netcdf_path)
                self.hydro_entries['result_dir'].setText(results_path)

            if hasattr(self, 'rain_input'):
                self.rain_input.setText(netcdf_path)
            
    def browse_file(self, key, entries, file_filter):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if path:
            entries[key].setText(path)

    def scan_tiff_directory(self, directory):
        """Scan the input TIFF directory and count files by variable"""
        if not os.path.isdir(directory):
            return None
        
        results = {}
        total_files = 0
        
        # Scan all TIFF files in each variable's directory
        for var_name, config in self.dataset_config.items():
            var_dir = os.path.join(directory, config['subdir'])
            if not os.path.exists(var_dir):
                results[var_name] = {
                    'count': 0,
                    'status': f"Directory not found: {config['subdir']}",
                    'attrs': config['attrs'],
                    'display_name': config['display_name']
                }
                continue
                
            # Count all TIFF files in the directory
            tiff_files = [f for f in os.listdir(var_dir) 
                        if f.lower().endswith(('.tif', '.tiff'))]
            file_count = len(tiff_files)
            
            results[var_name] = {
                'count': file_count,
                'display_name': config['display_name'],
                'attrs': config['attrs']
            }
            total_files += file_count

        return {'results': results, 'total_files': total_files}

    def update_tiff_counts(self):
        """Update the count of TIFF files in the input directory for NetCDF page"""
        input_dir = self.netcdf_entries.get("input_tifs", QLineEdit()).text()
        scan_result = self.scan_tiff_directory(input_dir)
        
        if scan_result is None:
            self.netcdf_tiff_count.setText("TIFF Files: 0 (Invalid directory)")
            return
            
        # Create summary text with display names
        summary_lines = [f"<b>Total TIFF Files:</b> {scan_result['total_files']}"]
        
        # Order the variables as we want them displayed
        display_order = [
            'P',        # Monthly P
            'dailyP',   # Daily P
            'ET',
            'ETref',
            'LAI',
            'SMsat',
            'Ari',
            'LU',
            'ProbaV'
        ]
        
        for var_name in display_order:
            if var_name in scan_result['results']:
                data = scan_result['results'][var_name]
                summary_lines.append(f"<b>{data['display_name']}:</b> {data['count']} files")
        
        self.netcdf_tiff_count.setText("<br>".join(summary_lines))
        self.netcdf_tiff_count.setStyleSheet("color: #333333; font-size: 14px;")

    def update_tiff_counts_full(self):
        """Update the count of TIFF files for the full workflow page"""
        input_dir = self.full_entries.get("input_tifs", QLineEdit()).text()
        scan_result = self.scan_tiff_directory(input_dir)
        
        if scan_result is None:
            self.full_tiff_count.setText("TIFF Files: 0 (Invalid directory)")
            return
            
        # Create summary text with display names
        summary_lines = [f"<b>Total TIFF Files:</b> {scan_result['total_files']}"]
        
        # Order the variables as we want them displayed
        display_order = [
            'P',        # Monthly P
            'dailyP',   # Daily P
            'ET',
            'ETref',
            'LAI',
            'SMsat',
            'Ari',
            'LU',
            'ProbaV'
        ]
        
        for var_name in display_order:
            if var_name in scan_result['results']:
                data = scan_result['results'][var_name]
                summary_lines.append(f"<b>{data['display_name']}:</b> {data['count']} files")
        
        self.full_tiff_count.setText("<br>".join(summary_lines))
        self.full_tiff_count.setStyleSheet("color: #333333; font-size: 14px;")

    def show_netcdf_info(self):
        text = """
WA+ Input Data Requirements for NetCDF Creation

The Water Accounting Plus (WA+) Tool developed by IWMI requires a structured set of GeoTIFF raster inputs. These are later aggregated into NetCDF files for analysis.

-------------------------------------------------------------------------------
Required Folder Structure
-------------------------------------------------------------------------------

Input_Directory/
│
├── P/
│   ├── Monthly/   # Monthly precipitation (mm/month)
│   └── Daily/     # Daily precipitation (mm/day)
│
├── ET/            # Actual evapotranspiration (ETa)
├── ETref/         # Reference evapotranspiration (ETref / PET)
├── LAI/           # Leaf Area Index
├── ThetaSat/      # Soil moisture at saturation (Θsat)
├── Aridity/       # Aridity index
├── LULC/          # Land use / land cover (WALU classes)
└── NDM/           # Net dry matter

Note: Some implementations use LUWA/ or LandUse/ instead of LULC/, and SMsat/ instead of ThetaSat/. Ensure consistency with your processing scripts.

-------------------------------------------------------------------------------
File Naming Convention
-------------------------------------------------------------------------------

Each file must include the variable prefix and date.
- Daily rasters → YYYYMMDD
- Monthly rasters → YYYYMM

Examples:
- Precipitation (monthly): P_monthly_202301.tif
- Precipitation (daily): P_daily_20230115.tif
- Actual evapotranspiration (ETa): ETa_20230115.tif
- Reference evapotranspiration (ETref): ETref_20230115.tif
- Leaf Area Index (LAI): LAI_20230115.tif
- Soil moisture saturation (Θsat): ThetaSat_20230115.tif (or SMsat_YYYYMMDD.tif)
- Aridity index: Aridity_20230115.tif
- Land use / land cover: LULC_20230101.tif (or LU_YYYYMMDD.tif if simplified)
- Net dry matter (NDM): NDM_20230115.tif

-------------------------------------------------------------------------------
Spatial & Metadata Requirements
-------------------------------------------------------------------------------

- Projection: All rasters must share the same CRS (e.g., UTM or geographic WGS84).
- Resolution: Spatial resolution must be identical across all datasets.
- Extent: Files should fully cover the basin area.
- Shapefile: A basin boundary shapefile defines the area of interest.
- Mask: A binary GeoTIFF mask (1 = inside basin, 0 = outside) ensures uniform clipping.

-------------------------------------------------------------------------------
Summary
-------------------------------------------------------------------------------

This structure and naming scheme follows IWMI’s WA+ framework documentation and recent applications. It ensures smooth NetCDF creation and prevents processing errors.

        """
        QMessageBox.information(self, "Input File Requirements for NetCDF Creation", text.strip())

    def create_intro_page(self):
        """Create an interactive introduction page with IWMI and SIWA logos"""
        page = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self.create_header("Water Accounting Plus Tool")
        header.setFixedHeight(150)
        main_layout.addWidget(header)

        # Main content
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #E3F2FD, stop:1 #BBDEFB);
            border-radius: 15px;
            margin: 20px;
        """)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)

        # Title
        welcome_title = QLabel("Welcome to Water Accounting Plus Tool")
        welcome_title.setStyleSheet("""
            QLabel {
                font-size: 34px;
                font-weight: bold;
                color: #0D47A1;
            }
        """)
        welcome_title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(welcome_title)

        # Decorative line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("border: 2px solid #42A5F5; width: 80%; margin: 0 auto;")
        content_layout.addWidget(line)

        # Short description
        welcome_text = QLabel(
            "The WA+ methodology supports sustainable water management "
            "by providing a systematic approach to water resource assessment."
        )
        welcome_text.setWordWrap(True)
        welcome_text.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #424242;
                line-height: 1.5;
                margin: 15px 0;
            }
        """)
        welcome_text.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(welcome_text)

        # Buttons container
        button_container = QWidget()
        button_container.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 15px;
                padding: 25px;
            }
        """)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)

        # Learn About WA+ button
        info_btn = QPushButton("Learn About WA+")
        info_btn.clicked.connect(self.launch_intro)
        info_btn.setMinimumSize(300, 100)  # allow expansion if needed
        info_btn.setStyleSheet("""
            QPushButton {
                background-color: #42A5F5;
                color: white;
                font-size: 22px;  /* slightly larger than before */
                font-weight: bold;
                padding: 15px 20px;  /* more padding to avoid clipping */
                border-radius: 35px;
                border: none;
            }
            QPushButton:hover { background-color: #1E88E5; }
            QPushButton:pressed { background-color: #0D47A1; }
        """)
        info_btn.setCursor(Qt.PointingHandCursor)

        # Start Analysis button
        start_btn = QPushButton("Start Analysis")
        start_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        start_btn.setMinimumSize(300, 100)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #66BB6A;
                color: white;
                font-size: 22px;
                font-weight: bold;
                padding: 15px 20px;
                border-radius: 35px;
                border: none;
            }
            QPushButton:hover { background-color: #43A047; }
            QPushButton:pressed { background-color: #2E7D32; }
        """)
        start_btn.setCursor(Qt.PointingHandCursor)


        # Add buttons to layout
        button_layout.addWidget(info_btn)
        button_layout.addWidget(start_btn)
        button_container.setLayout(button_layout)

        content_layout.addWidget(button_container, alignment=Qt.AlignCenter)
        content_layout.addStretch()

        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)

        # Footer
        footer = self.create_footer()
        version_label = QLabel("Version 2.1.0")
        version_label.setStyleSheet("font-size: 12px; color: #666;")
        footer.layout().insertWidget(1, version_label)
        main_layout.addWidget(footer)

        page.setLayout(main_layout)
        self.stacked_widget.addWidget(page)


    def launch_intro(self):
        """Show the WA+ introduction window directly"""
        try:
            # Import the IntroWindow class directly
            from intro import IntroWindow
            
            # Create and show the intro window
            self.intro_window = IntroWindow()
            self.intro_window.show()
            
        except Exception as e:
            print(f"Error showing intro window: {e}")
            QMessageBox.critical(self, "Error", f"Could not show introduction: {str(e)}")

    def create_module_selection_page(self):
        """Create the module selection page"""
        page = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        main_layout.addWidget(self.create_header("Water Accounting Plus Tool"))

        welcome_title = QLabel("Select Analysis Module")
        welcome_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #81C784; margin-top: 20px;")
        welcome_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(welcome_title)

        # Content layout
        content_layout = QVBoxLayout()

        # Description
        desc = QLabel("Please select the type of analysis you want to perform:")
        desc.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(desc)
        
        # Working directory selection
        work_dir_row = QHBoxLayout()
        work_dir_row.addWidget(QLabel("Working Directory:"))
        self.working_dir_entry = QLineEdit()
        self.working_dir_entry.setToolTip("Select the base working directory. Subfolders 'NetCDF' and 'Results' will be created automatically.")
        work_dir_row.addWidget(self.working_dir_entry)
        browse_work_btn = QPushButton("Browse")
        browse_work_btn.clicked.connect(self.browse_working_dir)
        browse_work_btn.setCursor(Qt.PointingHandCursor)
        work_dir_row.addWidget(browse_work_btn)
        content_layout.addLayout(work_dir_row)

        basin_row = QHBoxLayout()
        basin_row.addWidget(QLabel("Basin Name:"))
        if getattr(self, 'basin_name_entry', None) is None:
            self.basin_name_entry = QLineEdit()
        basin_row.addWidget(self.basin_name_entry)
        self.basin_name_entry.setPlaceholderText("Enter basin name (e.g., Awash)")
        self.basin_name_entry.textChanged.connect(lambda text: self.sync_basin_name(text, 'analysis'))
        if getattr(self, 'selected_basin_name', ""):
            self.basin_name_entry.setText(self.selected_basin_name)
        content_layout.addLayout(basin_row)

        # Module buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(20)

        full_btn = QPushButton("Full Water Accounting")
        full_btn.setToolTip("Complete workflow from NetCDF creation to final water accounting sheets")
        full_btn.setMinimumSize(300, 60)
        full_btn.clicked.connect(lambda: self.start_workflow("full"))
        full_btn.setCursor(Qt.PointingHandCursor)
        full_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #4FC3F7;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
                border: 1px solid #4FC3F7;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
            }
        """)
        
        netcdf_btn = QPushButton("Create NetCDF")
        netcdf_btn.setToolTip("Create NetCDF files from TIFFs only")
        netcdf_btn.setMinimumSize(300, 60)
        netcdf_btn.clicked.connect(lambda: self.start_workflow("netcdf"))
        netcdf_btn.setCursor(Qt.PointingHandCursor)
        netcdf_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #81C784;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
                border: 1px solid #81C784;
            }
            QPushButton:hover {
                background-color: #E8F5E9;
            }
        """)
        
        sm_btn = QPushButton("Soil Moisture Balance")
        sm_btn.setToolTip("Calculate soil moisture balance only")
        sm_btn.setMinimumSize(300, 60)
        sm_btn.clicked.connect(lambda: self.start_workflow("smbalance"))
        sm_btn.setCursor(Qt.PointingHandCursor)
        sm_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #81C784;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
                border: 1px solid #81C784;
            }
            QPushButton:hover {
                background-color: #E8F5E9;
            }
        """)
        
        hydro_btn = QPushButton("Hydroloop Simulation")
        hydro_btn.setToolTip("Perform hydroloop calculations only")
        hydro_btn.setMinimumSize(300, 60)
        hydro_btn.clicked.connect(lambda: self.start_workflow("hydroloop"))
        hydro_btn.setCursor(Qt.PointingHandCursor)
        hydro_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #81C784;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
                border: 1px solid #81C784;
            }
            QPushButton:hover {
                background-color: #E8F5E9;
            }
        """)

        btn_layout.addWidget(full_btn, alignment=Qt.AlignCenter)
        btn_layout.addWidget(netcdf_btn, alignment=Qt.AlignCenter)
        btn_layout.addWidget(sm_btn, alignment=Qt.AlignCenter)
        btn_layout.addWidget(hydro_btn, alignment=Qt.AlignCenter)
        
        content_layout.addLayout(btn_layout)
        content_layout.addStretch(1)
        
        # Back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        back_btn.setFixedSize(100, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #EF5350;
                border-radius: 5px;
                border: 1px solid #EF5350;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        content_layout.addWidget(back_btn, alignment=Qt.AlignLeft)
        
        content_layout.setSpacing(20)
        main_layout.addLayout(content_layout)

        # Add consistent footer
        main_layout.addWidget(self.create_footer())

        page.setLayout(main_layout)
        self.stacked_widget.addWidget(page)

    def create_full_inputs_page(self):
        """Create the input page for full water accounting workflow"""
        page = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Add consistent header
        main_layout.addWidget(self.create_header("Full Water Accounting Inputs"))

        # Back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        back_btn.setFixedSize(100, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #EF5350;
                border-radius: 5px;
                border: 1px solid #EF5350;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(back_btn, alignment=Qt.AlignLeft)
        
        # Content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 30)
        content_layout.setSpacing(22)

        if not hasattr(self, 'full_entries'):
            self.full_entries = {}

        basin_display = QLabel()
        basin_display.setObjectName("basinBadge")
        self.register_basin_display_label(basin_display)

        netcdf_card, netcdf_layout = self.create_section_card(
            "NetCDF Creation Inputs",
            "Provide the required folders and spatial references for compiling the NetCDF stack."
        )
        netcdf_layout.addWidget(basin_display)

        netcdf_fields = [
            ("Input TIFF Directory:", "input_tifs", True, "Directory containing TIFF files"),
            ("Shapefile:", "shapefile", False, "Shapefile (*.shp)", "Shapefile for spatial reference"),
            ("Template/Mask File:", "template_mask", False, "GeoTIFF Files (*.tif *.tiff)", "Template and basin mask GeoTIFF file"),
            ("Output Directory:", "output_dir", True, "Directory to save NetCDF files (automatically set to Working Directory/NetCDF)")
        ]

        for label, key, is_dir, *args in netcdf_fields:
            field = QLineEdit()
            field.setToolTip(args[-1] if args else "")
            if key == "output_dir":
                field.textChanged.connect(lambda text: self.sync_netcdf_directory(text, 'full_output'))
                working_dir = self.working_dir_entry.text()
                if working_dir and not field.text():
                    field.setText(os.path.join(working_dir, "NetCDF"))
            if key == "input_tifs":
                field.textChanged.connect(lambda _: self.update_tiff_counts_full())

            self.full_entries[key] = field

            browse_btn = QPushButton("Browse")
            if is_dir:
                browse_btn.clicked.connect(lambda _, k=key: self.browse_directory(k, self.full_entries))
            else:
                file_filter = args[0] if args else "All Files (*)"
                browse_btn.clicked.connect(lambda _, k=key, f=file_filter: self.browse_file(k, self.full_entries, f))

            row = self.create_form_row(label, field, browse_btn)
            netcdf_layout.addLayout(row)

        info_btn = QPushButton("NetCDF File Requirements")
        info_btn.setObjectName("secondaryButton")
        info_btn.clicked.connect(self.show_netcdf_info)
        netcdf_layout.addWidget(info_btn, alignment=Qt.AlignLeft)

        self.full_tiff_count = QLabel("TIFF Files: 0")
        self.full_tiff_count.setObjectName("infoPanel")
        self.full_tiff_count.setWordWrap(True)
        netcdf_layout.addWidget(self.full_tiff_count)

        content_layout.addWidget(netcdf_card)

        sm_card, sm_layout = self.create_section_card(
            "Soil Moisture Balance Inputs",
            "Tune the temporal range and calibration factors before running the balance model."
        )

        sm_fields = [
            ("Input Directory:", "sm_input", True, "Directory containing input files"),
            ("Start Year:", "start_year", False, "Starting year for analysis (e.g., 2019)"),
            ("End Year:", "end_year", False, "Ending year for analysis (e.g., 2022)"),
            ("Percolation Factor:", "f_percol", False, "Percolation factor (e.g., 0.9)"),
            ("Smax Factor:", "f_smax", False, "Smax factor (e.g., 0.818)"),
            ("Correction Factor:", "cf", False, "Correction factor (e.g., 50)"),
            ("Baseflow Factor:", "f_bf", False, "Baseflow factor (e.g., 0.095)"),
            ("Deep Percolation Factor:", "deep_percol_f", False, "Deep percolation factor (e.g., 0.905)")
        ]

        for label, key, is_dir, tooltip in sm_fields:
            field = QLineEdit()
            field.setToolTip(tooltip)
            if key == "sm_input":
                field.setReadOnly(True)

            self.full_entries[key] = field
            browse_btn = None
            if is_dir and key != "sm_input":
                browse_btn = QPushButton("Browse")
                browse_btn.clicked.connect(lambda _, k=key: self.browse_directory(k, self.full_entries))

            row = self.create_form_row(label, field, browse_btn)
            sm_layout.addLayout(row)

        self.full_entries["start_year"].setText("2019")
        self.full_entries["end_year"].setText("2022")
        self.full_entries["f_percol"].setText("0.9")
        self.full_entries["f_smax"].setText("0.818")
        self.full_entries["cf"].setText("50")
        self.full_entries["f_bf"].setText("0.095")
        self.full_entries["deep_percol_f"].setText("0.905")

        content_layout.addWidget(sm_card)

        hydro_card, hydro_layout = self.create_section_card(
            "Hydroloop Inputs",
            "Link supporting rasters and tabular data before running the hydroloop simulation."
        )

        hydro_fields = [
            ("NC Directory:", "nc_dir", True, "Directory containing NetCDF files (automatically set to Working Directory/NetCDF)"),
            ("Results Directory:", "result_dir", True, "Directory to save results (automatically set to Working Directory/Results)"),
            ("DEM File:", "dem_path", False, "GeoTIFF Files (*.tif *.tiff);;All Files (*)", "Digital Elevation Model file"),
            ("AEISW File:", "aeisw_path", False, "GeoTIFF Files (*.tif *.tiff);;All Files (*)", "AEISW GeoTIFF file"),
            ("Population File:", "population_path", False, "GeoTIFF Files (*.tif *.tiff);;All Files (*)", "Population GeoTIFF file"),
            ("WPL File:", "wpl_path", False, "GeoTIFF Files (*.tif *.tiff);;All Files (*)", "WPL GeoTIFF file"),
            ("EWR File:", "ewr_path", False, "All Files (*)", "EWR file"),
            ("Inflow File:", "inflow", False, "CSV Files (*.csv);;All Files (*)", "Inflow CSV file"),
            ("Outflow File:", "outflow", False, "CSV Files (*.csv);;All Files (*)", "Outflow CSV file"),
            ("Total Waste Water File:", "tww", False, "CSV Files (*.csv);;All Files (*)", "Total Waste Water CSV file"),
            ("Total Water Consumption File:", "cw_do", False, "CSV Files (*.csv);;All Files (*)", "Total Water Consumption CSV file"),
            ("Hydro Year End Month:", "hydro_year", False, "", "End month of hydrological year"),
            ("Output Unit:", "output_unit", False, "", "Unit for output (MCM or Km³)")
        ]

        file_fields = ["dem_path", "aeisw_path", "population_path", "wpl_path", "ewr_path",
                       "inflow", "outflow", "tww", "cw_do"]

        for label, key, is_dir, *args in hydro_fields:
            browse_btn = None

            if key == "hydro_year":
                field = QComboBox()
                field.addItems(['A-JAN','A-FEB','A-MAR','A-APR','A-MAY','A-JUN',
                                'A-JUL','A-AUG','A-SEP','A-OCT','A-NOV','A-DEC'])
                field.setCurrentText('A-OCT')
                field.setToolTip(args[-1] if args else "")
            elif key == "output_unit":
                field = QComboBox()
                field.addItems(['MCM (million cubic meters)', 'Km³ (cubic kilometers)'])
                field.currentTextChanged.connect(self.update_unit_conversion)
                field.setToolTip(args[-1] if args else "")
                self.full_entries["unit_conversion"] = QLineEdit()
                self.full_entries["unit_conversion"].setText("1e3")
                self.full_entries["unit_conversion"].setVisible(False)
            else:
                field = QLineEdit()
                field.setToolTip(args[-1] if args else "")
                if key in ["nc_dir", "result_dir"]:
                    working_dir = self.working_dir_entry.text()
                    if working_dir and not field.text():
                        default_sub = "NetCDF" if key == "nc_dir" else "Results"
                        field.setText(os.path.join(working_dir, default_sub))
                if key == "nc_dir":
                    field.setReadOnly(True)

            if is_dir and key != "nc_dir":
                browse_btn = QPushButton("Browse")
                browse_btn.clicked.connect(lambda _, k=key: self.browse_directory(k, self.full_entries))
            elif key in file_fields:
                browse_btn = QPushButton("Browse")
                browse_btn.clicked.connect(lambda _, k=key, f=args[0]: self.browse_file(k, self.full_entries, f))

            self.full_entries[key] = field
            row = self.create_form_row(label, field, browse_btn)
            hydro_layout.addLayout(row)

        content_layout.addWidget(hydro_card)

        output_dir_value = self.full_entries.get("output_dir").text()
        if output_dir_value:
            self.sync_netcdf_directory(output_dir_value, source='full_output')

        run_card, run_layout = self.create_section_card(
            "Run Full Workflow",
            "Monitor each processing step and review detailed logs once the workflow finishes."
        )

        self.full_step_label = QLabel("Current step: Ready")
        self.full_step_label.setObjectName("stepLabel")
        run_layout.addWidget(self.full_step_label)

        self.full_log = QTextEdit()
        self.full_log.setObjectName("logPanel")
        self.full_log.setReadOnly(True)
        run_layout.addWidget(self.full_log)

        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(12)
        self.full_progress = QProgressBar()
        self.full_progress.setMaximum(2100)
        self.full_progress.setObjectName("progressBar")
        self.full_progress_label = QLabel("0%")
        self.full_progress_label.setObjectName("progressValue")
        self.full_progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(self.full_progress)
        progress_layout.addWidget(self.full_progress_label)
        run_layout.addLayout(progress_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)

        self.full_run_btn = QPushButton("Run Full Workflow")
        self.full_run_btn.setObjectName("primaryActionButton")
        self.full_run_btn.clicked.connect(self.run_full_workflow)
        btn_layout.addWidget(self.full_run_btn)

        self.full_next_btn = QPushButton("Next: Generate Sheets")
        self.full_next_btn.setObjectName("secondaryButton")
        self.full_next_btn.setEnabled(False)
        btn_layout.addWidget(self.full_next_btn)

        save_log_btn = QPushButton("Save Log")
        save_log_btn.setObjectName("secondaryButton")
        save_log_btn.clicked.connect(self.save_log(self.full_log))
        btn_layout.addWidget(save_log_btn)

        run_layout.addLayout(btn_layout)
        content_layout.addWidget(run_card)
        content_layout.addStretch(1)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Add consistent footer
        main_layout.addWidget(self.create_footer())
        
        page.setLayout(main_layout)
        self.stacked_widget.addWidget(page)

    def create_netcdf_page(self):
        """Create the NetCDF creation page with progress tracking"""
        page = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add consistent header
        main_layout.addWidget(self.create_header("Create NetCDF Files"))
        
        # Back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2 if self.workflow_type == "full" else 1))
        back_btn.setFixedSize(100, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #EF5350;
                border-radius: 5px;
                border: 1px solid #EF5350;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        # Content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 30)
        content_layout.setSpacing(22)

        basin_display = QLabel()
        basin_display.setObjectName("basinBadge")
        self.register_basin_display_label(basin_display)

        netcdf_card, netcdf_layout = self.create_section_card(
            "NetCDF Setup",
            "Point the tool to the directories and reference layers required for NetCDF creation."
        )
        netcdf_layout.addWidget(basin_display)

        fields = [
            ("Input TIFF Directory:", "input_tifs", True, "Directory containing TIFF files"),
            ("Shapefile:", "shapefile", False, "Shapefile (*.shp)", "Shapefile for spatial reference"),
            ("Template/Mask File:", "template_mask", False, "GeoTIFF Files (*.tif *.tiff)", "Template and basin mask GeoTIFF file"),
            ("Output Directory:", "output_dir", True, "Directory to save NetCDF files (automatically set to Working Directory/NetCDF)")
        ]

        self.netcdf_entries = {}
        for label, key, is_dir, *args in fields:
            field = QLineEdit()
            field.setToolTip(args[-1] if args else "")
            if key == "output_dir":
                field.textChanged.connect(lambda text: self.sync_netcdf_directory(text, 'netcdf_output'))
                working_dir = self.working_dir_entry.text()
                if working_dir and not field.text():
                    field.setText(os.path.join(working_dir, "NetCDF"))
            if key == "input_tifs":
                field.textChanged.connect(lambda _: self.update_tiff_counts())

            self.netcdf_entries[key] = field

            browse_btn = QPushButton("Browse")
            if is_dir:
                browse_btn.clicked.connect(lambda _, k=key: self.browse_directory(k, self.netcdf_entries))
            else:
                browse_btn.clicked.connect(lambda _, k=key, f=args[0]: self.browse_file(k, self.netcdf_entries, f))

            row = self.create_form_row(label, field, browse_btn)
            netcdf_layout.addLayout(row)

        info_btn = QPushButton("NetCDF File Requirements")
        info_btn.setObjectName("secondaryButton")
        info_btn.clicked.connect(self.show_netcdf_info)
        netcdf_layout.addWidget(info_btn, alignment=Qt.AlignLeft)

        self.netcdf_tiff_count = QLabel("TIFF Files: 0")
        self.netcdf_tiff_count.setObjectName("infoPanel")
        self.netcdf_tiff_count.setWordWrap(True)
        netcdf_layout.addWidget(self.netcdf_tiff_count)

        content_layout.addWidget(netcdf_card)

        status_card, status_layout = self.create_section_card(
            "Progress", "Track NetCDF creation progress and review the detailed log."
        )

        self.current_step_label = QLabel("Current step: Ready")
        self.current_step_label.setObjectName("stepLabel")
        status_layout.addWidget(self.current_step_label)

        self.netcdf_log = QTextEdit()
        self.netcdf_log.setObjectName("logPanel")
        self.netcdf_log.setReadOnly(True)
        status_layout.addWidget(self.netcdf_log)

        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(12)
        self.netcdf_progress = QProgressBar()
        self.netcdf_progress.setMaximum(100)
        self.netcdf_progress.setObjectName("progressBar")
        self.netcdf_progress_label = QLabel("0%")
        self.netcdf_progress_label.setObjectName("progressValue")
        self.netcdf_progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(self.netcdf_progress)
        progress_layout.addWidget(self.netcdf_progress_label)
        status_layout.addLayout(progress_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)

        self.netcdf_run_btn = QPushButton("Create NetCDF")
        self.netcdf_run_btn.setObjectName("primaryActionButton")
        self.netcdf_run_btn.clicked.connect(self.create_netcdf)
        btn_layout.addWidget(self.netcdf_run_btn)

        self.netcdf_next_btn = QPushButton("Next: Soil Moisture Balance")
        self.netcdf_next_btn.setObjectName("secondaryButton")
        self.netcdf_next_btn.setEnabled(False)
        self.netcdf_next_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(5))
        btn_layout.addWidget(self.netcdf_next_btn)

        save_log_btn = QPushButton("Save Log")
        save_log_btn.setObjectName("secondaryButton")
        save_log_btn.clicked.connect(self.save_log(self.netcdf_log))
        btn_layout.addWidget(save_log_btn)

        status_layout.addLayout(btn_layout)
        content_layout.addWidget(status_card)
        content_layout.addStretch(1)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        main_layout.setSpacing(20)

        # Add consistent footer
        main_layout.addWidget(self.create_footer())

        page.setLayout(main_layout)
        self.stacked_widget.addWidget(page)

    def create_rain_page(self):
        """Create the rain interception page with progress tracking"""
        page = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add consistent header
        main_layout.addWidget(self.create_header("Rain Interception Calculation"))
        
        # Back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3 if self.workflow_type == "full" else 1))
        back_btn.setFixedSize(100, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #EF5350;
                border-radius: 5px;
                border: 1px solid #EF5350;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 30)
        content_layout.setSpacing(22)

        input_card, input_layout = self.create_section_card(
            "Rain Interception Inputs",
            "The NetCDF directory is filled automatically after Create NetCDF completes."
        )

        self.rain_input = QLineEdit()
        self.rain_input.setToolTip("Directory containing input files for rain interception")
        self.rain_input.textChanged.connect(lambda text: self.sync_netcdf_directory(text, 'rain_page_input'))
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_directory("rain_input", {"rain_input": self.rain_input}))

        row = self.create_form_row("Input Directory:", self.rain_input, browse_btn)
        input_layout.addLayout(row)

        auto_info = QLabel("Rain interception runs automatically after NetCDF creation. Use this page to rerun the step if inputs change.")
        auto_info.setObjectName("sectionSubtitle")
        auto_info.setWordWrap(True)
        input_layout.addWidget(auto_info)

        working_dir = self.working_dir_entry.text()
        if working_dir:
            self.rain_input.setText(os.path.join(working_dir, "NetCDF"))

        content_layout.addWidget(input_card)

        status_card, status_layout = self.create_section_card(
            "Progress",
            "View the interception log and monitor completion."
        )

        self.rain_step_label = QLabel("Current step: Ready")
        self.rain_step_label.setObjectName("stepLabel")
        status_layout.addWidget(self.rain_step_label)

        self.rain_log = QTextEdit()
        self.rain_log.setObjectName("logPanel")
        self.rain_log.setReadOnly(True)
        status_layout.addWidget(self.rain_log)

        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(12)
        self.rain_progress = QProgressBar()
        self.rain_progress.setMaximum(300)
        self.rain_progress.setObjectName("progressBar")
        self.rain_progress_label = QLabel("0%")
        self.rain_progress_label.setObjectName("progressValue")
        self.rain_progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(self.rain_progress)
        progress_layout.addWidget(self.rain_progress_label)
        status_layout.addLayout(progress_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)

        self.rain_run_btn = QPushButton("Recalculate Rain Interception")
        self.rain_run_btn.setObjectName("primaryActionButton")
        self.rain_run_btn.clicked.connect(self.calculate_rain)
        btn_layout.addWidget(self.rain_run_btn)

        self.rain_next_btn = QPushButton("Next: Soil Moisture Balance")
        self.rain_next_btn.setObjectName("secondaryButton")
        self.rain_next_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(5))
        self.rain_next_btn.setEnabled(False)
        btn_layout.addWidget(self.rain_next_btn)

        save_log_btn = QPushButton("Save Log")
        save_log_btn.setObjectName("secondaryButton")
        save_log_btn.clicked.connect(self.save_log(self.rain_log))
        btn_layout.addWidget(save_log_btn)

        status_layout.addLayout(btn_layout)
        content_layout.addWidget(status_card)
        content_layout.addStretch(1)

        main_layout.addLayout(content_layout)
        main_layout.setSpacing(20)

        # Add consistent footer
        main_layout.addWidget(self.create_footer())

        page.setLayout(main_layout)
        self.stacked_widget.addWidget(page)

    def create_smbalance_page(self):
        """Create the soil moisture balance page with progress tracking"""
        page = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add consistent header
        main_layout.addWidget(self.create_header("Soil Moisture Balance"))
        
        # Back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4 if self.workflow_type == "full" else 1))
        back_btn.setFixedSize(100, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #EF5350;
                border-radius: 5px;
                border: 1px solid #EF5350;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        # Content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 30)
        content_layout.setSpacing(22)

        basin_display = QLabel()
        basin_display.setObjectName("basinBadge")
        self.register_basin_display_label(basin_display)

        if self.workflow_type == "full":
            inputs_card, inputs_layout = self.create_section_card(
                "Soil Moisture Balance Inputs",
                "Parameters are inherited from the full workflow configuration."
            )
            inputs_layout.addWidget(basin_display)

            fields = [
                ("Netcdf Directory:", "sm_input"),
                ("Start Year:", "start_year"),
                ("End Year:", "end_year"),
                ("Percolation Factor:", "f_percol"),
                ("Smax Factor:", "f_smax"),
                ("Correction Factor:", "cf"),
                ("Baseflow Factor:", "f_bf"),
                ("Deep Percolation Factor:", "deep_percol_f")
            ]

            for label, key in fields:
                value_widget = QLineEdit(self.full_entries[key].text() if isinstance(self.full_entries[key], QLineEdit)
                                         else self.full_entries[key])
                value_widget.setReadOnly(True)
                row = self.create_form_row(label, value_widget)
                inputs_layout.addLayout(row)
            content_layout.addWidget(inputs_card)
        else:
            inputs_card, inputs_layout = self.create_section_card(
                "Soil Moisture Balance Inputs",
                "Adjust the temporal window and calibration factors before running the balance model."
            )
            inputs_layout.addWidget(basin_display)

            fields = [
                ("Input Directory:", "sm_input", True, "Directory containing input files"),
                ("Start Year:", "start_year", False, "Starting year for analysis (e.g., 2019)"),
                ("End Year:", "end_year", False, "Ending year for analysis (e.g., 2022)"),
                ("Percolation Factor:", "f_percol", False, "Percolation factor (e.g., 0.9)"),
                ("Smax Factor:", "f_smax", False, "Smax factor (e.g., 52)"),
                ("Correction Factor:", "cf", False, "Correction factor (e.g., 50)"),
                ("Baseflow Factor:", "f_bf", False, "Baseflow factor (e.g., 0.095)"),
                ("Deep Percolation Factor:", "deep_percol_f", False, "Deep percolation factor (e.g., 0.905)")
            ]

            self.sm_entries = {}
            for label, key, is_dir, tooltip in fields:
                field = QLineEdit()
                field.setToolTip(tooltip)
                if key == "sm_input":
                    field.textChanged.connect(lambda text: self.sync_netcdf_directory(text, 'sm_input'))

                self.sm_entries[key] = field
                browse_btn = None
                if is_dir:
                    browse_btn = QPushButton("Browse")
                    browse_btn.clicked.connect(lambda _, k=key: self.browse_directory(k, self.sm_entries))

                row = self.create_form_row(label, field, browse_btn)
                inputs_layout.addLayout(row)

            working_dir = self.working_dir_entry.text()
            if working_dir:
                self.sm_entries["sm_input"].setText(os.path.join(working_dir, "NetCDF"))

            self.sm_entries["start_year"].setText("2019")
            self.sm_entries["end_year"].setText("2022")
            self.sm_entries["f_percol"].setText("0.9")
            self.sm_entries["f_smax"].setText("52")
            self.sm_entries["cf"].setText("50")
            self.sm_entries["f_bf"].setText("0.095")
            self.sm_entries["deep_percol_f"].setText("0.905")

            content_layout.addWidget(inputs_card)

        status_card, status_layout = self.create_section_card(
            "Progress",
            "Monitor the soil moisture balance run and capture the log for review."
        )

        self.sm_step_label = QLabel("Current step: Ready")
        self.sm_step_label.setObjectName("stepLabel")
        status_layout.addWidget(self.sm_step_label)

        self.sm_log = QTextEdit()
        self.sm_log.setObjectName("logPanel")
        self.sm_log.setReadOnly(True)
        status_layout.addWidget(self.sm_log)

        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(12)
        self.sm_progress = QProgressBar()
        self.sm_progress.setMaximum(100)
        self.sm_progress.setObjectName("progressBar")
        self.sm_progress_label = QLabel("0%")
        self.sm_progress_label.setObjectName("progressValue")
        self.sm_progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(self.sm_progress)
        progress_layout.addWidget(self.sm_progress_label)
        status_layout.addLayout(progress_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)

        self.sm_run_btn = QPushButton("Run Soil Moisture Balance")
        self.sm_run_btn.setObjectName("primaryActionButton")
        self.sm_run_btn.clicked.connect(self.run_smbalance)
        btn_layout.addWidget(self.sm_run_btn)

        self.sm_next_btn = QPushButton("Next: Hydroloop")
        self.sm_next_btn.setObjectName("secondaryButton")
        self.sm_next_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(6))
        self.sm_next_btn.setEnabled(False)
        btn_layout.addWidget(self.sm_next_btn)

        save_log_btn = QPushButton("Save Log")
        save_log_btn.setObjectName("secondaryButton")
        save_log_btn.clicked.connect(self.save_log(self.sm_log))
        btn_layout.addWidget(save_log_btn)

        status_layout.addLayout(btn_layout)
        content_layout.addWidget(status_card)
        content_layout.addStretch(1)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        main_layout.setSpacing(20)

        # Add consistent footer
        main_layout.addWidget(self.create_footer())

        page.setLayout(main_layout)
        self.stacked_widget.addWidget(page)

    def create_hydroloop_page(self):
        """Create the hydroloop page with progress tracking"""
        page = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add consistent header
        main_layout.addWidget(self.create_header("Hydroloop Analysis"))

        # Back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(5 if self.workflow_type == "full" else 1))
        back_btn.setFixedSize(100, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #EF5350;
                border-radius: 5px;
                border: 1px solid #EF5350;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        # Content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 30)
        content_layout.setSpacing(22)

        basin_display = QLabel()
        basin_display.setObjectName("basinBadge")
        self.register_basin_display_label(basin_display)

        if self.workflow_type == "full":
            inputs_card, inputs_layout = self.create_section_card(
                "Hydroloop Inputs",
                "Inputs mirror the configuration collected during the full workflow setup."
            )
            inputs_layout.addWidget(basin_display)

            fields = [
                ("Input Files Directory:", "nc_dir"),
                ("Results Directory:", "result_dir"),
                ("Template/Mask File:", "template_mask"),
                ("DEM File:", "dem_path"),
                ("AEISW File:", "aeisw_path"),
                ("Population File:", "population_path"),
                ("WPL File:", "wpl_path"),
                ("EWR File:", "ewr_path"),
                ("Inflow File:", "inflow"),
                ("Outflow File:", "outflow"),
                ("Total Waste Water File:", "tww"),
                ("Total Water Consumption File:", "cw_do"),
                ("Hydro Year End Month:", "hydro_year"),
                ("Output Unit:", "output_unit")
            ]

            for label, key in fields:
                source_widget = self.full_entries[key]
                if isinstance(source_widget, QLineEdit):
                    value = source_widget.text()
                elif isinstance(source_widget, QComboBox):
                    value = source_widget.currentText()
                else:
                    value = str(source_widget)
                display = QLineEdit(value)
                display.setReadOnly(True)
                row = self.create_form_row(label, display)
                inputs_layout.addLayout(row)

            content_layout.addWidget(inputs_card)
        else:
            inputs_card, inputs_layout = self.create_section_card(
                "Hydroloop Inputs",
                "Connect required rasters, CSV tables, and runtime preferences."
            )
            inputs_layout.addWidget(basin_display)

            fields = [
                ("Input Files Directory:", "nc_dir", True, "Directory containing NetCDF files"),
                ("Results Directory:", "result_dir", True, "Directory to save results"),
                ("Template/Mask File:", "template_mask", False, "GeoTIFF Files (*.tif *.tiff);;All Files (*)", "Template and basin mask GeoTIFF file"),
                ("DEM File:", "dem_path", False, "GeoTIFF Files (*.tif *.tiff);;All Files (*)", "Digital Elevation Model file"),
                ("AEISW File:", "aeisw_path", False, "GeoTIFF Files (*.tif *.tiff);;All Files (*)", "AEISW GeoTIFF file"),
                ("Population File:", "population_path", False, "GeoTIFF Files (*.tif *.tiff);;All Files (*)", "Population GeoTIFF file"),
                ("WPL File:", "wpl_path", False, "GeoTIFF Files (*.tif *.tiff);;All Files (*)", "WPL GeoTIFF file"),
                ("EWR File:", "ewr_path", False, "All Files (*)", "EWR file"),
                ("Inflow File:", "inflow", False, "CSV Files (*.csv);;All Files (*)", "Inflow CSV file"),
                ("Outflow File:", "outflow", False, "CSV Files (*.csv);;All Files (*)", "Outflow CSV file"),
                ("Total Waste Water File:", "tww", False, "CSV Files (*.csv);;All Files (*)", "Total Waste Water CSV file"),
                ("Total Water Consumption File:", "cw_do", False, "CSV Files (*.csv);;All Files (*)", "Total Water Consumption CSV file"),
                ("Hydro Year End Month:", "hydro_year", False, "", "End month of hydrological year"),
                ("Output Unit:", "output_unit", False, "", "Unit for output (MCM or Km³)")
            ]

            self.hydro_entries = {}
            file_fields = ["template_mask", "dem_path", "aeisw_path", "population_path",
                           "wpl_path", "ewr_path", "inflow", "outflow", "tww", "cw_do"]

            for label, key, is_dir, *args in fields:
                browse_btn = None

                if key == "hydro_year":
                    field = QComboBox()
                    field.addItems(['A-JAN','A-FEB','A-MAR','A-APR','A-MAY','A-JUN',
                                    'A-JUL','A-AUG','A-SEP','A-OCT','A-NOV','A-DEC'])
                    field.setCurrentText('A-OCT')
                    field.setToolTip(args[-1] if args else "")
                elif key == "output_unit":
                    field = QComboBox()
                    field.addItems(['MCM (million cubic meters)', 'Km³ (cubic kilometers)'])
                    field.currentTextChanged.connect(self.update_unit_conversion)
                    field.setToolTip(args[-1] if args else "")
                    self.hydro_entries["unit_conversion"] = QLineEdit()
                    self.hydro_entries["unit_conversion"].setText("1e3")
                    self.hydro_entries["unit_conversion"].setVisible(False)
                else:
                    field = QLineEdit()
                    field.setToolTip(args[-1] if args else "")
                    if key in ["nc_dir", "result_dir"]:
                        working_dir = self.working_dir_entry.text()
                        if working_dir and not field.text():
                            default_sub = "NetCDF" if key == "nc_dir" else "Results"
                            field.setText(os.path.join(working_dir, default_sub))
                    if key == "nc_dir":
                        field.setReadOnly(True)

                if is_dir and key != "nc_dir":
                    browse_btn = QPushButton("Browse")
                    browse_btn.clicked.connect(lambda _, k=key: self.browse_directory(k, self.hydro_entries))
                elif key in file_fields:
                    browse_btn = QPushButton("Browse")
                    browse_btn.clicked.connect(lambda _, k=key, f=args[0]: self.browse_file(k, self.hydro_entries, f))

                self.hydro_entries[key] = field
                row = self.create_form_row(label, field, browse_btn)
                inputs_layout.addLayout(row)

            content_layout.addWidget(inputs_card)

        status_card, status_layout = self.create_section_card(
            "Progress",
            "Initialize hydroloop assets, run the simulations, and monitor completion."
        )

        self.hydro_step_label = QLabel("Current step: Ready")
        self.hydro_step_label.setObjectName("stepLabel")
        status_layout.addWidget(self.hydro_step_label)

        self.hydro_log = QTextEdit()
        self.hydro_log.setObjectName("logPanel")
        self.hydro_log.setReadOnly(True)
        status_layout.addWidget(self.hydro_log)

        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(12)
        self.hydro_progress = QProgressBar()
        self.hydro_progress.setMaximum(500)
        self.hydro_progress.setObjectName("progressBar")
        self.hydro_progress_label = QLabel("0%")
        self.hydro_progress_label.setObjectName("progressValue")
        self.hydro_progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(self.hydro_progress)
        progress_layout.addWidget(self.hydro_progress_label)
        status_layout.addLayout(progress_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)

        self.hydro_init_btn = QPushButton("Initialize Hydroloop")
        self.hydro_init_btn.setObjectName("secondaryButton")
        self.hydro_init_btn.clicked.connect(self.init_hydroloop)
        btn_layout.addWidget(self.hydro_init_btn)

        self.hydro_run_btn = QPushButton("Run All Steps")
        self.hydro_run_btn.setObjectName("primaryActionButton")
        self.hydro_run_btn.setEnabled(False)
        self.hydro_run_btn.clicked.connect(self.run_hydroloop)
        btn_layout.addWidget(self.hydro_run_btn)

        self.hydro_next_btn = QPushButton("Next: Generate Sheets")
        self.hydro_next_btn.setObjectName("secondaryButton")
        self.hydro_next_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(7))
        self.hydro_next_btn.setEnabled(False)
        btn_layout.addWidget(self.hydro_next_btn)

        save_log_btn = QPushButton("Save Log")
        save_log_btn.setObjectName("secondaryButton")
        save_log_btn.clicked.connect(self.save_log(self.hydro_log))
        btn_layout.addWidget(save_log_btn)

        status_layout.addLayout(btn_layout)
        content_layout.addWidget(status_card)
        content_layout.addStretch(1)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        main_layout.setSpacing(20)

        # Add consistent footer
        main_layout.addWidget(self.create_footer())

        page.setLayout(main_layout)
        self.stacked_widget.addWidget(page)

    def create_sheets_page(self):
        """Create the sheets generation page with progress tracking"""
        page = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add consistent header
        main_layout.addWidget(self.create_header("Generate Sheets"))

        # Back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(6))
        back_btn.setFixedSize(100, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #EF5350;
                border-radius: 5px;
                border: 1px solid #EF5350;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        # Content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 30)
        content_layout.setSpacing(22)

        sheet1_card, sheet1_layout = self.create_section_card(
            "Sheet 1 Generation",
            "Create the WA+ Sheet 1 workbook and inspect the build log."
        )

        self.sheet1_step_label = QLabel("Current step: Ready")
        self.sheet1_step_label.setObjectName("stepLabel")
        sheet1_layout.addWidget(self.sheet1_step_label)

        self.sheet1_log = QTextEdit()
        self.sheet1_log.setObjectName("logPanel")
        self.sheet1_log.setReadOnly(True)
        sheet1_layout.addWidget(self.sheet1_log)

        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(12)
        self.sheet1_progress = QProgressBar()
        self.sheet1_progress.setMaximum(200)
        self.sheet1_progress.setObjectName("progressBar")
        self.sheet1_progress_label = QLabel("0%")
        self.sheet1_progress_label.setObjectName("progressValue")
        self.sheet1_progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(self.sheet1_progress)
        progress_layout.addWidget(self.sheet1_progress_label)
        sheet1_layout.addLayout(progress_layout)

        self.sheet1_btn_layout = QHBoxLayout()
        self.sheet1_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.sheet1_btn_layout.setSpacing(12)
        self.sheet1_run_btn = QPushButton("Generate Sheet 1")
        self.sheet1_run_btn.setObjectName("primaryActionButton")
        self.sheet1_run_btn.clicked.connect(self.generate_sheet1)
        self.sheet1_btn_layout.addWidget(self.sheet1_run_btn)

        save_sheet1_log_btn = QPushButton("Save Sheet 1 Log")
        save_sheet1_log_btn.setObjectName("secondaryButton")
        save_sheet1_log_btn.clicked.connect(self.save_log(self.sheet1_log))
        self.sheet1_btn_layout.addWidget(save_sheet1_log_btn)

        sheet1_layout.addLayout(self.sheet1_btn_layout)
        content_layout.addWidget(sheet1_card)

        sheet2_card, sheet2_layout = self.create_section_card(
            "Sheet 2 Generation",
            "Compile Sheet 2 outputs and review the processing log."
        )

        self.sheet2_step_label = QLabel("Current step: Ready")
        self.sheet2_step_label.setObjectName("stepLabel")
        sheet2_layout.addWidget(self.sheet2_step_label)

        self.sheet2_log = QTextEdit()
        self.sheet2_log.setObjectName("logPanel")
        self.sheet2_log.setReadOnly(True)
        sheet2_layout.addWidget(self.sheet2_log)

        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(12)
        self.sheet2_progress = QProgressBar()
        self.sheet2_progress.setMaximum(200)
        self.sheet2_progress.setObjectName("progressBar")
        self.sheet2_progress_label = QLabel("0%")
        self.sheet2_progress_label.setObjectName("progressValue")
        self.sheet2_progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(self.sheet2_progress)
        progress_layout.addWidget(self.sheet2_progress_label)
        sheet2_layout.addLayout(progress_layout)

        self.sheet2_btn_layout = QHBoxLayout()
        self.sheet2_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.sheet2_btn_layout.setSpacing(12)
        self.sheet2_run_btn = QPushButton("Generate Sheet 2")
        self.sheet2_run_btn.setObjectName("primaryActionButton")
        self.sheet2_run_btn.clicked.connect(self.generate_sheet2)
        self.sheet2_btn_layout.addWidget(self.sheet2_run_btn)

        save_sheet2_log_btn = QPushButton("Save Sheet 2 Log")
        save_sheet2_log_btn.setObjectName("secondaryButton")
        save_sheet2_log_btn.clicked.connect(self.save_log(self.sheet2_log))
        self.sheet2_btn_layout.addWidget(save_sheet2_log_btn)

        sheet2_layout.addLayout(self.sheet2_btn_layout)
        content_layout.addWidget(sheet2_card)
        content_layout.addStretch(1)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Add consistent footer
        main_layout.addWidget(self.create_footer())

        page.setLayout(main_layout)
        self.stacked_widget.addWidget(page)

    def update_unit_conversion(self, text):
        if text == 'MCM (million cubic meters)':
            self.full_entries["unit_conversion"].setText("1e3") if hasattr(self, 'full_entries') else self.hydro_entries["unit_conversion"].setText("1e3")
        else:
            self.full_entries["unit_conversion"].setText("1e6") if hasattr(self, 'full_entries') else self.hydro_entries["unit_conversion"].setText("1e6")