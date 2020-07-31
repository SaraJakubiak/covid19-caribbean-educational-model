"""
Runs the simulation for each combination of app inputs provided
"""

import argparse
import json
import multiprocessing
import os
import random
import re
import shutil
from collections import defaultdict
from contextlib import closing
from datetime import datetime
from functools import partial
from itertools import product

import tqdm

from src.model import Model
from src.simulation import Simulation

start_time = datetime.now()

parser = argparse.ArgumentParser(
    description="""Runs the simulation for each combination of app inputs
                   provided""")

parser.add_argument("-i", "--input_spec_file", required=True, type=str,
                    metavar="file",
                    help="""JSON file specifying locations of data files required for the specification.
                            See input files specification in data/README.md
                            for details. 'real' defaults to
                            data/real/input-spec.json; 'sample' defaults to
                            data/sample/sample-input-spec.json""")

parser.add_argument("-o", "--output_dir", required=False, type=str,
                    metavar="dir", default="data/output/",
                    help="""Directory where the results should be saved.
                            data/output/ by default.""")

parser.add_argument("-n", "--number_of_runs", type=int,
                    metavar="int", default=10,
                    help="""Number of runs per single simulation.
                            If bigger than 1, the simulation results
                            are averaged across the runs.
                            10 by default.""")

parser.add_argument("-tasks", "--max_tasks_per_child", type=int,
                    metavar="int", default=1,
                    help="""Number of maximum tasks per child subprocess.
                            1 by default.""")

parser.add_argument("-chunk", "--chunksize", type=int,
                    metavar="int", default=1,
                    help="""Chunksize of multiprocessing pool mapping.
                            1 by default.""")

parser.add_argument("-cpu", "--cpu", type=int,
                    metavar="int", default=os.cpu_count(),
                    help="""Number of worker processes to use.
                            Number of CPU cores by default.""")

parser.add_argument("-uinter", "--use_intermediary", action="store_true",
                    help="""Compute only variants not already present
                            in intermediary/ directory.""")

parser.add_argument("-dinter", "--delete_intermediary", action="store_true",
                    help="""Delete the intermediary/ directory after the simulations finish.
                            intermediary/ directory stores graphs and results of every
                            variant in separate files which are joint together
                            after all simulations finish.""")

parser.add_argument("-gensample", "--generate_sample", action="store_true",
                    help="""Do not run the simulation and return dummy results
                            instead.""")

parser.add_argument("-lg", "--load_graph_dir", type=str,
                    metavar="str", default="",
                    help="""When supplied, attempts to load graph from a file
                            {community_name}-graph.pkl in specified
                            directory.""")

parser.add_argument("-ng", "--new_graph", action="store_true",
                    help="""Construct a graph on per simulation basis instead of once
                            per community.""")

parser.add_argument("-sp", "--single_processing", action="store_true",
                    help="""Do not use multiprocessing.""")


def main():

    args = parser.parse_args()

    # define input file spec
    if args.input_spec_file == "real":
        input_file_spec = "data/real/input-spec.json"
    elif args.input_spec_file == "sample":
        input_file_spec = "data/sample/sample-input-spec.json"
    else:
        input_file_spec = args.input_spec_file

    # retrieve input filepaths
    with open(input_file_spec, "r") as f:
        input_files = json.loads(f.read())
        app_input_values_filename = input_files["app_input_values_filename"]

    # get parameter values
    with open(app_input_values_filename, "r") as f:
        input_values = json.loads(f.read())

    # iterate through possible values
    iterate_communities(input_values, input_files, args)

    # report the runtime
    print()
    print(datetime.now() - start_time)


def iterate_communities(input_values, input_files, args):
    """Iterate through each community and save the results of the simulations
    to a file

    Parameters
    ----------
    input_values : dict
        Dictionary with parameter values
    input_files : dict
        Dictionary with filenames of input files
    args : argparse.Namespace
        Parsed program arguments
    """

    # create intermediary/ directory if not existing
    if not os.path.exists(os.path.join(args.output_dir, "intermediary")):
        os.makedirs(os.path.join(args.output_dir, "intermediary"))

    # go over each community
    for community in input_values["community"]:

        # set up the simulation
        simulation = Simulation(input_files["infection_data_filename"],
                                input_files["community_data_filename"],
                                input_files["simulation_config_filename"],
                                new_graph_per_run=args.new_graph)
        simulation.params.set_community(community)

        if not args.load_graph_dir and not args.new_graph:
            # create and save graph to file
            simulation.create_graph()
            simulation.save_graph_to_file(
                os.path.join(
                    args.output_dir, "intermediary", "{}-graph.pkl".format(community)))
            simulation.graph.graph = None

        # generate behaviour variants combinations
        variants = generate_variants(input_values)

        # modify the variants if needed
        if args.use_intermediary:
            # get all already computed variants
            valid_name = r"{}-.*.json".format(community)
            existing_variants = set()
            for filename in os.listdir(os.path.join(args.output_dir, "intermediary")):
                if re.match(valid_name, filename):
                    behaviours_tuple = tuple(re.findall("[a-z]+_[a-z]+_\d+_\d+", filename))
                    existing_variants.add(behaviours_tuple)

            # remove existing variants to only compute missing
            variants = variants - existing_variants

        if args.single_processing:
            # run simulations sequentially
            for variant in tqdm.tqdm(variants):
                run_simulation(variant, simulation, args)

        else:
            # run simulations as separate subprocesses
            with closing(multiprocessing.Pool(args.cpu, maxtasksperchild=args.max_tasks_per_child)) as p:
                for _ in tqdm.tqdm(
                            p.imap_unordered(
                                partial(run_simulation,
                                        simulation=simulation,
                                        args=args),
                                # cast to list to avoid pickling a memory heavy set
                                list(variants),
                                chunksize=args.chunksize),
                            total=len(variants)):
                    continue
                p.terminate()

        # load all results from files in intermediary/
        # and concatenate into one results file
        if args.use_intermediary:
            # get all variants to retrieve all files
            variants = generate_variants(input_values)

        # create nested dictionary to store all results
        recursivedict = lambda: defaultdict(recursivedict)
        results_dict = recursivedict()

        # retrieve all variants
        for variant in variants:

            filename = os.path.join(args.output_dir, "intermediary",
                                    "{}-{}.json".format(community, ("_".join(variant))))

            with open(filename, "r") as f:
                results_dict[variant[0]][variant[1]][variant[2]] = json.loads(f.read())

        # add metadata
        all_results = make_results_dict(simulation)
        all_results["results"] = results_dict

        # save to JSON
        filename = os.path.join(
            args.output_dir, "{}-results.json".format(community))
        with open(filename, "w") as f:
            f.write(json.dumps(all_results))

    if args.delete_intermediary:
        shutil.rmtree(os.path.join(args.output_dir, "intermediary"))


