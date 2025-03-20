from __future__ import annotations

import csv
import shutil
import subprocess
import sys
import os
import re

import numpy as np

import qdarktheme

from PySide6.QtCore import QSettings
from PySide6.QtCore import Qt
from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction
from PySide6.QtGui import QCloseEvent
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QButtonGroup
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QDoubleSpinBox
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import QFormLayout
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QHeaderView
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QMenu
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QRadioButton
from PySide6.QtWidgets import QSlider
from PySide6.QtWidgets import QSpinBox
from PySide6.QtWidgets import QSplitter
from PySide6.QtWidgets import QTableWidget
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.Core import Core
from src.cycle import CyclicMeasurementSetupWindow
from src.s_server import SocketWindow
from src.tooltips import tooltips as tt
from src.utils import units_of_measurements
from src.Widgets import AnalyserWidget
from src.Widgets import Graph
from src.Widgets import PixmapWidget
from src.Widgets import TableUnit
from src.surface_mapping_ui import SurfaceMappingDialog

def extract_numeric_value(text):
        """Extract numeric values from a string, ignoring units (e.g., μm)."""
        match = re.search(r"[-+]?\d*\.?\d+", text)  # Matches floats (including negative values)
        return float(match.group()) if match else None  # Convert to float if found

# Define the main window
class MainWindow(QMainWindow):  # type: ignore
    cycle_dialog: CyclicMeasurementSetupWindow

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Laser Level Webcam Tool")
        # self.resize(1100, 650)

        # create a "File" menu and add an "Export CSV" action to it
        file_menu = QMenu("File", self)
        self.menuBar().addMenu(file_menu)
        export_action = QAction("Export CSV", self)
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)

        # create "File->Cyclic measurement" action
        cycle_action = QAction("Cyclic measurement", self)
        cycle_action.triggered.connect(self.cycle_measurement_action)
        self.cycle_dialog = CyclicMeasurementSetupWindow(self)
        self.cycle_dialog.onMeasurementTrigger.connect(self.on_cyclic_measurement)
        file_menu.addAction(cycle_action)

        # Create a new menu option
        surface_mapping_action = QAction("Surface Mapping", self)
        surface_mapping_action.triggered.connect(self.open_surface_mapping)  # ✅ Attach to method
        self.menuBar().addMenu("Tools").addAction(surface_mapping_action)

        # websocket server action
        websocket_action = QAction("Socket Server", self)
        websocket_action.triggered.connect(self.socket_server_action)
        self.socket_dialog = SocketWindow(self)
        file_menu.addAction(websocket_action)

        # create a QAction for the "Exit" option
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # create a QAction for the "Source Code" option
        source_action = QAction("Source Code", self)
        source_action.triggered.connect(self.openSourceCode)
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(source_action)

        # Create status bar
        self.status_bar = self.statusBar()

        self.setting_zero = False  # state if the GUI is setting zero
        self.replace_sample = False  # state if we are replcing a sample
        self.table_selected_index = 0  # we keep track of the index so we can reselect it

        self.core = Core()  # where all the magic happens

        # Set the main window layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)



        

        self.farleft_splitter = QSplitter()
        # Widgets
        self.left_splitter = QSplitter()
        self.middle_splitter = QSplitter()
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.setup_surface_mapping_panel()  # ✅ Add this line to initialize the panel
        
        surface_map_widget = QGroupBox("Surface Map")

        sensor_feed_widget = QGroupBox("Sensor Feed")
        analyser_widget = QGroupBox("Analyser")
        sampler_widget = QGroupBox("Sampler")
        plot_widget = QGroupBox("Plot")

        # -- Sensor Feed --
        self.sensor_feed_widget = PixmapWidget()
        self.sensor_feed_widget.setToolTip(tt["feed"])
        self.camera_combo = QComboBox()
        self.camera_combo.setToolTip(tt["cameras"])
        camera_device_settings_btn = QPushButton("Device Settings")
        camera_device_settings_btn.setToolTip(tt["cam_device"])
        sensor_layout = QVBoxLayout()
        sensor_layout.setContentsMargins(1, 6, 1, 1)
        sensor_form = QFormLayout()
        sensor_form.addRow("Camera", self.camera_combo)
        sensor_layout.addWidget(self.sensor_feed_widget)
        sensor_layout.addLayout(sensor_form)
        sensor_layout.addWidget(camera_device_settings_btn)
        sensor_feed_widget.setLayout(sensor_layout)

        # -- Analyser --
        self.analyser_widget = AnalyserWidget()
        self.analyser_widget.setToolTip(tt["analyser"])
        self.smoothing = QSlider(Qt.Horizontal)
        self.smoothing.setToolTip(tt["smoothing"])
        self.smoothing.setRange(0, 200)
        self.smoothing.setTickInterval(1)
        analyser_form = QFormLayout()
        analyser_layout = QVBoxLayout()
        analyser_layout.setContentsMargins(1, 6, 1, 1)
        analyser_form.addRow("Smoothing", self.smoothing)
        analyser_layout.addWidget(self.analyser_widget)
        analyser_layout.addLayout(analyser_form)
        analyser_widget.setLayout(analyser_layout)

        # -- Sampler --
        self.subsamples_spin = QSpinBox()
        self.subsamples_spin.setToolTip(tt["subsamples"])
        self.subsamples_spin.setRange(1, 9999)
        self.outlier_spin = QSpinBox()
        self.outlier_spin.setToolTip(tt["outliers"])
        self.outlier_spin.setRange(0, 99)
        self.units_combo = QComboBox()
        self.units_combo.setToolTip(tt["units"])
        self.units_combo.addItems(list(units_of_measurements.keys()))
        self.units_combo.setCurrentIndex(1)
        self.sensor_width_spin = QDoubleSpinBox()
        self.sensor_width_spin.setToolTip(tt["sensor_width"])
        self.zero_btn = QPushButton("Zero")
        self.zero_btn.setToolTip(tt["zero_btn"])
        self.sample_btn = QPushButton("Take Sample")
        self.sample_btn.setToolTip(tt["samples"])
        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setToolTip(tt["replace"])
        self.delete_btn = QPushButton("Clear")
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setToolTip("Clear all measuremnts from sample table")

        self.delete_btn.setDisabled(True)
        self.reset_btn.setDisabled(False)  # ✅ Ensure it's enabled

        self.sample_btn.setDisabled(True)
        self.replace_btn.setDisabled(True)
        self.sample_table = QTableWidget()
        self.sample_table.setToolTip(tt["table"])
        self.sample_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sample_table.setSelectionMode(QAbstractItemView.SingleSelection)  # limit selection to a single row
        sample_layout = QGridLayout()
        sample_layout.setContentsMargins(1, 1, 1, 1)
        sample_layout.addWidget(QLabel("Sub Samples #"), 0, 0, 1, 1, alignment=Qt.AlignRight)
        sample_layout.addWidget(self.subsamples_spin, 0, 1, 1, 1)
        sample_layout.addWidget(QLabel("Outlier Removal %"), 0, 2, 1, 2, alignment=Qt.AlignRight)
        sample_layout.addWidget(self.outlier_spin, 0, 4, 1, 1)
        sample_layout.addWidget(QLabel("Units"), 1, 0, 1, 1, alignment=Qt.AlignRight)
        sample_layout.addWidget(self.units_combo, 1, 1, 1, 1)
        sample_layout.addWidget(QLabel("Sensor Width (mm)"), 1, 2, 1, 2, alignment=Qt.AlignRight)
        sample_layout.addWidget(self.sensor_width_spin, 1, 4, 1, 1)
        sample_layout.addWidget(self.zero_btn, 2, 0, 1, 1)
        sample_layout.addWidget(self.sample_btn, 2, 1, 1, 1)
        sample_layout.addWidget(self.replace_btn, 2, 2, 1, 1)
        sample_layout.addWidget(self.delete_btn, 2, 3, 1, 1)
        sample_layout.addWidget(self.reset_btn, 2, 4, 1, 1)  # ✅ Added to the right of Delete
        sample_layout.addWidget(self.sample_table, 3, 0, 1, 5)
        sampler_widget.setLayout(sample_layout)

        # -- Plot --
        self.graph_mode_group = QButtonGroup()

        self.raw_radio = QRadioButton("Raw")
        self.raw_radio.setToolTip(tt["raw"])
        self.graph_mode_group.addButton(self.raw_radio)
        self.flat_radio = QRadioButton("Flattened")
        self.flat_radio.setToolTip(tt["flat"])
        self.graph_mode_group.addButton(self.flat_radio)
        self.graph = Graph(self.core.samples)
        self.graph.setToolTip(tt["plot"])
        plot_layout = QVBoxLayout()
        plot_layout.setContentsMargins(0, 3, 0, 0)
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.raw_radio, alignment=Qt.AlignRight)
        radio_layout.addWidget(self.flat_radio)
        plot_layout.addLayout(radio_layout)
        plot_layout.addWidget(self.graph)
        plot_widget.setLayout(plot_layout)
        # Attach Widgets
        self.left_splitter.addWidget(sensor_feed_widget)
        self.left_splitter.addWidget(analyser_widget)
        self.right_splitter.addWidget(sampler_widget)
        self.right_splitter.addWidget(plot_widget)
        self.middle_splitter.addWidget(self.left_splitter)
        self.middle_splitter.addWidget(self.right_splitter)
        main_layout.addWidget(self.middle_splitter)

        # Logic
        self.middle_splitter.setSizes([300, 100])

        self.graph.samples = self.core.samples

        for cam in self.core.get_cameras():
            self.camera_combo.addItem(cam)

        self.core.set_camera(self.camera_combo.currentIndex())

        # Signals
        # self.core.OnSensorFeedUpdate.connect(self.sensor_feed_widget.setPixmap)
        self.core.frameWorker.OnAnalyserUpdate.connect(self.analyser_widget.set_data)
        self.sensor_feed_widget.OnHeightChanged.connect(self.analyser_widget.setMaximumHeight)
        self.sensor_feed_widget.OnHeightChanged.connect(
            lambda value: setattr(self.core.frameWorker, "analyser_widget_height", value)
        )
        self.smoothing.valueChanged.connect(lambda value: setattr(self.core.frameWorker, "analyser_smoothing", value))
        self.smoothing.valueChanged.connect(self.smoothing_value)
        self.subsamples_spin.valueChanged.connect(lambda value: setattr(self.core, "subsamples", value))
        self.outlier_spin.valueChanged.connect(lambda value: setattr(self.core, "outliers", value))
        self.units_combo.currentTextChanged.connect(self.core.set_units)
        self.sensor_width_spin.valueChanged.connect(lambda value: setattr(self.core, "sensor_width", value))
        self.zero_btn.clicked.connect(self.zero_btn_cmd)
        self.sample_btn.clicked.connect(self.sample_btn_cmd)
        self.replace_btn.clicked.connect(self.replace_btn_cmd)
        self.delete_btn.clicked.connect(self.delete_btn_cmd)
        self.reset_btn.clicked.connect(self.reset_sample_table)  # Connect action

        self.core.OnSubsampleProgressUpdate.connect(self.subsample_progress_update)
        self.core.OnSampleComplete.connect(self.finished_subsample)
        self.core.OnSampleComplete.connect(self.update_table)
        self.core.OnUnitsChanged.connect(self.update_table)
        self.core.OnUnitsChanged.connect(self.graph.set_units)
        camera_device_settings_btn.clicked.connect(self.extra_controls)
        self.camera_combo.currentIndexChanged.connect(self.core.set_camera)
        self.graph_mode_group.buttonClicked.connect(self.update_graph_mode)
        self.sample_table.itemSelectionChanged.connect(self.hightlight_sample)

        # New
        self.core.frameWorker.OnPixmapChanged.connect(self.sensor_feed_widget.setPixmap)
        self.core.frameWorker.OnCentreChanged.connect(self.core.sample_worker.sample_in)

        # Trigger the state of things
        self.smoothing.setValue(50)
        self.subsamples_spin.setValue(10)
        self.outlier_spin.setValue(30)
        self.units_combo.setCurrentIndex(0)
        self.sensor_width_spin.setValue(5.9)
        self.raw_radio.setChecked(True)

        settings = QSettings("laser-level-webcam", "LaserLevelWebcam")

        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("sensor_width"):
            self.sensor_width_spin.setValue(float(settings.value("sensor_width")))
        if settings.contains("smoothing"):
            self.smoothing.setValue(int(settings.value("smoothing")))
        if settings.contains("subsamples"):
            self.subsamples_spin.setValue(int(settings.value("subsamples")))
        if settings.contains("outlier"):
            self.outlier_spin.setValue(int(settings.value("outlier")))
        if settings.contains("units"):
            self.units_combo.setCurrentIndex(int(settings.value("units")))
        if settings.contains("raw"):
            if settings.value("raw") == "true":
                self.raw_radio.setChecked(True)
            else:
                self.flat_radio.setChecked(True)

        if settings.contains("left_splitter"):
            self.left_splitter.setSizes([int(i) for i in settings.value("left_splitter")])
        if settings.contains("middle_splitter"):
            self.middle_splitter.setSizes([int(i) for i in settings.value("middle_splitter")])
        if settings.contains("right_splitter"):
            self.right_splitter.setSizes([int(i) for i in settings.value("right_splitter")])

        if settings.contains("ip_address"):
            self.socket_dialog.ip_line.setText(settings.value("ip_address"))
        if settings.contains("port"):
            self.socket_dialog.port_line.setText(settings.value("port"))

        self.update_graph_mode()  # have to trigger it manually the first time

        self.status_bar.showMessage("Loading first camera", 1000)  # 3 seconds

    def setup_surface_mapping_panel(self):
        """
        Adds the Surface Mapping Panel to the left-hand side of the MainWindow.
        """
        self.surface_mapping_panel = SurfaceMappingDialog(self)
    # ✅ Ensure the panel appears on the left by adding it to `left_splitter`
        self.left_splitter.insertWidget(0, self.surface_mapping_panel)

    def smoothing_value(self, val: float) -> None:
        self.status_bar.showMessage(f"Smoothing: {val}", 1000)  # 3 seconds

    def openSourceCode(self) -> None:
        url = "https://github.com/bhowiebkr/laser-level-webcam"
        QDesktopServices.openUrl(QUrl(url))

    def export_csv(self) -> None:
        # get the file path from the user using a QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        # open the file and write the data from the QTableWidget to it as CSV
        with open(file_path, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            for row in range(self.sample_table.rowCount()):
                row_data = []
                for column in range(self.sample_table.columnCount()):
                    item = self.sample_table.item(row, column)
                    if item is not None:
                        row_data.append(item.text().replace("\u03bc", "u"))
                    else:
                        row_data.append("")
                writer.writerow(row_data)

    def socket_server_action(self) -> None:
        """Show the dialog for the websocket server"""
        self.socket_dialog.message_received.connect(self.socket_dialog.update_text_edit)
        self.socket_dialog.take_sample.connect(self.sample_btn_cmd)
        self.socket_dialog.zero.connect(self.zero_btn_cmd)
        self.core.OnSampleComplete.connect(self.socket_server_sample_complete)

        self.socket_dialog.show()

    def open_surface_mapping(self):
        """Opens the Surface Mapping UI and ensures it is initialized."""
        if not hasattr(self, "surface_mapping_ui") or self.surface_mapping_ui is None:
            self.surface_mapping_ui = SurfaceMappingDialog(self)  # ✅ Create the instance

        self.surface_mapping_ui.show()  # ✅ Show the dialog

    def socket_server_sample_complete(self) -> None:
        # Zeroing out samples
        if self.core.setting_zero_sample:
            self.socket_dialog.send_message("ZERO_COMPLETE")
        # Sample finished
        else:
            sample_val = self.core.samples[-1].y
            self.socket_dialog.send_message(f"SAMPLE {sample_val}")

    def cycle_measurement_action(self) -> None:
        """Displays the cyclic measurement dialog"""
        self.cycle_dialog.show()

    def on_cyclic_measurement(self) -> None:
        """Executed on each cyclic measurement- acquires a sample (if zeroed), zeroes measurements otherwise."""
        if self.sample_btn.isEnabled():
            self.sample_btn.click()
        else:
            self.zero_btn.click()

    def hightlight_sample(self) -> None:
        index = self.sample_table.currentRow()
        self.graph.set_selected_index(index)

    def extra_controls(self) -> None:
        # If the command exists
        if shutil.which("ffmpeg"):
            cmd = f'ffmpeg -f dshow -show_video_device_dialog true -i video="{self.camera_combo.currentText()}"'
            subprocess.Popen(cmd, shell=True)
        else:
            print("missing!")
            msg = QMessageBox()
            msg.setWindowTitle("Missing FFMPEG")
            msg_str = "FFMPEG is not installed or is not found in the Windows path. "
            msg_str += "Please download, install, and add it to your Windows path"
            msg.setText(msg_str)
            msg.exec_()

    def update_graph_mode(self) -> None:
        checked_button = self.graph_mode_group.checkedButton()
        self.graph.set_mode(checked_button.text())

    def get_unique_filename(self, base_filename="latest_measurement.csv"):
        """Ensures that data is always appended to the latest existing file."""

        file_base, file_ext = os.path.splitext(base_filename)

        # ✅ Check if the base file exists and use it
        if os.path.exists(base_filename):
            return base_filename

        # ✅ If no base file, check for the latest version
        version = 1
        latest_file = base_filename  # Default to base filename if no versions exist

        while os.path.exists(f"{file_base}_v{version}{file_ext}"):
            latest_file = f"{file_base}_v{version}{file_ext}"
            version += 1

        # ✅ Return the latest existing file (or base file if no versions exist)
        return latest_file

    def update_table(self) -> None:
        """
        Updates the QTableWidget with the latest measurement data.
        This function no longer writes to external files.
        """
        units = self.core.units
        header_names = [
            f"Measured ({units})",
            f"Flattened ({units})",
            f"Shim ({units})",
            f"Scrape ({units})",
        ]

        self.sample_table.setColumnCount(len(header_names))
        self.sample_table.setHorizontalHeaderLabels(header_names)
        header = self.sample_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Clear the table UI
        self.sample_table.setRowCount(0)

        for sample in self.core.samples:
            row_index = self.sample_table.rowCount()
            self.sample_table.insertRow(row_index)

            row_data = [sample.y, sample.linYError, sample.shim, sample.scrape]
            
            for col, val in enumerate(row_data):
                cell = TableUnit()
                cell.value = val
                cell.units = self.core.units
                self.sample_table.setItem(row_index, col, cell)

        # Maintain UI selection
        if self.sample_table.rowCount() and not self.sample_table.selectedIndexes():
            self.sample_table.selectRow(0)

        self.sample_table.selectRow(self.table_selected_index)
        self.graph.update_graph()
        print("Table updated successfully.")

    def reset_sample_table(self):
        """Clears all entries in the sample table."""
        confirm = QMessageBox.question(
            self, "Confirm Reset", "Are you sure you want to clear all sample data?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self.sample_table.setRowCount(0)  # ✅ Clears all rows
            print("[DEBUG] Sample Table Reset: All entries cleared.")

    def collect_measurement_data(self, row_index=None):
        """
        ✅ Extracts raw measurement data from the sample table without computing averages.
        This function simply collects the data for storage and visualization.
        """
        print(f"\n🔍 [DEBUG] collect_measurement_data() called! Row Index: {row_index}")

        if row_index is None or row_index >= self.sample_table.rowCount():
            print("❌ [DEBUG] Invalid row index! Exiting function.")
            return None, None, None, None, None, None, None, None, None

        # ✅ Extract values directly from the sample table
        item = self.sample_table.item(row_index, 0)  # ✅ Measured Avg
        shim_item = self.sample_table.item(row_index, 2)  # ✅ Shim Value
        scrape_item = self.sample_table.item(row_index, 3)  # ✅ Scrape Value

        measured_avg = extract_numeric_value(item.text().strip()) if item else None
        min_value, max_value = measured_avg, measured_avg  # ✅ No computation, just raw values
        shim_value = extract_numeric_value(shim_item.text().strip()) if shim_item else None
        scrape_value = extract_numeric_value(scrape_item.text().strip()) if scrape_item else None

        # ✅ Debug output
        print(f"  📝 [DEBUG] Extracted Data from Row {row_index}:")
        print(f"     - Measured Avg: {measured_avg}")
        print(f"     - Shim Value: {shim_value}")
        print(f"     - Scrape Value: {scrape_value}")

        return measured_avg, min_value, max_value, shim_value, shim_value, shim_value, scrape_value, scrape_value, scrape_value


    def compute_overall_measurement(self, row_index=None):
        """
        ✅ Compute the average, min, and max measurement from the selected sample row.
        If row_index is None, process all samples.
        """

        print("[DEBUG] compute_overall_measurement() called!")

        values, shim_values, scrape_values = [],[],[]
        
        for row in range(self.sample_table.rowCount()):
            # ✅ If a specific row index is provided, only process that row
            if row_index is not None and row != row_index:
                continue  

            item = self.sample_table.item(row, 0)  # ✅ Column 0 = Measured Avg
            shim_item = self.sample_table.item(row, 2)  # ✅ Shim Value
            scrape_item = self.sample_table.item(row, 3)  # ✅ Scrape Value

            numeric_value = extract_numeric_value(item.text().strip()) if item else None
            if numeric_value is not None:
                values.append(numeric_value)

            shim_numeric = extract_numeric_value(shim_item.text().strip()) if shim_item else None
            if shim_numeric is not None:
                shim_values.append(shim_numeric)

            scrape_numeric = extract_numeric_value(scrape_item.text().strip()) if scrape_item else None
            if scrape_numeric is not None:
                scrape_values.append(scrape_numeric)
        
        # ✅ Compute stats only if values exist
        if values:
            avg_value, min_value, max_value = np.mean(values), min(values), max(values)
            avg_shim, min_shim, max_shim = np.mean(shim_values), min(shim_values), max(shim_values) if shim_values else (None, None, None)
            avg_scrape, min_scrape, max_scrape = np.mean(scrape_values), min(scrape_values), max(scrape_values) if scrape_values else (None, None, None)
        else:
            return None, None, None, None, None, None, None, None, None

        return avg_value, min_value, max_value, avg_shim, min_shim, max_shim, avg_scrape, min_scrape, max_scrape



    def export_measurement_to_mapping(self):
        """Sends computed average measurement to Surface Mapping UI."""
        
        # 🔥 Debug: Ensure this function is running
        print("🔥 export_measurement_to_mapping() is being called!")
        avg_value, min_value, max_value = self.compute_overall_measurement()
        
        # 🔥 Debug: Print computed values
        print(f"✅ Computed Values -> Avg: {avg_value}, Min: {min_value}, Max: {max_value}")
        

        # ✅ Ensure Surface Mapping UI is open before sending data
        if hasattr(self, "surface_mapping_ui") and self.surface_mapping_ui:
            self.surface_mapping_ui.handle_measurement_import(avg_value, min_value, max_value, count)
        else:
                print("❌ Error: Surface Mapping UI is not open!")
                QMessageBox.warning(self, "Error", "Surface Mapping UI is not open.")



    def finished_subsample(self) -> None:
        """
        Sample complete. Reset the GUI back to the default state
        """
        self.zero_btn.setEnabled(True)
        self.sample_btn.setEnabled(True)
        self.replace_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        if self.setting_zero is True:
            self.zero_btn.setText("Zero")
            self.setting_zero = False
        else:
            if self.replace_sample:
                self.replace_btn.setText("Replace Sample")
                self.replace_sample = False
            else:
                self.sample_btn.setText("Take Sample")

    def subsample_progress_update(self, sample_total: list[int]) -> None:
        """
        Progress update on either zero or sample button
        """

        sample = sample_total[0]
        total = sample_total[1]

        if self.setting_zero is True:
            self.zero_btn.setText(f"{sample}/{total}")
        else:
            if self.replace_sample:
                self.replace_btn.setText(f"{sample}/{total}")
            else:
                self.sample_btn.setText(f"{sample}/{total}")

    def zero_btn_cmd(self) -> None:
        """
        Calls the sample button command but sets a flag so we know the GUI is in a state of setting the zero value
        """
        self.table_selected_index = 0

        self.setting_zero = True
        self.replace_sample = False
        self.zero_btn.setDisabled(True)
        self.sample_btn.setDisabled(True)
        self.replace_btn.setDisabled(True)

        self.core.samples[:] = []  # clear list in-place without changing it's reference
        self.graph.update_graph()
        self.core.start_sample(self.setting_zero, replacing_sample=False, replacing_sample_index=0)

    def sample_btn_cmd(self) -> None:
        """
        Calls on Core to take a sample
        """
        self.table_selected_index = self.sample_table.currentRow()

        self.zero_btn.setDisabled(True)
        self.sample_btn.setDisabled(True)
        self.replace_btn.setDisabled(True)
        self.core.start_sample(self.setting_zero, replacing_sample=False, replacing_sample_index=0)

    def replace_btn_cmd(self) -> None:
        """
        Call for when we are replacing a sample
        """
        self.table_selected_index = self.sample_table.currentRow()

        self.zero_btn.setDisabled(True)
        self.sample_btn.setDisabled(True)
        self.replace_btn.setDisabled(True)
        self.replace_sample = True
        index = self.sample_table.currentRow()
        self.core.start_sample(self.setting_zero, replacing_sample=True, replacing_sample_index=index)

    def delete_btn_cmd(self) -> None:
        """Prompts user with a single dialog offering to delete a selected sample or all samples."""

        num_rows = self.sample_table.rowCount()  # Total number of samples
        selected_indexes = self.sample_table.selectionModel().selectedRows()  # Get selected rows

        if num_rows == 0:
            QMessageBox.information(self, "No Samples", "There are no samples to delete.")
            return  # No samples to delete

        # Create a custom question dialog with two buttons
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Delete Samples")
        msg_box.setText("What do you want to delete?")
        delete_selected_btn = msg_box.addButton("Delete Selected Sample", QMessageBox.AcceptRole)
        delete_all_btn = msg_box.addButton("Delete All Samples", QMessageBox.DestructiveRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        msg_box.exec_()

        if msg_box.clickedButton() == delete_selected_btn and selected_indexes:
            selected_row = selected_indexes[0].row()  # Get first selected row
            self.core.delete_samples(selected_row)  # Delete selected sample
            self.sample_table.removeRow(selected_row)  # Remove from UI
            self.update_table()  # Refresh UI

        elif msg_box.clickedButton() == delete_all_btn:
            self.core.delete_samples()  # Delete all samples
            self.sample_table.setRowCount(0)  # Clear the table UI
            self.update_table()  # Refresh UI
            
    def closeEvent(self, event: QCloseEvent) -> None:
        print("In close event")
        self.settings = QSettings("laser-level-webcam", "LaserLevelWebcam")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("sensor_width", self.sensor_width_spin.value())
        self.settings.setValue("smoothing", self.smoothing.value())
        self.settings.setValue("subsamples", self.subsamples_spin.value())
        self.settings.setValue("outlier", self.outlier_spin.value())
        self.settings.setValue("units", self.units_combo.currentIndex())
        self.settings.setValue("raw", self.raw_radio.isChecked())
        """Ensure all QThreads are safely closed before exiting."""
        self.core.workerThread.quit()
        self.core.workerThread.wait()
        self.core.sampleWorkerThread.quit()
        self.core.sampleWorkerThread.wait()
        event.accept()
        self.settings.setValue("left_splitter", self.left_splitter.sizes())
        self.settings.setValue("middle_splitter", self.middle_splitter.sizes())
        self.settings.setValue("right_splitter", self.right_splitter.sizes())

        self.settings.setValue("ip_address", self.socket_dialog.ip_line.text())
        self.settings.setValue("port", self.socket_dialog.port_line.text())

        self.core.workerThread.quit()
        self.core.workerThread.wait()
        self.core.sampleWorkerThread.quit()
        self.core.sampleWorkerThread.wait()
        self.deleteLater()
        super().closeEvent(event)


def start() -> None:
    app = QApplication(sys.argv)
    qdarktheme.load_stylesheet("dark")
    

    window = MainWindow()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    start()

