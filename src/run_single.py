"""
Runs the simulation once based on the files provided
"""

import argparse
import json
import os
from datetime import datetime

from src.simulation import Simulation

parser = argparse.ArgumentParser(
    description="Runs the simulation once based on the files provided")

parser.add_argument("-i", "--input_spec_file", required=True, type=str,
                    metavar="file",
                    help="""JSON file specifying locations of data files required for the specification.
                            See input files specification in data/README.md for details.
                            'real' defaults to data/real/input-spec.json;
                            'sample' defaults to data/sample/sample-input-spec.json""")

parser.add_argument("-o", "--output_filename", required=False, type=str,
                    metavar="file", default="data/output/sample-output.json",
                    help="""Filename where the results should be saved.
                            data/output/sample-output.json by default.""")

parser.add_argument("-n", "--number_of_runs", type=int,
                    metavar="int", default=10,
                    help="""Number of runs of the simulation. If bigger than 1,
                            the simulation results are averaged across the runs.
                            10 by deafult.""")

parser.add_argument("-lg", "--load_graph_dir", type=str,
                    metavar="str", default="",
                    help="""When supplied, attempts to load graph from a file
                            {community_name}-graph.pkl in specified
                            directory.""")

parser.add_argument("-ng", "--new_graph", action="store_true",
                    help="""Construct a graph on per simulation basis instead of once
                            per run.""")

parser.add_argument("-q", "--quiet", action="store_true",
                    help="Do not print results to console.")

parser.add_argument("-gp", "--graph_plot_filename", type=str,
                    metavar="file",
                    help="When supplied, saves PNG graph visualisation to given filename.")

parser.add_argument("-dtp", "--doubling_time_plot_filename", type=str,
                    metavar="file",
                    help="When supplied, saves PNG doubling time plot to given filename.")

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
    app_input_filename = input_files["app_input_filename"]
    community_data_filename = input_files["community_data_filename"]
    infection_data_filename = input_files["infection_data_filename"]
    simulation_config_filename = input_files["simulation_config_filename"]

simulation = Simulation(infection_data_filename,
                        community_data_filename,
                        simulation_config_filename,
                        new_graph_per_run=args.new_graph,
                        verbose=not(args.quiet))
simulation.set_app_input_from_file(app_input_filename)

if args.load_graph_dir:
    graph_filename = os.path.join(args.load_graph_dir, "{}-graph.pkl".format(simulation.params.community))
    simulation.load_graph_from_file(graph_filename)
    simulation.load_graph_filename = graph_filename
else:
    simulation.create_graph()

# run the simulation
results = simulation.run_multiple(args.number_of_runs)

if args.output_filename:
    json_str = json.dumps(results)

    with open(args.output_filename, "w") as f:
        f.write(json_str)

if args.graph_plot_filename:
    simulation.graph.draw_graph(args.graph_plot_filename)

if args.doubling_time_plot_filename:
    simulation.model.plot_doubling_time(args.doubling_time_plot_filename)

if not args.quiet:
    print()
    print(datetime.now() - start_time)
