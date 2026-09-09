"""
Live visualization of EEG stream
"""

import matplotlib.pyplot as plt
from src.inlet import create_inlet
from src.buffer import CircularBuffer
import numpy as np
import pylsl

FS = 250
BUFFER_SEC = 2
N_CHANNELS = 8
DURATION = 60
start_time = pylsl.local_clock()

inlet = create_inlet()
buffer = CircularBuffer(FS * BUFFER_SEC, N_CHANNELS)

plt.ion()
fig, ax = plt.subplots()

latencies = []
samples = []
timestamps = []

while pylsl.local_clock() - start_time < DURATION:
    sample, timestamp = inlet.pull_sample()

    # multiply channel index by -50 mV for channel spacing
    for idx, channel_value in enumerate(sample):
        sample[idx] = channel_value + (idx * -50.0)

    buffer.append(sample)
    data = buffer.get()
    latency = pylsl.local_clock() - timestamp
    
    latencies.append(latency)
    samples.append(sample.copy())
    timestamps.append(timestamp)

    # plotting code (causes latency)
    ax.clear()
    ax.plot(data)
    ax.set_title("Live EEG (Simulated)")
    plt.pause(0.01)


throughput = len(timestamps) / (timestamps[-1] - timestamps[0])
intervals = np.diff(timestamps)
jitter = np.std(intervals) * 1000.0
mean_latency = np.mean(latencies)

print("DIAGNOSTIC BREAKDOWN:\n")
print(f"Effective Throughput: {throughput:.2f} Hz")
print(f"Inter-Sample Jitter:  {jitter:.4f} ms")
print(f"Mean Latency:         {mean_latency:.4f} s")