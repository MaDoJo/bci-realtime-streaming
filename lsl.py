
# use pylsl local_clock() function 
"""
Live visualization of EEG stream
"""

import matplotlib.pyplot as plt
from src.inlet import create_inlet
from src.buffer import CircularBuffer
import time 
import numpy as np
import pylsl

FS = 250
BUFFER_SEC = 2
N_CHANNELS = 8

inlet = create_inlet()
buffer = CircularBuffer(FS * BUFFER_SEC, N_CHANNELS)

plt.ion()
fig, ax = plt.subplots()
latencies = []
samples = [] 
timestamps = []
n = 250 * 5
for _ in range(n):
    sample, timestamp = inlet.pull_sample()
    for idx, channel_value in enumerate(sample):
        sample[idx] = channel_value + (idx * -50.0)
    buffer.append(sample)
    data = buffer.get()
    latency = pylsl.local_clock() - timestamp
    latencies.append(latency)
    samples.append(sample)
    timestamps.append(timestamp)
        

    ax.clear()
    ax.plot(data)
    ax.set_title("Live EEG (Simulated)")
    plt.pause(0.01)

