"""
Generate and save graphs for each community
"""

import argparse
import json
import os
from datetime import datetime

from src.simulation import Simulation

parser = argparse.ArgumentParser(description="Generate and save graphs for communities")

parser.add_argument("-i", "--input_spec_file", required=True, type=str,
                    metavar="file",
                    help="""JSON file specifying locations of data files required for the specification.
                            See input files specification in data/README.md for details.
                            'real' defaults to data/real/input-spec.json;
                            'sample' defaults to data/sample/sample-input-spec.json""")

parser.add_argument("-o", "--output_dir", required=False, type=str,
                    metavar="dir", default="data/output/intermediary",
                    help="""Directory where the results should be saved.
                            data/output/tmp by default.""")

parser.add_argument("-c", "--communities", default="", type=str,
                    metavar="csv names",
                    help="""Comma-separated list of communities for which to
                            generate graphs. If not supplied, generates graphs for all communities
                            listed in the community data file.""")

args = parser.parse_args()

start_time = datetime.now()

# define input files
if args.input_spec_file == "real":
    input_file_spec = "data/real/input-spec.json"
elif args.input_spec_file == "sample":
    input_file_spec = "data/sample/sample-input-spec.json"
else:
    input_file_spec = args.input_spec_file

with open(input_file_spec, "r") as f:
    input_files = json.loads(f.read())
    community_data_filename = input_files["community_data_filename"]
    infection_data_filename = input_files["infection_data_filename"]
    simulation_config_filename = input_files["simulation_config_filename"]

# create output directory if not existing
if not os.path.exists(args.output_dir):
    print("Making {} directory.".format(args.output_dir))
    os.makedirs(args.output_dir)

# set up the simulation
simulation = Simulation(infection_data_filename,
                        community_data_filename,
                        simulation_config_filename)

# get communities
if args.communities == "":
    communities = simulation.params.community_data
else:
    communities = args.communities.split(",")

# create and save graph for each community
for community in communities:
    print("Building {}...".format(community))
    simulation.params.set_community(community)
    simulation.create_graph()
    simulation.save_graph_to_file(os.path.join(args.output_dir, "{}-graph.pkl".format(community)))

print(datetime.now() - start_time)
