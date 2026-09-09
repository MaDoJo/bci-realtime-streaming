"""
Live visualization of EEG stream
"""

import sys
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
import pylsl
from src.inlet import create_inlet
from src.buffer import CircularBuffer

FS = 250
BUFFER_SEC = 2
N_CHANNELS = 8

class EEGVisualizer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Initialize LSL Connection
        self.inlet = create_inlet()
        
        # 2. Setup Data Windows (Keep history small to save memory)
        self.buffer = CircularBuffer(FS * BUFFER_SEC, N_CHANNELS)
        
        self.n = 250 * 60 
        self.s = 0
        self.latencies = np.zeros(self.n)
        self.samples = np.zeros((self.n, N_CHANNELS))
        self.timestamps = np.zeros(self.n)
        
        # 3. Setup High-Performance UI Layout
        self.win = pg.GraphicsLayoutWidget(title="Optimized LSL EEG Plot")
        self.setCentralWidget(self.win)
        self.plot = self.win.addPlot(title="Live EEG")
        
        self.curves = [self.plot.plot() for _ in range(N_CHANNELS)]
        
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
                
            # multiply channel index by -50 mV for channel spacing
            for idx, channel_value in enumerate(sample):
                sample[idx] = channel_value + (idx * -50.0)
                
            self.buffer.append(sample)
            latency = pylsl.local_clock() - timestamp
            
            # store raw values for post run analysis
            self.latencies[self.s] = latency
            self.samples[self.s] = sample
            self.timestamps[self.s] = timestamp
            
            self.s += 1
            samples_pulled += 1

            #if self.s >= self.n:
            if timestamp - self.timestamps[0] > 10.0: 
                self.timer.stop()
                self.run_analysis()
                return

        # Only update the screen if new data actually arrived
        if samples_pulled > 0:
            data = self.buffer.get()
            # `setData` updates existing array memory instead of allocating new memory
            for i in range(N_CHANNELS):
                self.curves[i].setData(data[:, i])
                
    def run_analysis(self):
        throughput = self.s / (self.timestamps[self.s - 1] - self.timestamps[0])
        print(self.s)
        intervals = np.diff(self.timestamps[:self.s])
        jitter = np.std(intervals[:self.s]) * 1000.0
        mean_latency = np.mean(self.latencies[:self.s])

        print("DIAGNOSTIC BREAKDOWN:\n")
        print(f"Effective Throughput: {throughput:.2f} Hz")
        print(f"Inter-Sample Jitter:  {jitter:.4f} ms")
        print(f"Mean Latency:         {mean_latency:.4f} s")
        
        QtWidgets.QApplication.quit()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = EEGVisualizer()
    main.show()
    sys.exit(app.exec_())