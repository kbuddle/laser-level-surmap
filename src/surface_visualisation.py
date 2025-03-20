import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (
    QTableWidget, QApplication, QVBoxLayout, QWidget, QLabel, 
    QHBoxLayout, QFrame, QSlider, QMessageBox
)
from PySide6.QtCore import Qt
import sys


class SurfaceMappingTable(QWidget):  # ✅ Change from QTableWidget to QWidget to allow layout
    def __init__(self, rows, cols):
        super().__init__()
        self.setWindowTitle("Surface Measurement Table")
        self.rows = rows
        self.cols = cols
        
        self.measurement_data = {}  # ✅ Store actual measurement values
        
        # ✅ Create a QTableWidget inside SurfaceMappingTable
        self.table = QTableWidget(self.rows, self.cols)  
        self.table.setHorizontalHeaderLabels([str(i + 1) for i in range(self.cols)])
        self.table.setVerticalHeaderLabels([chr(65 + i) for i in range(self.rows)])

        # ✅ Add Zero Point Label
        self.zero_label = QLabel("Zero Point: 0.0 mm")  # ✅ Fix: Ensure label exists

        # ✅ Add Zero Point Slider (default 0)
        self.zero_point_slider = QSlider(Qt.Horizontal)
        self.zero_point_slider.setMinimum(-100)
        self.zero_point_slider.setMaximum(100)
        self.zero_point_slider.setValue(0)  # Default zero point at 0
        self.zero_point_slider.valueChanged.connect(self.update_zero_point)
        
        self.init_ui()

    def init_ui(self):
        """✅ Setup layout with the QTableWidget inside."""
        layout = QVBoxLayout()
        layout.addWidget(self.table)  # ✅ Now `self.table` exists
        layout.addWidget(self.zero_label)  # ✅ Fix: Add label to layout
        layout.addWidget(self.zero_point_slider)  # ✅ Add the zero slider
        self.setLayout(layout)

        self.populate_table_with_plots()  # ✅ Ensure plots are populated

    def populate_table_with_plots(self):
        """✅ Fix: Ensure table exists before trying to update it."""

        # ✅ Check if table exists before accessing it
        if not hasattr(self, "table") or self.table is None:
            print("[ERROR] ❌ Table does not exist! Creating a new one...")
            self.create_table()  # ✅ Ensure table is recreated before use
            return  # ✅ Prevent crashing by stopping execution if table was missing

        try:
            # ✅ Clear previous widgets to avoid duplicate legends
            while self.layout().count() > 0:
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # ✅ Add single legend at the top
            fig, ax = plt.subplots(figsize=(6, 1))  # ✅ Legend size
            ax.set_axis_off()

            legend_elements = [
                plt.Line2D([0], [0], color="black", lw=2, label="Min-Max Range"),
                plt.Line2D([0], [0], marker="_", color="blue", markersize=12, lw=0, label="Avg Measurement"),
                plt.Line2D([0], [0], marker="o", color="green", markersize=10, lw=0, label="Shim Measurement"),
                plt.Line2D([0], [0], marker="s", color="red", markersize=10, lw=0, label="Scrape Measurement"),
            ]
            ax.legend(handles=legend_elements, loc="center", fontsize=10, ncol=4)
            legend_canvas = FigureCanvas(fig)
            self.layout().addWidget(legend_canvas)

            # ✅ Populate each cell with its corresponding plot
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    self.table.setCellWidget(row, col, self.create_candlestick_plot(row, col, self.get_zero_point()))

        except RuntimeError as e:
            print(f"[ERROR] ❌ RuntimeError encountered: {e}")



    def handle_measurement_import(self, row, col, avg_value, min_value, max_value, avg_shim, min_shim, max_shim, avg_scrape, min_scrape, max_scrape):
        """✅ Store all measurement samples in a single cell, ensuring a consistent data structure."""

        key = (row, col)

        # ✅ Always ensure the cell dictionary exists
        if key not in self.measurement_data:
            self.measurement_data[key] = {}  # ✅ Initialize dictionary

        # ✅ Ensure all required keys exist and are standardized
        required_keys = [
            "avg", "min", "max", 
            "shim_avg", "shim_min", "shim_max", 
            "scrape_avg", "scrape_min", "scrape_max"
        ]
        
        for field in required_keys:
            if field not in self.measurement_data[key]:
                self.measurement_data[key][field] = []  # ✅ Initialize as empty list

        # ✅ Append new measurement values correctly
        self.measurement_data[key]["avg"].append(avg_value)
        self.measurement_data[key]["min"].append(min_value)
        self.measurement_data[key]["max"].append(max_value)

        self.measurement_data[key]["shim_avg"].append(avg_shim)  # ✅ Standardized naming
        self.measurement_data[key]["shim_min"].append(min_shim)
        self.measurement_data[key]["shim_max"].append(max_shim)

        self.measurement_data[key]["scrape_avg"].append(avg_scrape)  # ✅ Standardized naming
        self.measurement_data[key]["scrape_min"].append(min_scrape)
        self.measurement_data[key]["scrape_max"].append(max_scrape)

        # ✅ Debugging output to validate stored data
        print(f"\n💾 [DEBUG] Stored Data for Cell ({row}, {col}):")
        print(f"   - Avg Measurements: {self.measurement_data[key]['avg']}")
        print(f"   - Min Values: {self.measurement_data[key]['min']}")
        print(f"   - Max Values: {self.measurement_data[key]['max']}")
        print(f"   - Shim Avg: {self.measurement_data[key]['shim_avg']}")
        print(f"   - Shim Min: {self.measurement_data[key]['shim_min']}")
        print(f"   - Shim Max: {self.measurement_data[key]['shim_max']}")
        print(f"   - Scrape Avg: {self.measurement_data[key]['scrape_avg']}")
        print(f"   - Scrape Min: {self.measurement_data[key]['scrape_min']}")
        print(f"   - Scrape Max: {self.measurement_data[key]['scrape_max']}")

        # ✅ Refresh visualization
        self.populate_table_with_plots()

        


    def create_candlestick_plot(self, row, col, zero_point):
        """✅ Improved Candlestick Plot: Enlarged and More Readable"""

        fig, ax = plt.subplots(figsize=(4, 4))  # ✅ Increased plot size

        key = (row, col)

        if key in self.measurement_data:
            data = self.measurement_data[key]

            avg_values = data.get("avg", [])
            min_values = data.get("min", [])
            max_values = data.get("max", [])
            shim_values = data.get("shim_avg", [])
            scrape_values = data.get("scrape_avg", [])

            sample_count = len(avg_values)

            if sample_count == 0:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center', fontsize=10)
                ax.set_xticks([])
                ax.set_yticks([])
                fig.tight_layout()
                return FigureCanvas(fig)

            # ✅ Ensure all lists match in length
            shim_values = shim_values[:sample_count] if len(shim_values) > sample_count else shim_values + [None] * (sample_count - len(shim_values))
            scrape_values = scrape_values[:sample_count] if len(scrape_values) > sample_count else scrape_values + [None] * (sample_count - len(scrape_values))

            # ✅ Calculate min, max, and avg for visualization
            avg_value = np.mean(avg_values)
            min_value = min(min_values)
            max_value = max(max_values)

            # ✅ Draw the candlestick-like visualization
            ax.vlines(x=1, ymin=min_value, ymax=max_value, color="black", linewidth=3, label="Min-Max Range")
            ax.scatter(1, avg_value, color="blue", s=80, marker="_")  # ✅ Larger Avg Marker
            ax.scatter(1, shim_values[-1], color="green", s=70, marker="o")  # ✅ Larger Shim Marker
            ax.scatter(1, scrape_values[-1], color="red", s=70, marker="s")  # ✅ Larger Scrape Marker

            # ✅ Remove per-cell legends (Handled in global legend)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"({row}, {col})", fontsize=10)  # ✅ Increased font size

            fig.tight_layout()
            return FigureCanvas(fig)
        else:
            ax.text(0.5, 0.5, "No Data", ha='center', va='center', fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])
            fig.tight_layout()
            return FigureCanvas(fig)





    def get_zero_point(self):
        """✅ Get zero point from slider or default to 0."""
        if hasattr(self, 'zero_point_slider'):
            return self.zero_point_slider.value() / 10  # Convert range (-100 to 100) to (-10 mm to +10 mm)
        return 0
        
    def update_zero_point(self):
        """✅ Recalculate all plots based on the new zero reference."""
        zero_value = self.get_zero_point()

        if hasattr(self, "zero_label"):  # ✅ Prevent attribute error
            self.zero_label.setText(f"Zero Point: {zero_value:.1f} mm")  # ✅ Update label display

        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                self.table.setCellWidget(row, col, self.create_candlestick_plot(row, col, zero_value))


    def create_legend(self):
        """Create a legend for the table footer."""
        legend_layout = QHBoxLayout()

        # Helper function to create colored labels
        def create_legend_label(color, text):
            label_layout = QHBoxLayout()
            color_box = QFrame()
            color_box.setFixedSize(15, 15)
            color_box.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
            label_text = QLabel(text)
            label_layout.addWidget(color_box)
            label_layout.addWidget(label_text)
            legend_item = QWidget()
            legend_item.setLayout(label_layout)
            return legend_item

        # ✅ Add color-coded legend items
        legend_layout.addWidget(create_legend_label("black", "Measured Min/Max Range"))
        legend_layout.addWidget(create_legend_label("blue", "Avg Measurement"))
        legend_layout.addWidget(create_legend_label("red", "Scrape (Remove Material)"))
        legend_layout.addWidget(create_legend_label("green", "Shim (Add Material)"))

        return legend_layout


if __name__ == "__main__":
    app = QApplication(sys.argv)
    table = SurfaceMappingTable(4, 4)
    table.show()
    sys.exit(app.exec())