def run_simulation(variant, simulation, args):
    """Run simulation for given variant

    Parameters
    ----------
    variant : tuple
        Tuple of behaviours
    simulation : src.Simulation
        Partially preconfigured simulation object
    args : argparse.Namespace
        Parsed program arguments
    """

    # graph is loaded per simulation to avoid memory issues when
    # pickling big graphs through the multiprocessing pool
    if args.new_graph:
        if args.load_graph_dir:
            # set graph filename to load each run
            graph_filename = os.path.join(args.load_graph_dir, "{}-graph.pkl".format(simulation.params.community))
            simulation.load_graph_filename = graph_filename
    else:
        if args.load_graph_dir:
            # load from specified directory once for all runs
            graph_filename = os.path.join(args.load_graph_dir, "{}-graph.pkl".format(simulation.params.community))
            simulation.load_graph_from_file(graph_filename)
        else:
            # loaded from directory file was just saved to once for all runs
            graph_filename = os.path.join(args.output_dir, "intermediary", "{}-graph.pkl".format(simulation.params.community))
            simulation.load_graph_from_file(graph_filename)

    simulation.params.behaviours = variant

    if args.generate_sample:
        results = get_dummy_results(simulation)
    else:
        results = simulation.run_multiple(args.number_of_runs)

    # save to intermediary/
    filename = os.path.join(
        args.output_dir, "intermediary", "{}-{}.json".format(simulation.params.community, ("_".join(variant))))
    with open(filename, "w") as f:
        f.write(json.dumps(results))


def generate_variants(input_values):
    """Return all possible values of behaviours

    Parameters
    ----------
    input_values : dict
        Dictionary with parameter values

    Returns
    -------
    set
        Set of lists of behaviour variants
    """

    behaviours = input_values["behaviour"]
    variants_per_behaviour = map(partial(get_behaviour_variants,
                                         input_values=input_values),
                                 behaviours)
    variants = list(product(*variants_per_behaviour))

    return set(variants)


def get_behaviour_variants(behaviour, input_values):
    """Return all possible values (variants) of given behaviour
    and its possible attributes (number of visits, number of people)

    Parameters
    ----------
    behaviour : str
        Name of the behaviour
    input_values : dict
        Dictionary with parameter values

    Returns
    -------
    list
        List of possible variants in form (behaviour, number of visits,
        number of people)
    """

    visits_vals = [str(value) for value in input_values["num_visits"][behaviour]]
    num_people_vals = [str(value) for value in input_values["num_people"][behaviour]]

    vals = [[behaviour], visits_vals, num_people_vals]
    variants_tuples = list(product(*vals))
    variants = ["_".join(var_tuple) for var_tuple in variants_tuples]
    variants.append(("{}_0_0".format(behaviour)))

    return variants


def make_results_dict(simulation):
    """Create results dictionary with metadata

    Parameters
    ----------
    simulation : src.Simulation
        Partially preconfigured simulation object

    Returns
    -------
    dict
        Results dictionary with metadata
    """

    return {
            "results": None,
            "timestamp": str(datetime.now()),
            "community_data": {
                "name": simulation.params.community,
                "population": simulation.params.population_size,
                "age_structure": simulation.params.age_structure},
            "sim_config": {
                "time_horizon": simulation.graph.time_horizon,
                "num_infected": simulation.graph.num_infected,
                "graph_config": simulation.graph.graph_config},
            "infection_data": {"generic_infection": simulation.params.generic_infection,
                               "state_transitions": simulation.params.state_transitions}}


def get_dummy_results(simulation):
    """Return dummy results where population is randomly
    split between R and S states

    Parameters
    ----------
    simulation : src.Simulation
        Partially preconfigured simulation object

    Returns
    -------
    dict
        Dummy simulation results
    """

    n = simulation.graph.time_horizon // 7
    state_dict = {state: [0] * n for state in Model.STATES}

    for timestep in range(n):
        state_dict["S"][timestep] = random.randint(0, simulation.params.population_size)
        state_dict["R"][timestep] = simulation.params.population_size - state_dict["S"][timestep]

    return state_dict


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    main()
