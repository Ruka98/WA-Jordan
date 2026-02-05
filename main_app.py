# Updated main_app.py with consistent headers and footers across all pages

import sys
import os
import time
import inspect
from license_page import LicenseDialog
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QProgressBar, 
                             QComboBox, QSpinBox, QMessageBox, QScrollArea, QStackedWidget, 
                             QSizePolicy, QFrame, QStackedLayout, QDialog)  # ← add QDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QFont
try:
    from backend import Backend
except ImportError:
    from app_backend import Backend
from ui_pages import UIPages
from ai_assistant import AIHandler
from collections import defaultdict


class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int, str)  # current, total, message
    result_signal = pyqtSignal(bool, list)

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        # Make args mutable so we can replace a progress callback if provided
        self.args = list(args)

    def run(self):
        try:
            # If the last arg is a callable (intended as progress callback), replace it with
            # a thread-safe emitter that uses Qt signals.
            if self.args and callable(self.args[-1]):
                def emit_progress(current, total, message=None):
                    try:
                        c = int(current) if current is not None else 0
                    except Exception:
                        c = 0
                    try:
                        t = int(total) if total else 100
                    except Exception:
                        t = 100
                    self.progress_signal.emit(c, t, message or "")
                self.args[-1] = emit_progress

            success, messages = self.func(*self.args)
        except Exception as e:
            # Ensure we never crash the GUI due to worker exceptions
            success = False
            messages = [f"[Worker] Error: {e}"]

        # Stream any messages to the UI
        for msg in messages or []:
            self.log_signal.emit(msg)

        self.result_signal.emit(success, messages or [])

