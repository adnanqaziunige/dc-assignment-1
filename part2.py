#!/usr/bin/env python3


import matplotlib.pyplot as plt
import numpy as np
from discrete_event_sim import Event
from queue_sim import Queues


lambdas = [0.5, 0.9, 0.95, 0.99]
choices = [1, 2, 5, 10]
mu = 1
max_t = 1000
n_servers=10
plot_interval=1

class MonitorSIR(Event):

    def __init__(self,lambd ,queue_snapshots,key,interval=1):
        self.interval = interval
        self.lambd = lambd
        self.queue_snapshots=queue_snapshots
        self.key=key

    def process(self, sim):
        # print(self.queue_snapshots)
        analyze_queue_lengths(sim,self.key,self.queue_snapshots)
        
        sim.schedule(self.interval, self)



# Analyze queue lengths
def analyze_queue_lengths(sim,key,queue_snapshots):
    queue_lengths = [len(q) for q in sim.queues]
    queue_snapshots[key].append(queue_lengths)

# Function to run the simulation and compute time-averaged fractions
def compute_time_averaged_fractions(snapshots, max_queue_length):
    fractions = []
    for x in range(max_queue_length + 1):
        fractions.append((snapshots >= x).mean(axis=1))  # Fraction of queues ≥ x for each snapshot
    fractions = np.array(fractions)
    return fractions.mean(axis=1)  # Time-averaged fractions for each queue length

max_queue_length = 15





if __name__ == '__main__':
    # queue_snapshots={}
    # for lambd in lambdas:
    #     queue_snapshots[lambd]=[]
    # Plot results
    plt.figure(figsize=(18, 14))
    for idx, d in enumerate(choices, 1):
        plt.subplot(2, 2, idx)
        queue_snapshots = {lambd: [] for lambd in lambdas}
        for lambd in lambdas:
            sim = Queues(lambd, mu, n_servers, d)
            sim.schedule(0, MonitorSIR(lambd,queue_snapshots,lambd,plot_interval))

            sim.run(max_t)
    
    
            snapshots=np.array(queue_snapshots[lambd])
            # Compute time-averaged fractions for each λ
            time_averaged_fractions = compute_time_averaged_fractions(snapshots, max_queue_length)
            plt.plot(
                    range(max_queue_length + 1),
                    time_averaged_fractions,
                    label=f"λ={lambd}"
                )
            plt.title(f"{d} choices")
            plt.xlabel("Queue Length (x)")
            plt.ylabel("Fraction of Queues with Size ≥ x")
            plt.legend(loc="upper right")
            plt.grid(True)

    plt.suptitle("Theoretical vs. Simulated Queue Lengths for Various n Choices", fontsize=16, y=0.98)  # Add a global title
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.subplots_adjust(hspace=0.4, wspace=0.3)
    plt.show()
