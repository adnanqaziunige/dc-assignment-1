#!/usr/bin/env python3

import argparse
import configparser
import logging
import random
from dataclasses import dataclass
from discrete_event_sim import Simulation, Event
from typing import Optional, List
from humanfriendly import format_timespan, parse_size, parse_timespan

from edit_storage import NodeEvent,Node,Backup,exp_rv,Online,Fail

logging.basicConfig(filename="storage.log",format='{levelname}:{message}', level=logging.INFO, style='{')  # output info on stdout


# Define new events for nodes joining and leaving the network
class JoinNetwork(NodeEvent):
    """A new node joins the network."""
    def process(self, sim: Backup):
        node = self.node
        if node not in sim.nodes:
            sim.nodes.append(node)
            print(f"{format_timespan(sim.t)}: {node} joined the network")
            sim.schedule(exp_rv(node.average_uptime), Online(node))
            sim.schedule(exp_rv(node.average_lifetime), Fail(node))






# Extend the main simulation logic to schedule join and leave events
def schedule_dynamic_behaviors(sim: Backup, nodes: List[Node], join_time: float,):
    """Schedule join events for nodes."""
    for node in nodes:
        print(f"{format_timespan(join_time)}: {node.name} joined")
        # Ensure nodes start by joining the network
        sim.schedule(join_time, JoinNetwork(node))




# Example of extending main() to include dynamic behaviors
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="configuration file")
    parser.add_argument("--max-t", default="100 years")
    parser.add_argument("--seed", help="random seed")
    parser.add_argument("--verbose", action='store_true')
    # parser.add_argument("--join_time", type=float, default=3* 31536000, help="How much Time after nodes join the network") # after one year other nodes join
    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)  # Set a seed to make experiments repeatable
    if args.verbose:
        logging.basicConfig(format='{levelname}:{message}', level=logging.INFO, style='{')

    # Parse node configurations
    config = configparser.ConfigParser()
    config.read(args.config)
    nodes = []
    parsing_functions = [
        ('n', int), ('k', int),
        ('data_size', parse_size), ('storage_size', parse_size),
        ('upload_speed', parse_size), ('download_speed', parse_size),
        ('average_uptime', parse_timespan), ('average_downtime', parse_timespan),
        ('average_lifetime', parse_timespan), ('average_recover_time', parse_timespan),
        ('arrival_time', parse_timespan)
    ]
    t=18 #some dynamic
    c=0
    lnodes=[]
   
    for node_class in config.sections():
        class_config = config[node_class]
        cfg = [parse(class_config[name]) for name, parse in parsing_functions]
        c+=1
        initial=class_config.getint('number')
        nodes.extend(Node(f"{node_class}-{i}", *cfg) for i in range(t))
        if initial>t:
     
        
            lnodes.extend(Node(f"{node_class}-{i}", *cfg) for i in range(t,initial+1))
    avg_times_first=[]
    avg_times_second=[]
    # Initialize simulation and schedule dynamic behaviors
    max_t=parse_timespan(args.max_t)
    sim = Backup(nodes,avg_times_first,avg_times_second,max_t)
    schedule_dynamic_behaviors(sim, lnodes, max_t/2)
    sim.run(max_t)
    sim.log_info("Simulation over")
    print(format_timespan(sum(sim.avg_times_first)/len(sim.avg_times_first)))
    print(format_timespan(sum(sim.avg_times_second)/len(sim.avg_times_second)))


if __name__ == '__main__':
    main()

"""
what if we increase the no. of nodes later? it affects throughput due to more coordination in a bad network 

see the 't' parameter above
Latency in Recovery:

    Effect: Additional nodes may introduce some delay in data retrieval, especially if nodes are geographically distant or if the network is not optimized for quick data recovery.
    Why: While having more nodes may increase redundancy, the process of retrieving data from nodes that are farther away or less optimized can lead to slower recovery times in certain scenarios.
"""