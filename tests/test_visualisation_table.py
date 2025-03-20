import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (
    QTableWidget, QApplication, QVBoxLayout, QWidget, QLabel, 
    QHBoxLayout, QFrame, QSlider
)
from PySide6.QtCore import Qt
import sys


class SurfaceMappingTable(QWidget):  # ✅ Change from QTableWidget to QWidget to allow layout
    def __init__(self, rows, cols):
        super().__init__()
        self.setWindowTitle("Surface Measurement Table")

        # ✅ Create main layout
        main_layout = QVBoxLayout(self)

        # ✅ Zero Point Adjustment Slider
        self.zero_point_slider = QSlider(Qt.Horizontal)
        self.zero_point_slider.setMinimum(-100)  # Represents -10 mm
        self.zero_point_slider.setMaximum(100)   # Represents +10 mm
        self.zero_point_slider.setValue(0)       # Default zero point (0 mm)
        self.zero_point_slider.setTickPosition(QSlider.TicksBelow)
        self.zero_point_slider.setTickInterval(10)
        self.zero_point_slider.valueChanged.connect(self.update_zero_point)  # Update when changed
        
        # ✅ Zero Label to Display Current Value
        self.zero_label = QLabel("Zero Point: 0.0 mm")

        zero_layout = QHBoxLayout()
        zero_layout.addWidget(QLabel("Adjust Zero Point:"))
        zero_layout.addWidget(self.zero_point_slider)
        zero_layout.addWidget(self.zero_label)

        # ✅ Create Table Widget
        self.table = QTableWidget(rows, cols)
        
        # ✅ Add UI elements to layout
        main_layout.addLayout(zero_layout)  # Add zero point slider
        main_layout.addWidget(self.table)   # Add table
        main_layout.addLayout(self.create_legend())  # Add legend
        
        self.populate_table_with_plots()

    def populate_table_with_plots(self):
        """Fill table with embedded candlestick plots and adjust cell size."""
        self.table.setRowCount(4)
        self.table.setColumnCount(4)

        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 150)  # ✅ Increase cell height

            for col in range(self.table.columnCount()):
                self.table.setColumnWidth(col, 150)  # ✅ Increase column width
                self.table.setCellWidget(row, col, self.create_candlestick_plot(row, col, self.get_zero_point()))

    def create_candlestick_plot(self, row, col, zero_point):
        """Generate a candlestick plot for a table cell, adjusting scrape/shim based on zero reference."""
        fig, ax = plt.subplots(figsize=(3.5, 3.5))  # ✅ Increased figure size

        # Simulated Data (Replace with actual measurements)
        avg_value = np.random.uniform(0, 1)
        min_value = avg_value - np.random.uniform(0.1, 0.2)
        max_value = avg_value + np.random.uniform(0.1, 0.2)

        # ✅ Adjust shim & scrape based on the new zero reference
        avg_shim = max(0, zero_point - avg_value)  # Shim only if below zero point
        min_shim = max(0, zero_point - min_value)
        max_shim = max(0, zero_point - max_value)

        avg_scrape = max(0, avg_value - zero_point)  # Scrape only if above zero point
        min_scrape = max(0, min_value - zero_point)
        max_scrape = max(0, max_value - zero_point)

        # ✅ Plot Min-Max-Average as a Vertical Line
        ax.plot([1, 1], [min_value, max_value], color="black", lw=3)
        ax.scatter([1], [avg_value], color="blue", label="Avg Measurement")

        # ✅ Overlay Scrape and Shim regions
        ax.plot([1.1, 1.1], [min_scrape, max_scrape], color="red", lw=3, label="Scrape Range")
        ax.plot([0.9, 0.9], [min_shim, max_shim], color="green", lw=3, label="Shim Range")

        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"({row}, {col})", fontsize=12)  # ✅ Larger font

        fig.tight_layout()
        canvas = FigureCanvas(fig)
        plot_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(canvas)
        layout.setContentsMargins(0, 0, 0, 0)  # ✅ Remove extra padding
        plot_widget.setLayout(layout)

        return plot_widget

    def get_zero_point(self):
        """Convert slider value to real-world zero point (-10 to +10 mm)."""
        return self.zero_point_slider.value() / 10  # Convert from slider range (-100 to 100) to (-10 mm to +10 mm)

    def update_zero_point(self):
        """Recalculate all plots based on the new zero reference."""
        zero_value = self.get_zero_point()
        self.zero_label.setText(f"Zero Point: {zero_value:.1f} mm")  # Update label display

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
