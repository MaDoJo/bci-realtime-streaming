import sys
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
from pylsl import StreamInlet, resolve_byprop

class EEGVisualizer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Initialize LSL Connection
        print("Connecting to EEG stream...")
        streams = resolve_byprop("type", "EEG")
        self.inlet = StreamInlet(streams[0])
        
        # 2. Setup Data Windows (Keep history small to save memory)
        self.window_size = 1000
        self.data = np.zeros(self.window_size)
        
        # 3. Setup High-Performance UI Layout
        self.win = pg.GraphicsLayoutWidget(title="Optimized LSL EEG Plot")
        self.setCentralWidget(self.win)
        self.plot = self.win.addPlot(title="Channel 1 (Live)")
        self.curve = self.plot.plot(pen='y') # Yellow line
        
        # 4. Decouple Plotting from Ingestion using a QTimer
        # This keeps the UI rendering speed independent of the data speed
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(16) # ~60 Frames Per Second maximum
        
    def update_loop(self):
        # Pull ALL available samples currently waiting in the buffer
        # This prevents the buffer from backing up during a slow render frame
        samples_pulled = 0
        while True:
            sample, timestamp = self.inlet.pull_sample(timeout=0.0)
            if timestamp is None:
                break # Buffer is empty, proceed to draw
                
            # Shift data array and insert new sample point
            self.data = np.roll(self.data, -1)
            self.data[-1] = sample[0] # Track channel 0
            samples_pulled += 1
            
        # Only update the screen if new data actually arrived
        if samples_pulled > 0:
            # `setData` updates existing array memory instead of allocating new memory
            self.curve.setData(self.data)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = EEGVisualizer()
    main.show()
    sys.exit(app.exec_())