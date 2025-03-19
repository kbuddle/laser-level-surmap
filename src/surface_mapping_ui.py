import sys
import os
import csv
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QDialog, QLabel, QComboBox,
    QSpinBox, QGridLayout, QMessageBox, QLineEdit, QHBoxLayout, QFileDialog, QGroupBox, QInputDialog
)
from PySide6.QtGui import QColor

class SurfaceMappingDialog(QDialog):
    def __init__(self, main_window, plate_name=None, rows=4, cols=4):
        super().__init__()
        self.cell_data = {} #create a dictionary for storing cell data
        self.main_window = main_window
        self.rows = rows
        self.cols = cols
        self.plate_data_dir = os.path.abspath(os.path.join(os.getcwd(), 'plate_data'))
        os.makedirs(self.plate_data_dir, exist_ok=True)
        
        # ✅ Modify to start with a blank sheet instead of opening a file picker
        self.plate_name = plate_name if plate_name else "NewPlate"
        self.file_path = os.path.join(self.plate_data_dir, f"{self.plate_name}_measurements.csv")
        
        self.init_ui()
        self.table.itemSelectionChanged.connect(self.restore_background_colors)
        self.import_measurement_button.clicked.connect(lambda: print("[DEBUG] Import Measurement Button Clicked!") or self.import_computed_measurement())


    def init_ui(self):
        """Initialize the UI layout and add the Surface Map box."""
        self.setWindowTitle("Surface Mapping")
        self.setGeometry(100, 100, 600, 450)
        
        main_layout = QVBoxLayout()
        surface_map_widget = QGroupBox("Surface Map")
        surface_map_layout = QVBoxLayout()
        
        # ✅ Layout for Plate Name, Rows, and Columns
        info_layout = QHBoxLayout()
        self.plate_name_label = QLabel(f"Plate: {self.plate_name}")
        
        info_layout.addWidget(self.plate_name_label)

        surface_map_layout.addLayout(info_layout)
        
        self.table = QTableWidget(self.rows, self.cols)
        self.update_table_headers()
        self.restore_background_colors()
        surface_map_layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.select_plate_button = QPushButton("Select Existing Plate")
        self.select_plate_button.clicked.connect(self.select_existing_plate)
        button_layout.addWidget(self.select_plate_button)
        
        self.new_plate_button = QPushButton("Create New Plate")
        self.new_plate_button.clicked.connect(self.create_new_plate)
        button_layout.addWidget(self.new_plate_button)
        
        self.import_measurement_button = QPushButton("Import Measurement")
        button_layout.addWidget(self.import_measurement_button)
        
        surface_map_layout.addLayout(button_layout)  # ✅ Buttons moved inside Surface Map
        
        surface_map_widget.setLayout(surface_map_layout)
        main_layout.addWidget(surface_map_widget)
        self.setLayout(main_layout)

        """  for row in range(self.rows):
            for col in range(self.cols):
                item = QTableWidgetItem("0")
                item.setBackground(QColor("red"))
                self.table.setItem(row, col, item)
         """
       
    def select_existing_plate(self):
        """Prompt user to select an existing plate file."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Existing Plate", "", "CSV Files (*.csv)", options=options)
        if file_path:
            self.plate_name = os.path.basename(file_path).replace("_measurements.csv", "")
            QMessageBox.information(self, "Plate Loaded", f"Loaded {self.plate_name}")
    
    def import_computed_measurement(self):
        """Fetch computed statistics (avg, min, max, count) and store them in the table."""
        print("[DEBUG] import_computed_measurement() called!")

        if hasattr(self.main_window, 'compute_overall_measurement'):
            avg_value, min_value, max_value, count = self.main_window.compute_overall_measurement()  # ✅ Unpack returned values
        else:
            print("[ERROR] compute_overall_measurement() not found in MainWindow!")
            QMessageBox.critical(self, "Error", "Measurement computation function is missing!")
            return

        if avg_value is None:
            print("[WARNING] No valid data found to compute average!")
            QMessageBox.warning(self, "No Data", "No valid measurement data found.")
            return

        print(f"[DEBUG] Computed Measurement: Avg={avg_value}, Min={min_value}, Max={max_value}, Count={count}")

        # ✅ Pass all values correctly
        self.handle_measurement_import(avg_value, min_value, max_value, count)



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
        self.table.setRowCount(self.rows)
        self.table.setColumnCount(self.cols)
        self.update_table_headers()

    def update_table_headers(self):
        """Update row and column headers when the table size changes."""
        self.table.setHorizontalHeaderLabels([str(i+1) for i in range(self.cols)])
        self.table.setVerticalHeaderLabels([chr(65+i) for i in range(self.rows)])

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
                self.table.setRowCount(self.rows)
                self.table.setColumnCount(self.cols)
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

    def handle_measurement_import(self, avg_value: float, min_value: float, max_value: float, count: int):
        """Stores and updates measurement statistics for a selected cell."""
        print(f"[DEBUG] handle_measurement_import called with Avg={avg_value}, Min={min_value}, Max={max_value}, Count={count}")

        selected = self.table.selectedIndexes()
        if not selected:
            print("[DEBUG] No cell selected!")
            QMessageBox.warning(self, "No Cell Selected", "Please select a cell to store the measurement.")
            return

        row = selected[0].row()
        col = selected[0].column()
        pos_label = f"{chr(65 + row)}{col + 1}"

        print(f"[DEBUG] Cell selected at {pos_label}")

        # ✅ Initialize cell data storage if not already stored
        if pos_label not in self.cell_data:
            self.cell_data[pos_label] = {
                "count": count,
                "avg": avg_value,
                "min": min_value,
                "max": max_value
            }
        else:
            # ✅ Retrieve existing values
            cell_info = self.cell_data[pos_label]
            prev_count = cell_info["count"]
            prev_avg = cell_info["avg"]
            prev_min = cell_info["min"]
            prev_max = cell_info["max"]

            # ✅ Compute new rolling statistics
            new_count = prev_count + count
            new_avg = ((prev_avg * prev_count) + (avg_value * count)) / new_count
            new_min = min(prev_min, min_value)  # ✅ Ensure min updates only if new measurement is lower
            new_max = max(prev_max, max_value)  # ✅ Ensure max updates only if new measurement is higher

            # ✅ Store updated statistics
            self.cell_data[pos_label] = {
                "count": new_count,
                "avg": new_avg,
                "min": new_min,
                "max": new_max
            }

        # ✅ Debugging Output
        print(f"[DEBUG] Updated {pos_label}: Count={self.cell_data[pos_label]['count']}, "
            f"Avg={self.cell_data[pos_label]['avg']:.2f}, Min={self.cell_data[pos_label]['min']}, "
            f"Max={self.cell_data[pos_label]['max']}")

        # ✅ Update table display
        self.update_table_display(row, col, self.cell_data[pos_label]["count"], self.cell_data[pos_label]["avg"])

        # ✅ Save to file (optional)
        try:
            with open(self.file_path, "a", newline='', encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([pos_label, self.cell_data[pos_label]["count"], self.cell_data[pos_label]["avg"],
                                self.cell_data[pos_label]["min"], self.cell_data[pos_label]["max"]])
                print(f"[DEBUG] Measurement saved to file at {self.file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save measurement: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save measurement: {e}")

    def update_table_headers(self):
        """Update row and column headers when the table size changes."""
        self.table.setHorizontalHeaderLabels([str(i+1) for i in range(self.cols)])
        self.table.setVerticalHeaderLabels([chr(65+i) for i in range(self.rows)])
    


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
                item = self.table.item(row, col)
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
        selected = self.table.selectedIndexes()
        for index in selected:
            item = self.table.item(index.row(), index.column())
            if item:
                item.setBackground(QColor("purple"))  # ✅ Change to Purple when selected
                item.setData(1, "selected")  # ✅ Track selection with metadata

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = SurfaceMappingDialog()
    dialog.show()
    sys.exit(app.exec())
