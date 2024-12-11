#!/usr/bin/env python3

import argparse
import configparser
import logging
import random
from dataclasses import dataclass
from discrete_event_sim import Simulation, Event
from typing import Optional, List
from humanfriendly import format_timespan, parse_size, parse_timespan

from edit_storage import NodeEvent, Node, Backup, exp_rv, Online, Fail

logging.basicConfig(filename="storage.log", format='{levelname}:{message}', level=logging.INFO, style='{')

@dataclass
class Region:
    name: str
    nodes: List[Node]
    join_interval: float
    leave_interval: float

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

class LeaveNetwork(NodeEvent):
    """A node leaves the network."""
    def process(self, sim: Backup):
        node = self.node
        if node in sim.nodes:
            sim.nodes.remove(node)
            print(f"{format_timespan(sim.t)}: {node} left the network")
            sim.schedule(node.join_time, JoinNetwork(node))

# Extend the main simulation logic to schedule join and leave events
def schedule_dynamic_behaviors(sim: Backup, regions: List[Region]):
    """Schedule join and leave events for nodes in different regions."""
    for region in regions:
        for node in region.nodes:
            join_time = exp_rv(region.join_interval)
            leave_time = exp_rv(region.leave_interval)
            sim.schedule(join_time, JoinNetwork(node))
            sim.schedule(leave_time, LeaveNetwork(node))

# Example of extending main() to include dynamic behaviors
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="configuration file")
    parser.add_argument("--max-t", default="100 years")
    parser.add_argument("--seed", help="random seed")
    parser.add_argument("--verbose", action='store_true')
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
        ('arrival_time', parse_timespan), ('join_interval', parse_timespan),
        ('leave_interval', parse_timespan)
    ]
    # t = 18  # some dynamic
    c = 0
    regions = []

    for node_class in config.sections():
        class_config = config[node_class]
        cfg = [parse(class_config[name]) for name, parse in parsing_functions]
        c += 1
        n = class_config.getint('number')
        region_name = class_config.get('region', f"Region-{c}")
        join_interval = parse_timespan(class_config.get('join_interval', '1 year'))
        leave_interval = parse_timespan(class_config.get('leave_interval', '2 years'))
        region_nodes = [Node(f"{node_class}-{i}", *cfg) for i in range(n)]
        regions.append(Region(region_name, region_nodes, join_interval, leave_interval))

    # Initialize simulation and schedule dynamic behaviors
    max_t = parse_timespan(args.max_t)
    sim = Backup(nodes, max_t)
    schedule_dynamic_behaviors(sim, regions)
    sim.run(max_t)
    sim.log_info("Simulation over")

if __name__ == '__main__':
    main()