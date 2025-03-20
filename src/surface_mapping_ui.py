import sys
import os
import csv
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QDialog, QLabel, QComboBox,
    QSpinBox, QGridLayout, QMessageBox, QLineEdit, QHBoxLayout, QFileDialog, QGroupBox, QInputDialog
)
import numpy as np

from PySide6.QtGui import QColor




class SurfaceMappingDialog(QDialog):
    def __init__(self, main_window, plate_name=None, rows=4, cols=4):
        super().__init__()
        self.selected_row = None  # ✅ Initialize selected_row
        from src.surface_visualisation import SurfaceMappingTable  # ✅ Lazy import

        self.main_window = main_window
        self.rows = rows
        self.cols = cols

        self.selected_row = None  # ✅ Ensure row selection is initialized
        self.current_col = 0  # ✅ Initialize current column
        self.current_row = 0  # ✅ Initialize current row for cycling
        
        self.measurement_data = {}  # ✅ Initialize dictionary to store measurement values

        # ✅ Define plate_name BEFORE calling init_ui()
        self.plate_name = plate_name if plate_name else "NewPlate"
        
        self.file_path = os.path.join(os.getcwd(), "plate_data", f"{self.plate_name}_measurements.csv")
        self.current_view = "table"  # ✅ Fix: Ensure `current_view` is initialized

        self.visual_table = SurfaceMappingTable(self.rows, self.cols)  # ✅ Instantiate the new table
        self.init_ui()

    def init_ui(self):
        """Initialize the UI layout with a toggle between table and visualization."""
        from src.surface_visualisation import SurfaceMappingTable  # ✅ Lazy import inside function

        self.setWindowTitle("Surface Mapping")
        self.setGeometry(100, 100, 800, 650)

        main_layout = QVBoxLayout()

        # ✅ Plate Info Section
        info_layout = QHBoxLayout()
        self.plate_name_label = QLabel(f"Plate: {self.plate_name}")
        info_layout.addWidget(self.plate_name_label)

        main_layout.addLayout(info_layout)

        # ✅ Create the original QTableWidget (Numerical View)
        self.data_table = QTableWidget(self.rows, self.cols)
        self.data_table.setHorizontalHeaderLabels([str(i + 1) for i in range(self.cols)])
        self.data_table.setVerticalHeaderLabels([chr(65 + i) for i in range(self.rows)])

        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)  # ✅ Ensure  full row selection
        self.data_table.setSelectionMode(QTableWidget.SingleSelection)  # ✅ Only one row at a time
        self.data_table.selectionModel().selectionChanged.connect(self.update_selected_row)

        # ✅ Initialize SurfaceMappingTable after import
        self.visual_table = SurfaceMappingTable(self.rows, self.cols)

        # ✅ Create Toggle Button
        self.toggle_button = QPushButton("Switch to Visualization")
        self.toggle_button.clicked.connect(self.toggle_view)

        # ✅ Create Buttons Layout
        button_layout = QHBoxLayout()
        self.select_plate_button = QPushButton("Select Existing Plate")
        self.select_plate_button.clicked.connect(self.select_existing_plate)
        button_layout.addWidget(self.select_plate_button)

        self.new_plate_button = QPushButton("Create New Plate")
        self.new_plate_button.clicked.connect(self.create_new_plate)
        button_layout.addWidget(self.new_plate_button)

        self.import_measurement_button = QPushButton("Import Measurement")
        self.import_measurement_button.clicked.connect(self.import_computed_measurement)
        button_layout.addWidget(self.import_measurement_button)

        # ✅ Add elements to the layout
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.data_table)  # ✅ Show the numerical table initially
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
       
    def toggle_view(self):
        """✅ Switch between the table view and the visualization view."""

        if not hasattr(self, "current_view"):
            self.current_view = "table"  # ✅ Ensure `current_view` is initialized if missing

        layout = self.layout()

        if self.current_view == "table":
            # ✅ Switch to visualization mode
            layout.replaceWidget(self.data_table, self.visual_table)
            self.data_table.hide()
            self.visual_table.show()
            self.toggle_button.setText("Switch to Table View")
            self.current_view = "visual"
        else:
            # ✅ Switch back to table mode
            layout.replaceWidget(self.visual_table, self.data_table)
            self.visual_table.hide()
            self.data_table.show()
            self.toggle_button.setText("Switch to Visualization")
            self.current_view = "table"

        print(f"[DEBUG] View switched to: {self.current_view}")

    
    def select_existing_plate(self):
        """Prompt user to select an existing plate file."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Existing Plate", "", "CSV Files (*.csv)", options=options)
        if file_path:
            self.plate_name = os.path.basename(file_path).replace("_measurements.csv", "")
            QMessageBox.information(self, "Plate Loaded", f"Loaded {self.plate_name}")
    
    def update_selected_row(self):
        """U`pdate self.selected_row when a row is clicked."""
        selected = self.data_table.selectionModel().selectedRows()
        if selected:
            self.selected_row = selected[0].row()
            print(f"[DEBUG] Row {self.selected_row} selected")  # Debugging output

    def select_row_for_measurement(self):
        """✅ Allow the user to select a row for measurement input."""
        selected = self.data_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "No Row Selected", "Please select a row in the table to record measurements.")
            return

        self.selected_row = selected[0].row()  # ✅ Store selected row
        QMessageBox.information(self, "Row Selected", f"Measurements will be recorded in row {self.selected_row + 1}.")
        
    def clear_selected_row(self):
        """✅ Clear only the selected row in the Surface Mapping Table."""
        selected = self.data_table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "No Row Selected", "Please select a row to clear.")
            return

        row = selected[0].row()
        confirm = QMessageBox.question(
            self, "Confirm Clear", f"Are you sure you want to clear row {row + 1}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            for col in range(self.cols):
                key = (row, col)
                if key in self.visual_table.measurement_data:
                    del self.visual_table.measurement_data[key]  # ✅ Remove data from dictionary
                self.data_table.setItem(row, col, QTableWidgetItem(""))  # ✅ Clear UI cell

            self.visual_table.populate_table_with_plots()
            print(f"[DEBUG] Cleared row {row + 1}.")
        
    def import_computed_measurement(self):
        """✅ Explicitly transfer up to the defined number of columns into the selected row of the Surface Map."""

        # ✅ Ensure a row is selected before importing
        if self.selected_row is None:
            QMessageBox.warning(self, "Error", "Please select a row in the Surface Map before importing.")
            return

        # ✅ Get number of available columns in the Surface Map
        max_columns = self.cols  # Assume `self.cols` is the defined column count

        if hasattr(self.main_window, "collect_measurement_data") and callable(getattr(self.main_window, "collect_measurement_data", None)):
            sample_count = min(self.main_window.sample_table.rowCount(), max_columns)  # ✅ Limit samples to max columns

            for sample_index in range(sample_count):
                (
                    measured_avg, min_value, max_value,
                    avg_shim, min_shim, max_shim,
                    avg_scrape, min_scrape, max_scrape
                ) = self.main_window.collect_measurement_data(sample_index)

                if measured_avg is None:
                    continue  # ✅ Skip empty rows

                surface_row = self.selected_row  # ✅ Store data in the explicitly selected row
                surface_col = sample_index  # ✅ Map sample rows to columns (up to the defined limit)

                # ✅ Store data in the correct Surface Map cell
                self.update_numerical_table(surface_row, surface_col, measured_avg, min_value, max_value, avg_shim, min_shim, max_shim, avg_scrape, min_scrape, max_scrape)

                # ✅ Send data to visualization
                self.visual_table.handle_measurement_import(
                    surface_row, surface_col, measured_avg, min_value, max_value,
                    avg_shim, min_shim, max_shim,
                    avg_scrape, min_scrape, max_scrape
                )

                print(f"[DEBUG] Imported Sample {sample_index} → Surface Map (Row: {surface_row}, Col: {surface_col})")

        else:
            QMessageBox.critical(self, "Error", "Measurement computation function is missing!")

    def update_numerical_table(self, row, col, avg_value, min_value, max_value, avg_shim, min_shim, max_shim, avg_scrape, min_scrape, max_scrape):
        """✅ Store measurement values in a single cell and ensure correct tooltip updates."""

        key = (row, col)

        # ✅ Ensure storage exists
        if key not in self.measurement_data:
            self.measurement_data[key] = {
                "avg": [], "min": [], "max": [],
                "shim_avg": [], "shim_min": [], "shim_max": [],
                "scrape_avg": [], "scrape_min": [], "scrape_max": []
            }

        # ✅ Append new measurement values
        self.measurement_data[key]["avg"].append(avg_value)
        self.measurement_data[key]["min"].append(min_value)
        self.measurement_data[key]["max"].append(max_value)
        self.measurement_data[key]["shim_avg"].append(avg_shim)
        self.measurement_data[key]["shim_min"].append(min_shim)
        self.measurement_data[key]["shim_max"].append(max_shim)
        self.measurement_data[key]["scrape_avg"].append(avg_scrape)
        self.measurement_data[key]["scrape_min"].append(min_scrape)
        self.measurement_data[key]["scrape_max"].append(max_scrape)

        # ✅ Ensure `count` is defined before using it
        count = len(self.measurement_data[key]["avg"])

        # ✅ Compute new display values
        avg_display = np.mean(self.measurement_data[key]["avg"])

        # ✅ Correct tooltip text to match debug output
        tooltip_text = (
            f"📊 Cell ({row}, {col}) Data:\n"
            f"📈 Avg: {avg_display:.2f} | 🔽 Min: {min_value:.2f} | 🔼 Max: {max_value:.2f}\n"
            f"🟢 Shim Avg: {avg_shim:.2f} | 🔽 Shim Min: {min_shim:.2f} | 🔼 Shim Max: {max_shim:.2f}\n"
            f"🔴 Scrape Avg: {avg_scrape:.2f} | 🔽 Scrape Min: {min_scrape:.2f} | 🔼 Scrape Max: {max_scrape:.2f}\n"
            f"📌 Total Samples: {count}"
        )

        # ✅ Update the UI cell
        cell_item = self.data_table.item(row, col)
        if not cell_item:
            cell_item = QTableWidgetItem()
            self.data_table.setItem(row, col, cell_item)

        cell_item.setText(f"Avg: {avg_display:.2f} ({count})")
        cell_item.setToolTip(tooltip_text)  # ✅ Update tooltip with correct stored values

        # ✅ Debugging output
        print(f"[DEBUG] Updated cell ({row}, {col}) with Avg={avg_display:.2f}, Samples={count}")
        print(f"[DEBUG] Tooltip Set: {tooltip_text}")

   
    def update_table_display(self, row, col, count, avg_value):
        """Updates the cell UI with measurement statistics."""
        cell_item = self.table.item(row, col)
        if not cell_item:
            cell_item = QTableWidgetItem()
            self.table.setItem(row, col, cell_item)

        # ✅ Display count & average
        cell_item.setText(f"Avg: {avg_value:.2f} / {count}")

        # ✅ Retrieve detailed data from storage
        pos_label = f"{chr(65 + row)}{col + 1}"
        if pos_label in self.cell_data:
            cell_info = self.cell_data[pos_label]
            count = cell_info["count"]
            avg = cell_info["avg"]
            min_value = cell_info["min"]
            max_value = cell_info["max"]

        # ✅ Set tooltip text (display on hover)
        tooltip_text = (
            f"🔹 Cell: {pos_label}\n"
            f"📊 Count: {count}\n"
            f"📈 Avg: {avg:.2f}\n"
            f"🔽 Min: {min_value}\n"
            f"🔼 Max: {max_value}"
        )
        cell_item.setToolTip(tooltip_text)  # ✅ Show full details on hover

        # ✅ Change color based on data state
        if count == 1:
            cell_item.setBackground(QColor("blue"))  # 🔵 Single measurement
        elif count > 1:
            cell_item.setBackground(QColor("green"))  # 🟢 Multiple measurements
        else:
            cell_item.setBackground(QColor("red"))  # 🔴 Empty cell (should never happen)

    def update_table_size(self):
        """Update table size when row or column values change."""
        self.rows = self.rows_spinbox.value()
        self.cols = self.cols_spinbox.value()
        self.data_table.setRowCount(self.rows)
        self.data_table.setColumnCount(self.cols)
        self.update_table_headers()

    def update_table_headers(self):
        """Update row and column headers when the table size changes."""
        self.data_table.setHorizontalHeaderLabels([str(i+1) for i in range(self.cols)])
        self.data_table.setVerticalHeaderLabels([chr(65+i) for i in range(self.rows)])

    def create_new_plate(self):
        """Prompt user to enter a new plate name, rows, and columns."""
        dialog = QDialog(self)
        dialog.setWindowTitle("New Plate")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter new plate name:"))
        plate_name_input = QLineEdit()
        layout.addWidget(plate_name_input)
        
        layout.addWidget(QLabel("Enter number of rows:"))
        rows_input = QSpinBox()
        rows_input.setRange(1, 100)
        rows_input.setValue(self.rows)
        layout.addWidget(rows_input)
        
        layout.addWidget(QLabel("Enter number of columns:"))
        cols_input = QSpinBox()
        cols_input.setRange(1, 100)
        cols_input.setValue(self.cols)
        layout.addWidget(cols_input)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        def on_ok():
            new_name = plate_name_input.text().strip()
            new_rows = rows_input.value()
            new_cols = cols_input.value()
            if new_name:
                self.plate_name = new_name
                self.rows = new_rows
                self.cols = new_cols
                self.plate_name_label.setText(f"Plate: {self.plate_name}")
                self.data_table.setRowCount(self.rows)
                self.data_table.setColumnCount(self.cols)
                self.update_table_headers()
                self.restore_background_colors()
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "No Plate Created", "No plate name entered.")
        
        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)
        dialog.exec()

    def update_plate_name(self):
        new_name = self.plate_name_input.text().strip()
        if new_name:
            self.plate_name = new_name
            self.file_path = os.path.join(self.plate_data_dir, f"{new_name}_measurements.csv")
            QMessageBox.information(self, "Updated", f"Plate name set to {new_name}.")
    
    def reset_plate_data(self):
        reply = QMessageBox.question(self, "Confirm Reset", "Are you sure you want to reset all data for this plate?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            for row in range(self.rows):
                for col in range(self.cols):
                    item = self.table.item(row, col)
                    item.setText("0")
                    item.setBackground(QColor("red"))
            QMessageBox.information(self, "Reset", "Plate data has been reset.")
    
    def load_existing_measurements(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                data = list(reader)

                for row in data[1:]:  # Skip header
                    if len(row) < 3:
                        continue  # ✅ Skip rows that don't have enough values
                    
                    pos_label, avg_value, count = row[:3]  # ✅ Extract only the first 3 values

                    row_idx = ord(pos_label[0]) - 65  # Convert 'A' to index 0
                    col_idx = int(pos_label[1:]) - 1  # Convert '1' to index 0

                    if not self.table.item(row_idx, col_idx):
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(count)))

                    cell_item = self.table.item(row_idx, col_idx)

                    if count == "1":
                        cell_item.setBackground(QColor("blue"))
                    else:
                        cell_item.setBackground(QColor("green"))

                    cell_item.setText(str(count))

    def save_measurement(self):
        selected = self.table.selectedIndexes()
        if len(selected) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one cell to save measurement.")
            return
        
        if not selected:
            QMessageBox.warning(self, "No Cell Selected", "Please select a cell to save data.")
            return
        
        row = selected[0].row()
        col = selected[0].column()
        pos_label = f"{chr(65 + row)}{col + 1}"

        avg_value = 10.0  # Placeholder for measurement value

        # ✅ Get the existing count, defaulting to 0
        existing_item = self.table.item(row, col)
        existing_count = int(existing_item.text()) if existing_item.text().isdigit() else 0

        # ✅ First measurement case
        if existing_count == 0:
            new_sample = 1
            existing_item.setText(str(new_sample))  # Set to "1"
            existing_item.setBackground(QColor("blue"))  # ✅ Turn Blue
        else:
            # ✅ Subsequent measurements (Green, averaged)
            new_sample = existing_count + 1
            avg_value = (avg_value * existing_count + float(existing_count)) / new_sample
            existing_item.setText(str(new_sample))
            existing_item.setBackground(QColor("green"))

        # ✅ Save measurement to file
        with open(self.file_path, "a", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([pos_label, avg_value, new_sample])

        QMessageBox.information(self, "Saved", f"Measurement saved to {pos_label}.")

    def handle_measurement_import(self, row, col, avg_value, min_value, max_value, avg_shim, min_shim, max_shim, avg_scrape, min_scrape, max_scrape):
        """✅ Debugging: Ensure all dictionary keys exist before use."""

        key = (row, col)

        # ✅ Debugging: Check if key exists
        if key in self.measurement_data:
            print(f"\n[DEBUG] 🔍 Existing cell found for ({row}, {col}) → {self.measurement_data[key]}")
        else:
            print(f"\n[DEBUG] ⚠️ New cell created for ({row}, {col})")

        # ✅ Ensure the dictionary exists
        if key not in self.measurement_data:
            self.measurement_data[key] = {}  # ✅ Initialize dictionary

        # ✅ Debugging: Check the current keys in the dictionary
        print(f"[DEBUG] 🔑 Before key check: {self.measurement_data[key].keys()}")

        # ✅ Ensure all required keys exist before accessing them
        for field in ["avg", "min", "max", "shim", "scrape"]:
            if field not in self.measurement_data[key]:  
                self.measurement_data[key][field] = []  # ✅ Initialize as empty list

        # ✅ Debugging: Check the updated dictionary structure
        print(f"[DEBUG] 🔑 After key check: {self.measurement_data[key].keys()}")

        # ✅ Append new measurement values
        self.measurement_data[key]["avg"].append(avg_value)
        self.measurement_data[key]["min"].append(min_value)
        self.measurement_data[key]["max"].append(max_value)

        # ✅ Append shim and scrape values correctly
        self.measurement_data[key]["shim"].append((avg_shim, min_shim, max_shim))
        self.measurement_data[key]["scrape"].append((avg_scrape, min_scrape, max_scrape))

        # ✅ Debugging output for stored values
        print(f"\n💾 [DEBUG] Stored Data for Cell ({row}, {col}):")
        print(f"   - Avg Measurements: {self.measurement_data[key]['avg']}")
        print(f"   - Min Values: {self.measurement_data[key]['min']}")
        print(f"   - Max Values: {self.measurement_data[key]['max']}")

        # ✅ Check if "shim" exists before printing
        if "shim" in self.measurement_data[key]:
            print(f"   - Shim Values: {self.measurement_data[key]['shim']}")
        else:
            print(f"⚠️ [ERROR] 'shim' key is missing for ({row}, {col})!")

        # ✅ Check if "scrape" exists before printing
        if "scrape" in self.measurement_data[key]:
            print(f"   - Scrape Values: {self.measurement_data[key]['scrape']}")
        else:
            print(f"⚠️ [ERROR] 'scrape' key is missing for ({row}, {col})!")

        # ✅ Refresh visualization
        self.populate_table_with_plots()





    def clear_selected_cells(self):
        selected = self.data_table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "No Cell Selected", "Please select a row to clear.")
            return

        row = selected[0].row()
        confirm = QMessageBox.question(
            self, "Confirm Clear", f"Are you sure you want to clear row {row + 1}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            for col in range(self.cols):
                key = (row, col)
                if key in self.visual_table.measurement_data:
                    del self.visual_table.measurement_data[key]  # ✅ Remove data from dictionary
                self.data_table.setItem(row, col, QTableWidgetItem(""))  # ✅ Clear UI cell

            self.visual_table.populate_table_with_plots()
            print(f"[DEBUG] Cleared row {row + 1}.")

    def clear_selected_cells(self):
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "No Cell Selected", "Please select a cell to clear.")
            return
        reply = QMessageBox.question(self, "Confirm Clear", "Are you sure you want to clear the selected cells?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        row = selected[0].row()
        col = selected[0].column()
        pos_label = f"{chr(65 + row)}{col + 1}"
        
        reply = QMessageBox.question(self, "Confirm Delete", f"Clear data for selected range?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for index in selected:
                row = index.row()
                col = index.column()
                self.table.setItem(row, col, QTableWidgetItem("0"))
                self.table.item(row, col).setBackground(QColor("red"))
            QMessageBox.information(self, "Cleared", "Selected cells have been cleared.")

    def restore_background_colors(self):
        """Restore default background colors based on data."""
        for row in range(self.rows):
            for col in range(self.cols):
                item = self.data_table.item(row, col)
                if item:
                    count = int(item.text()) if item.text().isdigit() else 0
                    if count == 0:
                        item.setBackground(QColor("red"))  # ✅ Start as Red
                    elif count == 1:
                        item.setBackground(QColor("blue"))  # ✅ First measurement (Blue)
                    else:
                        item.setBackground(QColor("green"))  # ✅ Multiple measurements (Green)
                    
                    # ✅ Ensure the style is cleared before selection
                    item.setData(1, "")
        
        # ✅ Now, override selected cell color to Purple (🟣)
        selected = self.data_table.selectedIndexes()
        for index in selected:
            item = self.data_table.item(index.row(), index.column())
            if item:
                item.setBackground(QColor("purple"))  # ✅ Change to Purple when selected
                item.setData(1, "selected")  # ✅ Track selection with metadata

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = SurfaceMappingDialog(None)
    dialog.show()
    sys.exit(app.exec())