class MainWindow(QMainWindow, UIPages):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Water Accounting Analysis Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.backend = Backend()
        self.ai_handler = AIHandler()
        self.basin_name_entry = None
        self.selected_basin_name = ""
        self._syncing_basin_name = False
        self._syncing_netcdf_dir = False
        self.workflow_type = None  # Initialize workflow_type to avoid AttributeError
        
        # Set window icon (logo) using resource_path
        iwmi_path = self.resource_path(os.path.join("resources", "iwmi.png"))
        if os.path.exists(iwmi_path):
            self.setWindowIcon(QIcon(iwmi_path))

        # Debug logo paths (optional)
        iwmi_path = self.resource_path(os.path.join("resources", "iwmi.png"))
        siwa_path = self.resource_path(os.path.join("resources", "siwa.png"))
        print(f"IWMI logo path: {iwmi_path} (exists: {os.path.exists(iwmi_path)})")
        print(f"SIWA logo path: {siwa_path} (exists: {os.path.exists(siwa_path)})")

        # Define stylesheet for light mode only
        self.light_stylesheet = """
            QMainWindow {
                background: #F3F5FA;
            }
            QLabel {
                color: #263238;
                font-family: 'Segoe UI', 'Open Sans', sans-serif;
                font-size: 15px;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #FBFCFF;
                color: #263238;
                border: 1px solid #CFD8DC;
                border-radius: 8px;
                padding: 8px 12px;
                font-family: 'Segoe UI', 'Open Sans', sans-serif;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                border: 1px solid #64B5F6;
                box-shadow: 0 0 0 2px rgba(100, 181, 246, 0.18);
            }
            QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QTextEdit:disabled {
                background-color: #ECEFF4;
                color: #90A4AE;
            }
            QPushButton {
                background-color: #F4F7FB;
                color: #1F2933;
                border: 1px solid #D0D7E2;
                border-radius: 8px;
                padding: 9px 18px;
                font-family: 'Segoe UI', 'Open Sans', sans-serif;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E6EDF6;
            }
            QPushButton:pressed {
                background-color: #D8E2EE;
            }
            QPushButton#primaryActionButton {
                background-color: #2E7D32;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 22px;
                font-size: 15px;
            }
            QPushButton#primaryActionButton:hover {
                background-color: #388E3C;
            }
            QPushButton#primaryActionButton:disabled {
                background-color: #A5D6A7;
                color: #F1F8F4;
            }
            QPushButton#secondaryButton {
                background-color: #ffffff;
                color: #1565C0;
                border: 1px solid #64B5F6;
                border-radius: 8px;
                padding: 9px 18px;
                font-size: 14px;
            }
            QPushButton#secondaryButton:hover {
                background-color: #E3F2FD;
            }
            QPushButton#secondaryButton:disabled {
                color: #90A4AE;
                border-color: #CFD8DC;
            }
            QPushButton#browseButton {
                background-color: #E8F3FF;
                color: #1565C0;
                border: 1px solid #90CAF9;
                border-radius: 8px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#browseButton:hover {
                background-color: #D2E9FF;
            }
            QLabel#sectionTitle {
                font-size: 20px;
                font-weight: 700;
                color: #0D47A1;
            }
            QLabel#sectionSubtitle {
                font-size: 13px;
                color: #546E7A;
            }
            QLabel#formLabel {
                color: #37474F;
                font-weight: 600;
                font-size: 14px;
                padding-right: 8px;
            }
            QFrame#sectionCard {
                background-color: #FFFFFF;
                border: 1px solid #E1E8F2;
                border-radius: 14px;
            }
            QLabel#basinBadge {
                background-color: #E3F2FD;
                color: #0D47A1;
                border-radius: 14px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 600;
                max-width: 280px;
            }
            QLabel#infoPanel {
                background-color: #F5F9FF;
                border: 1px solid #D6E4FF;
                border-radius: 10px;
                padding: 12px;
                color: #365370;
                font-size: 14px;
            }
            QLabel#stepLabel {
                color: #0D47A1;
                font-weight: 600;
                font-size: 15px;
            }
            QLabel#progressValue {
                color: #607D8B;
                font-weight: 600;
                min-width: 38px;
            }
            QTextEdit#logPanel {
                background-color: #FBFCFF;
                border: 1px solid #E1E8F2;
                border-radius: 12px;
                padding: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                color: #37474F;
            }
            QProgressBar#progressBar {
                background-color: #F0F4F8;
                border: 1px solid #CFD8DC;
                border-radius: 10px;
                text-align: center;
                color: #0D47A1;
                height: 26px;
            }
            QProgressBar#progressBar::chunk {
                background-color: #4FC3F7;
                border-radius: 10px;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #F1F4F9;
                border: 1px solid #CFD8DC;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #B0BEC5;
                border-radius: 6px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                background: transparent;
            }
        """
        
        # Apply light theme
        self.setStyleSheet(self.light_stylesheet)
        
        self.init_ui()

    def init_ui(self):
        # Create stacked widget for page navigation
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create pages from UIPages
        self.create_intro_page()
        self.create_module_selection_page()
        self.create_full_inputs_page()
        self.create_netcdf_page()
        self.create_rain_page()
        self.create_smbalance_page()
        self.create_hydroloop_page()
        self.create_sheets_page()
        
        # Show intro page first
        self.stacked_widget.setCurrentIndex(0)

        self.full_next_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(7))

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

    def browse_directory(self, key, entries):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            entries[key].setText(path)
            if key == "input_tifs":
                if entries == self.netcdf_entries:
                    self.update_tiff_counts()
                elif entries == self.full_entries:
                    self.update_tiff_counts_full()

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

    def start_workflow(self, workflow_type):
        """Set the workflow type and navigate to the appropriate page"""
        self.workflow_type = workflow_type
        
        if workflow_type == "full":
            self.stacked_widget.setCurrentIndex(2)  # Full inputs page
        elif workflow_type == "netcdf":
            self.stacked_widget.setCurrentIndex(3)  # NetCDF page
        elif workflow_type == "rain":
            self.stacked_widget.setCurrentIndex(4)  # Rain page
        elif workflow_type == "smbalance":
            self.stacked_widget.setCurrentIndex(5)  # Soil moisture balance page
        elif workflow_type == "hydroloop":
            self.stacked_widget.setCurrentIndex(6)  # Hydroloop page
        elif workflow_type == "sheets":
            self.stacked_widget.setCurrentIndex(7)  # Sheets page

    def update_unit_conversion(self, unit_text):
        """Update the hidden unit conversion factor based on user selection"""
        if "MCM" in unit_text:
            self.hydro_entries["unit_conversion"].setText("1e3")
        else:  # Km³
            self.hydro_entries["unit_conversion"].setText("1e6")

    def save_log(self, log_widget):
        def save():
            filename, _ = QFileDialog.getSaveFileName(self, "Save Log", "", "Text Files (*.txt)")
            if filename:
                with open(filename, "w") as f:
                    f.write(log_widget.toPlainText())
                QMessageBox.information(self, "Success", f"Log saved to {filename}")
        return save

    def _backend_supports_basin_name(self):
        if not hasattr(self, "_netcdf_supports_basin"):
            try:
                signature = inspect.signature(self.backend.create_netcdf)
                self._netcdf_supports_basin = "basin_name" in signature.parameters
            except (TypeError, ValueError):
                self._netcdf_supports_basin = False
        return self._netcdf_supports_basin

    def _backend_supports_rain_basin(self):
        if not hasattr(self, "_rain_supports_basin"):
            try:
                signature = inspect.signature(self.backend.calculate_rain)
                self._rain_supports_basin = "basin_name" in signature.parameters
            except (TypeError, ValueError):
                self._rain_supports_basin = False
        return self._rain_supports_basin

    def _backend_supports_smbalance_basin(self):
        if not hasattr(self, "_sm_supports_basin"):
            try:
                signature = inspect.signature(self.backend.run_smbalance)
                self._sm_supports_basin = "basin_name" in signature.parameters
            except (TypeError, ValueError):
                self._sm_supports_basin = False
        return self._sm_supports_basin

    def _current_basin_name(self):
        basin = getattr(self, "selected_basin_name", "") or ""
        if not basin and getattr(self, "basin_name_entry", None):
            basin = self.basin_name_entry.text()
        return basin

    def create_netcdf_full(self, update_progress):
        """Run NetCDF creation for full workflow"""
        input_dir = self.full_entries["input_tifs"].text()
        shp_path = self.full_entries["shapefile"].text()
        template_path = self.full_entries["template_mask"].text()
        output_dir = self.full_entries["output_dir"].text()
        bn = self._current_basin_name()

        call_args = [input_dir, shp_path, template_path, output_dir, update_progress]
        if self._backend_supports_basin_name():
            call_args.append(bn or None)

        return self.backend.create_netcdf(*call_args)

    def calculate_rain_full(self, update_progress):
        """Run rain interception for full workflow"""
        directory = self.full_entries["output_dir"].text()
        bn = self._current_basin_name()
        call_args = [directory, update_progress]
        if self._backend_supports_rain_basin():
            call_args.append(bn or None)
        return self.backend.calculate_rain(*call_args)

    def run_smbalance_full(self, update_progress):
        """Run soil moisture balance for full workflow"""
        directory = self.full_entries["sm_input"].text()
        start_year = self.full_entries["start_year"].text()
        end_year = self.full_entries["end_year"].text()
        f_percol = self.full_entries["f_percol"].text()
        f_smax = self.full_entries["f_smax"].text()
        cf = self.full_entries["cf"].text()
        f_bf = self.full_entries["f_bf"].text()
        deep_percol_f = self.full_entries["deep_percol_f"].text()
        bn = self._current_basin_name()
        call_args = [
            directory,
            start_year,
            end_year,
            f_percol,
            f_smax,
            cf,
            f_bf,
            deep_percol_f,
            update_progress,
        ]
        if self._backend_supports_smbalance_basin():
            call_args.append(bn or None)
        return self.backend.run_smbalance(*call_args)

    def init_hydroloop_full(self, update_progress):
        """Initialize hydroloop for full workflow"""
        inputs = {key: entry.text() if isinstance(entry, QLineEdit) else entry.currentText()
                 for key, entry in self.full_entries.items()}
        inputs.setdefault('basin_name', self._current_basin_name())
        return self.backend.init_hydroloop(inputs, update_progress)

    def run_hydroloop_full(self, update_progress):
        """Run hydroloop for full workflow"""
        return self.backend.run_hydroloop(update_progress)

    def create_netcdf(self):
        if self.workflow_type == "full":
            input_dir = self.full_entries["input_tifs"].text()
            shp_path = self.full_entries["shapefile"].text()
            template_path = self.full_entries["template_mask"].text()
            output_dir = self.full_entries["output_dir"].text()
            dir_source = "full_output"
        else:
            input_dir = self.netcdf_entries["input_tifs"].text()
            shp_path = self.netcdf_entries["shapefile"].text()
            template_path = self.netcdf_entries["template_mask"].text()
            output_dir = self.netcdf_entries["output_dir"].text()
            dir_source = "netcdf_output"

        if hasattr(self, "sync_netcdf_directory"):
            self.sync_netcdf_directory(output_dir, source=dir_source)

        basin_name = self._current_basin_name()

        self.netcdf_run_btn.setEnabled(False)
        self.netcdf_next_btn.setEnabled(False)
        self.netcdf_progress.setMaximum(100)
        self.netcdf_progress.setValue(0)
        self.netcdf_progress_label.setText("0%")
        self.current_step_label.setText("Current step: Preparing NetCDF creation")
        self.netcdf_log.append(f"[{time.strftime('%H:%M:%S')}] Starting NetCDF creation...")

        def update_netcdf_progress(current, total, message=None):
            total = int(total) if total else 100
            current = int(current)
            if self.netcdf_progress.maximum() != total:
                self.netcdf_progress.setMaximum(total)
            self.netcdf_progress.setValue(current)
            pct = 0 if not total else int((current / total) * 100)
            self.netcdf_progress_label.setText(f"{pct}%")
            if message:
                self.current_step_label.setText(f"Current step: {message}")
                self.netcdf_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")

        def finalize(success, messages):
            self.netcdf_run_btn.setEnabled(True)
            if success:
                self.netcdf_progress.setValue(self.netcdf_progress.maximum())
                self.netcdf_progress_label.setText("100%")
                self.netcdf_next_btn.setEnabled(True)
                self.current_step_label.setText("Current step: Rain interception completed")
                self.netcdf_log.append(f"[{time.strftime('%H:%M:%S')}] Rain interception completed successfully.")
                if hasattr(self, 'rain_next_btn'):
                    self.rain_next_btn.setEnabled(True)
                if hasattr(self, 'rain_run_btn'):
                    self.rain_run_btn.setEnabled(True)
                if hasattr(self, 'rain_step_label'):
                    self.rain_step_label.setText("Current step: Rain interception completed")
                if hasattr(self, 'rain_progress'):
                    self.rain_progress.setValue(self.rain_progress.maximum())
                    self.rain_progress_label.setText("100%")
                QMessageBox.information(self, "Success", "NetCDF creation and rain interception completed successfully")
            else:
                self.current_step_label.setText("Current step: Failed")
                if hasattr(self, 'rain_run_btn'):
                    self.rain_run_btn.setEnabled(True)
                if messages:
                    self.netcdf_log.append("\n".join(messages))
                QMessageBox.critical(self, "Error", messages[-1] if messages else "Task failed")

        def start_rain_interception():
            if hasattr(self, "sync_netcdf_directory"):
                self.sync_netcdf_directory(output_dir, source="rain")

            if hasattr(self, 'rain_input'):
                self.rain_input.setText(output_dir)
            if hasattr(self, 'rain_log'):
                self.rain_log.append(f"[{time.strftime('%H:%M:%S')}] Rain interception triggered automatically after NetCDF creation.")
            if hasattr(self, 'rain_step_label'):
                self.rain_step_label.setText("Current step: Running rain interception")
            if hasattr(self, 'rain_run_btn'):
                self.rain_run_btn.setEnabled(False)
            if hasattr(self, 'rain_progress'):
                self.rain_progress.setValue(0)
                self.rain_progress_label.setText("0%")

            def update_rain_progress(current, total, message=None):
                total = int(total) if total else 100
                current = int(current)
                if self.netcdf_progress.maximum() != total:
                    self.netcdf_progress.setMaximum(total)
                self.netcdf_progress.setValue(current)
                pct = 0 if not total else int((current / total) * 100)
                self.netcdf_progress_label.setText(f"{pct}%")
                step_message = f"Rain Interception - {message}" if message else "Rain Interception"
                if message:
                    self.current_step_label.setText(f"Current step: {step_message}")
                    self.netcdf_log.append(f"[{time.strftime('%H:%M:%S')}] {step_message}")

                if hasattr(self, 'rain_progress'):
                    if self.rain_progress.maximum() != total:
                        self.rain_progress.setMaximum(total)
                    self.rain_progress.setValue(current)
                    self.rain_progress_label.setText(f"{pct}%")
                    if message and hasattr(self, 'rain_log'):
                        self.rain_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")

            def rain_result(success, messages):
                if success and hasattr(self, 'rain_log'):
                    self.rain_log.append(f"[{time.strftime('%H:%M:%S')}] Rain interception completed.")
                finalize(success, messages)

            rain_args = [output_dir, update_rain_progress]
            if self._backend_supports_rain_basin():
                rain_args.append(basin_name or None)
            self.worker = WorkerThread(self.backend.calculate_rain, *rain_args)
            self.worker.log_signal.connect(self.netcdf_log.append)
            if hasattr(self, 'rain_log'):
                self.worker.log_signal.connect(self.rain_log.append)
            self.worker.progress_signal.connect(update_rain_progress)
            self.worker.result_signal.connect(rain_result)
            self.worker.start()

        def handle_netcdf_result(success, messages):
            if not success:
                finalize(False, messages)
                return

            self.netcdf_log.append(f"[{time.strftime('%H:%M:%S')}] NetCDF creation completed. Starting rain interception...")
            self.current_step_label.setText("Current step: Starting rain interception")
            start_rain_interception()

        netcdf_args = [input_dir, shp_path, template_path, output_dir, update_netcdf_progress]
        if self._backend_supports_basin_name():
            netcdf_args.append(basin_name or None)

        self.worker = WorkerThread(self.backend.create_netcdf, *netcdf_args)
        self.worker.log_signal.connect(self.netcdf_log.append)
        self.worker.progress_signal.connect(update_netcdf_progress)
        self.worker.result_signal.connect(handle_netcdf_result)
        self.worker.start()

    def calculate_rain(self):
        if self.workflow_type == "full":
            directory = self.full_entries["output_dir"].text()
        else:
            directory = self.rain_input.text()
            
        self.rain_run_btn.setEnabled(False)
        self.rain_progress.setMaximum(300)
        self.rain_progress.setValue(0)
        
        def update_progress(current, total, message=None):
            # Keep bar maximum aligned to backend-reported total
            if self.rain_progress.maximum() != int(total):
                self.rain_progress.setMaximum(int(total))
            self.rain_progress.setValue(int(current))
            # Label percent computed from current/total
            pct = 0 if not total else int((int(current)/int(total))*100)
            self.rain_progress_label.setText(f"{pct}%")
            if message:
                self.rain_step_label.setText(f"Current step: {message}")
                self.rain_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")

        
        bn = self._current_basin_name()
        rain_args = [directory, update_progress]
        if self._backend_supports_rain_basin():
            rain_args.append(bn or None)

        self.worker = WorkerThread(self.backend.calculate_rain, *rain_args)
        self.worker.log_signal.connect(self.rain_log.append)
        self.worker.progress_signal.connect(update_progress)
        self.worker.result_signal.connect(
            lambda success, messages: self.task_finished(
                success, messages, 
                self.rain_run_btn, 
                self.rain_progress, 
                self.rain_next_btn
            )
        )
        self.worker.start()

    def run_smbalance(self):
        if self.workflow_type == "full":
            directory = self.full_entries["sm_input"].text()
            start_year = self.full_entries["start_year"].text()
            end_year = self.full_entries["end_year"].text()
            f_percol = self.full_entries["f_percol"].text()
            f_smax = self.full_entries["f_smax"].text()
            cf = self.full_entries["cf"].text()
            f_bf = self.full_entries["f_bf"].text()
            deep_percol_f = self.full_entries["deep_percol_f"].text()
        else:
            directory = self.sm_entries["sm_input"].text()
            start_year = self.sm_entries["start_year"].text()
            end_year = self.sm_entries["end_year"].text()
            f_percol = self.sm_entries["f_percol"].text()
            f_smax = self.sm_entries["f_smax"].text()
            cf = self.sm_entries["cf"].text()
            f_bf = self.sm_entries["f_bf"].text()
            deep_percol_f = self.sm_entries["deep_percol_f"].text()

        self.sm_run_btn.setEnabled(False)
        self.sm_progress.setMaximum(100)
        self.sm_progress.setValue(0)
        
        def update_progress(current, total, message=None):
            total = int(total) if total else 100
            current = int(current)
            if self.sm_progress.maximum() != total:
                self.sm_progress.setMaximum(total)
            self.sm_progress.setValue(current)
            pct = 0 if not total else int((current / total) * 100)
            self.sm_progress_label.setText(f"{pct}%")
            if message:
                self.sm_step_label.setText(f"Current step: {message}")
                self.sm_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")

        bn = self._current_basin_name()
        sm_args = [
            directory,
            start_year,
            end_year,
            f_percol,
            f_smax,
            cf,
            f_bf,
            deep_percol_f,
            update_progress,
        ]
        if self._backend_supports_smbalance_basin():
            sm_args.append(bn or None)

        self.worker = WorkerThread(
            self.backend.run_smbalance,
            *sm_args,
        )

        self.worker.log_signal.connect(self.sm_log.append)
        self.worker.progress_signal.connect(update_progress)
        self.worker.result_signal.connect(
            lambda success, messages: self.task_finished(
                success, messages, 
                self.sm_run_btn, 
                self.sm_progress, 
                self.sm_next_btn
            )
        )
        self.worker.start()

    def init_hydroloop(self):
        if self.workflow_type == "full":
            inputs = {key: entry.text() if isinstance(entry, QLineEdit) else entry.currentText()
                     for key, entry in self.full_entries.items()}
        else:
            inputs = {key: entry.text() if isinstance(entry, QLineEdit) else entry.currentText()
                     for key, entry in self.hydro_entries.items()}
        inputs.setdefault('basin_name', self._current_basin_name())

        self.hydro_init_btn.setEnabled(False)
        self.hydro_progress.setMaximum(500)
        self.hydro_progress.setValue(0)
        
        def update_progress(current, total, message=None):
            total = int(total) if total else 100
            current = int(current)
            if self.hydro_progress.maximum() != total:
                self.hydro_progress.setMaximum(total)
            self.hydro_progress.setValue(current)
            pct = 0 if not total else int((current / total) * 100)
            self.hydro_progress_label.setText(f"{pct}%")
            if message:
                self.hydro_step_label.setText(f"Current step: {message}")
                self.hydro_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        
        self.worker = WorkerThread(self.backend.init_hydroloop, inputs, update_progress)
        self.worker.log_signal.connect(self.hydro_log.append)
        self.worker.progress_signal.connect(update_progress)
        self.worker.result_signal.connect(
            lambda success, messages: self.task_finished(
                success, messages, 
                self.hydro_init_btn, 
                self.hydro_progress, 
                self.hydro_run_btn
            )
        )
        self.worker.start()

    def run_hydroloop(self):
        self.hydro_run_btn.setEnabled(False)
        self.hydro_progress.setMaximum(100)
        
        def update_progress(current, total, message=None):
            total = int(total) if total else 100
            current = int(current)
            if self.hydro_progress.maximum() != total:
                self.hydro_progress.setMaximum(total)
            self.hydro_progress.setValue(current)
            pct = 0 if not total else int((current / total) * 100)
            self.hydro_progress_label.setText(f"{pct}%")
            if message:
                self.hydro_step_label.setText(f"Current step: {message}")
                self.hydro_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        
        self.worker = WorkerThread(self.backend.run_hydroloop, update_progress)
        self.worker.log_signal.connect(self.hydro_log.append)
        self.worker.progress_signal.connect(update_progress)
        self.worker.result_signal.connect(
            lambda success, messages: self.task_finished(
                success, messages, 
                self.hydro_run_btn, 
                self.hydro_progress, 
                self.hydro_next_btn
            )
        )
        self.hydro_next_btn.clicked.disconnect()
        self.hydro_next_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(7))
        self.worker.start()

    def generate_sheet1(self):
        if not hasattr(self.backend, 'BASIN') or not self.backend.BASIN:
            QMessageBox.critical(self, "Error", "Hydroloop not initialized or basin data not available")
            return
            
        self.sheet1_run_btn.setEnabled(False)
        self.sheet1_progress.setMaximum(100)
        self.sheet1_progress.setValue(0)
        
        def update_progress(current, total, message=None):
            total = int(total) if total else 100
            current = int(current)
            if self.sheet1_progress.maximum() != total:
                self.sheet1_progress.setMaximum(total)
            self.sheet1_progress.setValue(current)
            pct = 0 if not total else int((current / total) * 100)
            self.sheet1_progress_label.setText(f"{pct}%")
            if message:
                self.sheet1_step_label.setText(f"Current step: {message}")
                self.sheet1_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        
        self.worker = WorkerThread(
            self.backend.generate_sheet1, 
            self.backend.BASIN, 
            update_progress
        )
        self.worker.log_signal.connect(self.sheet1_log.append)
        self.worker.progress_signal.connect(update_progress)
        self.worker.result_signal.connect(
            lambda success, messages: self.task_finished(
                success, messages, 
                self.sheet1_run_btn, 
                self.sheet1_progress
            )
        )
        self.worker.start()

    def generate_sheet2(self):
        if not hasattr(self.backend, 'BASIN') or not self.backend.BASIN:
            QMessageBox.critical(self, "Error", "Hydroloop not initialized or basin data not available")
            return
            
        self.sheet2_run_btn.setEnabled(False)
        self.sheet2_progress.setMaximum(100)
        self.sheet2_progress.setValue(0)
        
        def update_progress(current, total, message=None):
            total = int(total) if total else 100
            current = int(current)
            if self.sheet2_progress.maximum() != total:
                self.sheet2_progress.setMaximum(total)
            self.sheet2_progress.setValue(current)
            pct = 0 if not total else int((current / total) * 100)
            self.sheet2_progress_label.setText(f"{pct}%")
            if message:
                self.sheet2_step_label.setText(f"Current step: {message}")
                self.sheet2_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        
        self.worker = WorkerThread(
            self.backend.generate_sheet2, 
            self.backend.BASIN, 
            update_progress
        )
        self.worker.log_signal.connect(self.sheet2_log.append)
        self.worker.progress_signal.connect(update_progress)
        self.worker.result_signal.connect(
            lambda success, messages: self.task_finished(
                success, messages, 
                self.sheet2_run_btn, 
                self.sheet2_progress
            )
        )
        self.worker.start()

    def task_finished(self, success, messages, run_btn, progress=None, next_btn=None):
        run_btn.setEnabled(True)
        if progress:
            progress.setValue(progress.maximum())
        if next_btn and success:
            next_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Success", "Task completed successfully")
        else:
            QMessageBox.critical(self, "Error", messages[-1] if messages else "Task failed")

