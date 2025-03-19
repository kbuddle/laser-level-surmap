from __future__ import annotations

from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFormLayout
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSpinBox


class CyclicMeasurementSetupWindow(QDialog):  # type: ignore
    """
    Represents a non-modal dialog that allows to start/stop cyclic measurements and adjust the interval
    between measurements

    Also handles starting/stopping the timer. Parent class is expected to actually perform the
    measurements when onMeasurementTrigger signal is emitted.
    """

    cycle_time_sb: QSpinBox
    cycle_timer: QTimer
    pb_start: QPushButton
    pb_stop: QPushButton

    onMeasurementTrigger = Signal()

    def __init__(self, parent: Any) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cyclic measurement setup")
        self.setModal(False)

        # Layouts
        fl = QFormLayout(self)

        # Widgets
        self.cycle_time_sb = QSpinBox(self)
        self.cycle_time_sb.setValue(10)
        self.cycle_time_sb.setMinimum(5 )
        self.cycle_time_sb.setMaximum(3600)
        fl.addRow("Cycle time (s)", self.cycle_time_sb)

        # Total Duration Input
        self.total_duration_sb = QSpinBox(self)
        self.total_duration_sb.setValue(60)  # Default 60s
        self.total_duration_sb.setMinimum(5)  # Minimum 5s
        self.total_duration_sb.setMaximum(3600)  # Max 1 hour
        fl.addRow("Total duration (s)", self.total_duration_sb)



        self.pb_start = QPushButton("Start", self)
        self.pb_stop = QPushButton("Stop", self)
        self.pb_stop.setEnabled(False)

        fl.addRow(self.pb_start, self.pb_stop)

        # Timer Setup
        self.cycle_timer = QTimer(self)
        self.cycle_timer.timeout.connect(self.on_timer_tick)

        # State Tracking
        self.elapsed_cycles = 0  # Track elapsed cycles

        # Button Logic
        self.pb_start.released.connect(self.start_cycle)
        self.pb_stop.released.connect(self.stop_cycle)
        
    def start_cycle(self) -> None:
        """
        Starts the cyclic measurement process based on the cycle time and total duration.
        """
        self.elapsed_cycles = 0  # Reset counter
        self.cycle_timer.setInterval(1000 * self.cycle_time_sb.value())  # Convert to milliseconds
        self.cycle_timer.start()

        self.pb_start.setEnabled(False)
        self.pb_stop.setEnabled(True)

    def on_timer_tick(self) -> None:
        """
        Handles the timer event, triggers measurement, and stops when duration is met.
        """
        self.onMeasurementTrigger.emit()  # Emit the signal for measurement
        self.elapsed_cycles += 1

        # Calculate total allowed cycles based on duration
        max_cycles = self.total_duration_sb.value() // self.cycle_time_sb.value()
        if self.elapsed_cycles >= max_cycles:
            self.stop_cycle()

    def stop_cycle(self) -> None:
        self.cycle_timer.stop()
        self.pb_stop.setEnabled(False)
        self.pb_start.setEnabled(True)
