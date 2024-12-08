#!/usr/bin/env python3

import argparse
import configparser
import logging
import random
from dataclasses import dataclass
from discrete_event_sim import Simulation, Event
from typing import Optional, List
from humanfriendly import format_timespan, parse_size, parse_timespan

from edit_storage import NodeEvent,Node,Backup,exp_rv,Online

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


class LeaveNetwork(NodeEvent):
    """A node leaves the network permanently."""
    def process(self, sim: Backup):
        node = self.node
        if node in sim.nodes:
            
            node.left=True#???
            print(f"{format_timespan(sim.t)}: {node} left the network permanently")
            # Cancel ongoing transfers for the node
            current_upload = node.current_upload
            current_download = node.current_download
            if current_upload:
                current_upload.canceled = True
                current_upload.downloader.current_download = None
            if current_download:
                current_download.canceled = True
                current_download.uploader.current_upload = None
        else:
            print(f"{format_timespan(sim.t)}: {node} was not in the network")


# Extend the main simulation logic to schedule join and leave events
def schedule_dynamic_behaviors(sim: Backup, nodes: List[Node], join_rate: float, leave_rate: float):
    """Schedule join and leave events for nodes."""
    for node in nodes:
        join_time = exp_rv(join_rate)
        leave_time = exp_rv(leave_rate)
        print(f"{format_timespan(join_time)}: {node.name} joined")
        # Ensure nodes start by joining the network
        sim.schedule(join_time, JoinNetwork(node))

        # Schedule leave events only for nodes that have joined
        sim.schedule(join_time + leave_time, LeaveNetwork(node))



# Example of extending main() to include dynamic behaviors
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="configuration file")
    parser.add_argument("--max-t", default="100 years")
    parser.add_argument("--seed", help="random seed")
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--join_rate", type=float, default=31536000, help="Average rate of nodes joining the network") # approx 1 join in one year 
    parser.add_argument("--leave_rate", type=float, default=31536000*10, help="Average rate of nodes leaving the network")
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
    t=2 #some dynamic
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

    # Initialize simulation and schedule dynamic behaviors
    sim = Backup(nodes)
    schedule_dynamic_behaviors(sim, lnodes, args.join_rate, args.leave_rate)
    sim.run(parse_timespan(args.max_t))
    sim.log_info("Simulation over")


if __name__ == '__main__':
    main()
