#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np

from weibull_premptive_lifo2 import Queues
from part2 import MonitorSIR,compute_time_averaged_fractions

max_queue_length = 15

shapes = [0.5, 1,4]
choices = [0.5,0.9,0.95,0.99]
mu = 1
max_t = 1000
n_servers=10
plot_interval=1



plt.figure(figsize=(18, 14))
for idx, lambd in enumerate(choices, 1):
    plt.subplot(2, 2, idx)
    queue_snapshots = {shape: [] for shape in shapes}
    # print(queue_snapshots)
    for shape in shapes:
        sim = Queues(lambd, mu, n_servers, 1,shape)
        sim.schedule(0, MonitorSIR(lambd,queue_snapshots,shape,plot_interval))
        sim.run(max_t)
  
        snapshots=np.array(queue_snapshots[shape])
        # Compute time-averaged fractions for each λ
        time_averaged_fractions = compute_time_averaged_fractions(snapshots, max_queue_length)

        plt.plot(
                range(max_queue_length + 1),
                time_averaged_fractions,
                label=f"shape = {shape}"
            )
        plt.title(f"lambda = {lambd}")
        plt.xlabel("Queue Length (x)")
        plt.ylabel("Fraction of Queues with Size ≥ x")
        plt.legend(loc="upper right")
        plt.grid(True)


plt.suptitle("Simulated Queue Lengths for Various Arrival Rates (preemptive LIFO)", fontsize=16, y=0.98)  # Add a global title
plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.subplots_adjust(hspace=0.4, wspace=0.3)
plt.show()