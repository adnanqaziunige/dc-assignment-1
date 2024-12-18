#!/usr/bin/env python3

import argparse
import csv
import collections
import logging
from random import expovariate, sample, seed

from discrete_event_sim import Simulation, Event
from workloads import weibull_generator


# One possible modification is to use a different distribution for job sizes or and/or interarrival times.
# Weibull distributions (https://en.wikipedia.org/wiki/Weibull_distribution) are a generalization of the
# exponential distribution, and can be used to see what happens when values are more uniform (shape > 1,
# approaching a "bell curve") or less (shape < 1, "heavy tailed" case when most of the work is concentrated
# on few jobs).

# To use Weibull variates, for a given set of parameter do something like
# from workloads import weibull_generator
# gen = weibull_generator(shape, mean)
#
# and then call gen() every time you need a random variable


# columns saved in the CSV file
CSV_COLUMNS = ['lambd', 'mu','shape',  'n', 'd','max_t']


class Queues(Simulation):
    """Simulation of a system with n servers and n queues.

    The system has n servers with one queue each. Jobs arrive at rate lambd and are served at rate mu.
    When a job arrives, according to the supermarket model, it chooses d queues at random and joins
    the shortest one.
    """

    def __init__(self, lambd, mu, n, d,shape=1):
        super().__init__()
        self.running = [None] * n  # if not None, the id of the running job (per queue)
        self.queues = [collections.deque() for _ in range(n)]  # FIFO queues of the system
        # NOTE: we don't keep the running jobs in self.queues
        self.arrivals = {}  # dictionary mapping job id to arrival time
        self.completions = {}  # dictionary mapping job id to completion time
        self.lambd = lambd
        self.n = n
        self.d = d
        self.mu = mu
        self.arrival_rate = lambd * n  # frequency of new jobs is proportional to the number of queues
        self.gen_lambbd = weibull_generator(shape, 1/self.arrival_rate)
        self.gen_mu = weibull_generator(shape, 1/self.mu)
        self.schedule(self.gen_lambbd(), Arrival(0))  # schedule the first arrival
      

    def schedule_arrival(self, job_id):
        """Schedule the arrival of a new job."""

        # schedule the arrival following an exponential distribution, to compensate the number of queues the arrival
        # time should depend also on "n"

        # memoryless behavior results in exponentially distributed times between arrivals (we use `expovariate`)
        # the rate of arrivals is proportional to the number of queues

        self.schedule( self.gen_lambbd(), Arrival(job_id))

    def schedule_completion(self, job_id, queue_index,service_time,left_time=None):  # TODO: complete this method
        """Schedule the completion of a job."""
        
        # schedule the time of the completion event
        # check `schedule_arrival` for inspiration
        
        service_time = left_time if left_time is not None else service_time
        self.schedule(service_time, Completion(job_id, queue_index))

    def queue_len(self, i):
        """Return the length of the i-th queue.
        
        Notice that the currently running job is counted even if it is not in self.queues[i]."""

        return (self.running[i] is not None) + len(self.queues[i])


class Arrival(Event):
    """Event representing the arrival of a new job."""

    def __init__(self, job_id):
        self.id = job_id

    def process(self, sim: Queues):  # TODO: complete this method
        sim.arrivals[self.id] = sim.t  # set the arrival time of the job
        sample_queues = sample(range(sim.n), sim.d)  # sample the id of d queues at random
        queue_index = min(sample_queues, key=sim.queue_len)  # shortest queue among the sampled ones
        # check the key argument of the min built-in function:
        # https://docs.python.org/3/library/functions.html#min

        # if you are looking for inspiration, check the `Completion` class below
        if sim.running[queue_index] is not None:  # queue is not empty
            current_job_id, service_time,left_time = sim.running[queue_index]
            elapsed_time = sim.t - sim.arrivals[current_job_id]  # Time spent so far
            left_time = service_time - elapsed_time 
            if(left_time<=0):
                left_time=0
            
            sim.queues[queue_index].appendleft((current_job_id, service_time,left_time))  # Push preempted job to front           
        
        new_service_time=sim.gen_mu()
        # sim.queues[queue_index].appendleft((self.id, None))  # New job with no preemption
        sim.running[queue_index] = (self.id, new_service_time,None)
        sim.schedule_completion(self.id, queue_index,new_service_time)
        sim.schedule_arrival(self.id+1)  # schedule its completion


class Completion(Event):
    """Job completion."""

    def __init__(self, job_id, queue_index):
        self.job_id = job_id  # currently unused, might be useful when extending
        self.queue_index = queue_index

    def process(self, sim: Queues):
        queue_index = self.queue_index
        # assert sim.running[queue_index][0] == self.job_id  # the job must be the one running , we should relax this condition since a job might have prempted after this event scheduled
        if sim.running[queue_index] is not None and sim.running[queue_index][0] == self.job_id:
            sim.completions[self.job_id] = sim.t
            queue = sim.queues[queue_index]
            if queue:  # queue is not empty
                next_job_id, service_time,left_time = sim.queues[queue_index].popleft()
                sim.running[queue_index] = (next_job_id, service_time,left_time) # assign the last interrupted job in the queue
                sim.schedule_completion(next_job_id, queue_index, service_time,left_time)# schedule its completion
            
            else:
                sim.running[queue_index] = None  # no job is running on the queue


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--lambd', type=float, default=0.7, help="arrival rate")
    parser.add_argument('--mu', type=float, default=1, help="service rate")
    parser.add_argument('--max-t', type=float, default=1_000_00, help="maximum time to run the simulation")
    parser.add_argument('--n', type=int, default=10, help="number of servers")
    parser.add_argument('--d', type=int, default=1, help="number of queues to sample")
    parser.add_argument('--shape', type=float, default=1, help="Weibull shape parameter")
    parser.add_argument('--csv', help="CSV file in which to store results")
    parser.add_argument("--seed", help="random seed")
    parser.add_argument("--verbose", action='store_true')
    args = parser.parse_args()

    params = [getattr(args, column) for column in CSV_COLUMNS[:]]
    # corresponds to params = [args.lambd, args.mu, args.max_t, args.n, args.d]

    if any(x <= 0 for x in params):
        logging.error("lambd, mu, max-t, n and d must all be positive")
        exit(1)

    if args.seed:
        seed(args.seed)  # set a seed to make experiments repeatable
    if args.verbose:
        # output info on stderr
        logging.basicConfig(format='{levelname}:{message}', level=logging.INFO, style='{')

    if args.lambd >= args.mu:
        logging.warning("The system is unstable: lambda >= mu")

    sim = Queues(args.lambd, args.mu, args.n, args.d, args.shape)
    sim.run(args.max_t)

    completions = sim.completions
    W = ((sum(completions.values()) - sum(sim.arrivals[job_id] for job_id in completions))
         / len(completions))
    print(f"Average time spent in the system: {W}")
    if args.mu == 1 and args.lambd != 1:
        print(f"Theoretical expectation for random server choice (d=1): {1 / (1 - args.lambd)}")

    if args.csv is not None:
        with open(args.csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(params + [W])


if __name__ == '__main__':
    main()