# Replace the run_full_workflow method with this improved version:

    def run_full_workflow(self):
        """Run all steps of the full workflow sequentially with memory management"""
        try:
            if self.workflow_type != "full":
                QMessageBox.critical(self, "Error", "Full workflow can only be run from Full Water Accounting mode")
                return

            # Reset UI elements
            self.full_run_btn.setEnabled(False)
            self.full_progress.setMaximum(100)  # Overall progress (percentage)
            self.full_progress.setValue(0)
            self.full_log.clear()
            self.full_step_label.setText("Current step: Starting full workflow...")

            # Define workflow steps. The overall progress will be derived from
            # the real current/total values reported by each task instead of a
            # static weighting scheme.
            workflow_steps = [
                {
                    'name': "Creating NetCDF Files",
                    'func': self.create_netcdf_full,
                },
                {
                    'name': "Calculating Rain Interception",
                    'func': self.calculate_rain_full,
                },
                {
                    'name': "Running Soil Moisture Balance",
                    'func': self.run_smbalance_full,
                },
                {
                    'name': "Initializing Hydroloop",
                    'func': self.init_hydroloop_full,
                },
                {
                    'name': "Running Hydroloop",
                    'func': self.run_hydroloop_full,
                },
            ]

            # Track current step and progress
            self.current_step_index = 0
            self.step_totals = [100 for _ in workflow_steps]
            self.completed_units = 0
            self.total_units = sum(self.step_totals)
            self._current_step_last_message = ""

            def update_step_progress(current, total, message=None):
                """Update progress within the current step"""
                step = workflow_steps[self.current_step_index]
                safe_total = max(int(total), 1) if total else self.step_totals[self.current_step_index]
                self.step_totals[self.current_step_index] = safe_total
                self.total_units = sum(self.step_totals)

                safe_current = min(max(int(current), 0), safe_total)
                overall_units = self.completed_units + safe_current
                overall_progress = (overall_units / self.total_units) * 100 if self.total_units else 0

                # Update overall progress bar and label with integers for smooth rendering
                self.full_progress.setValue(int(round(overall_progress)))
                self.full_progress_label.setText(f"{int(round(overall_progress))}%")

                # Build a descriptive status message for the current step
                if message:
                    step_message = message
                else:
                    ratio = safe_current / safe_total if safe_total else 0
                    step_message = f"{int(ratio * 100)}% complete"

                # Only append to the log when the message actually changes to avoid spam
                if step_message != self._current_step_last_message:
                    timestamp = time.strftime('%H:%M:%S')
                    self.full_log.append(f"[{timestamp}] {step['name']}: {step_message}")
                    self._current_step_last_message = step_message

                self.full_step_label.setText(f"Current step: {step['name']} - {step_message}")

            def step_completed(success, messages):
                """Handle completion of each step"""
                if not success:
                    self.full_run_btn.setEnabled(True)
                    QMessageBox.critical(self, "Error", "\n".join(messages))
                    return

                # Update accumulated progress
                step = workflow_steps[self.current_step_index]
                self.completed_units += self.step_totals[self.current_step_index]
                overall_progress = (self.completed_units / self.total_units) * 100 if self.total_units else 0
                self.full_progress.setValue(int(round(overall_progress)))
                self.full_progress_label.setText(f"{int(round(overall_progress))}%")

                # Log completion and update UI message
                timestamp = time.strftime('%H:%M:%S')
                self.full_log.append(f"[{timestamp}] Completed: {step['name']}")
                self.full_step_label.setText(f"Current step: {step['name']} - Completed")
                self._current_step_last_message = ""

                # Clean up memory between steps
                if hasattr(self.backend, 'cleanup'):
                    self.backend.cleanup()

                # Move to next step or finish
                self.current_step_index += 1
                if self.current_step_index < len(workflow_steps):
                    execute_step(self.current_step_index)
                else:
                    self.full_run_btn.setEnabled(True)
                    self.full_next_btn.setEnabled(True)
                    self.completed_units = self.total_units
                    self.full_progress.setValue(100)
                    self.full_progress_label.setText("100%")
                    self.full_step_label.setText("Workflow until Hydroloop is complete. You can now generate sheets.")
                    QMessageBox.information(self, "Success", "Workflow until Hydroloop is complete. Click 'Next: Generate Sheets' to continue.")

            def execute_step(step_index):
                """Execute a specific workflow step"""
                step = workflow_steps[step_index]
                self.full_log.append(f"Starting: {step['name']}")
                self.full_step_label.setText(f"Current step: {step['name']}")
                self._current_step_last_message = ""

                try:
                    self.worker = WorkerThread(step['func'], update_step_progress)
                    self.worker.log_signal.connect(self.full_log.append)
                    self.worker.progress_signal.connect(update_step_progress)
                    self.worker.result_signal.connect(step_completed)
                    self.worker.start()
                except Exception as e:
                    self.full_log.append(f"Error starting step {step['name']}: {str(e)}")
                    step_completed(False, [f"Error starting step {step['name']}: {str(e)}"])

            # Start the first step
            execute_step(0)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start workflow: {str(e)}")
            self.full_run_btn.setEnabled(True)

    def closeEvent(self, event):
        if hasattr(self.backend, 'running') and self.backend.running:
            reply = QMessageBox.question(self, "Quit", "A task is running! Are you sure you want to quit?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # 1) Show license FIRST
    dlg = LicenseDialog("LICENSE.txt")  # LicenseDialog already uses resource_path
    if dlg.exec_() != QDialog.Accepted:
        sys.exit(0)  # User declined → exit

    # 2) Only then start your main window
    window = MainWindow()
    window.show()

    # 3) Enter Qt event loop
    sys.exit(app.exec_())