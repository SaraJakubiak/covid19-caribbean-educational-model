import json
import pickle

import numpy as np

from src.graph import Graph
from src.model import Model
from src.params import Params


class Simulation:
    """Wrapper class for managing parameters and graph and running simulations

    params : src.Params
        Parameters holding object
    graph : src.Graph
        Graph holding object
    model: src.Model
        Model of the network
    new_graph_per_run : bool, optional
        If true, builds new graph for each single simulation run,
        by default False
    load_graph_filename : str, optional
        If not empty, loads graph each run, by default ""
    verbose : bool, optional
        Print results of each simulation to console, by default False
    """

    def __init__(self,
                 infection_data_filename,
                 community_data_filename,
                 simulation_config_filename,
                 new_graph_per_run=False,
                 load_graph_filename="",
                 verbose=False):

        # set up simulation parameters
        params = Params()
        params.set_infection_data_from_file(infection_data_filename)
        params.set_community_data_from_file(community_data_filename)

        # set up the base graph configuration
        graph = Graph()
        graph.set_simulation_config_from_file(simulation_config_filename)

        self.params = params
        self.graph = graph
        self.model = None

        # build new graph for each run by default
        self.new_graph_per_run = new_graph_per_run
        self.load_graph_filename = load_graph_filename
        self.verbose = verbose

    def set_app_input_from_file(self, filename):
        """Load the input data from the app from a JSON file

        Parameters
        ----------
        filename : str
            Path to the JSON file
        """

        with open(filename, "r") as f:
            app_input_data = json.loads(f.read())

        self.params.set_app_input(
            community=app_input_data["community"],
            behaviours=app_input_data["behaviours"],
        )

    def create_graph(self):
        """Create graph based on the supplied parameters

        Raises
        ------
        Exception
            Throws exception when population size or infection rate
            is missing
        """

        msg = []
        if self.params.population_size is None:
            msg.append("the community has not been set")
        if self.params.generic_infection is None:
            msg.append("the infection data has not been set")

        if msg != []:
            raise Exception("Cannot create the graph: {}".format(", ".join(msg)))

        self.graph.create_graph(
            age_structure=self.params.age_structure,
            infection_rate=self.params.generic_infection)

    def save_graph_to_file(self, filename):
        """Save current graph object to a file

        Parameters
        ----------
        filename : str
            Filename of the file to be saved
        """

        with open(filename, "wb") as f:
            pickle.dump(self.graph, f, pickle.HIGHEST_PROTOCOL)

    def load_graph_from_file(self, filename):
        """Load graph from a file and validate against current graph configuration

        Parameters
        ----------
        filename : str
            Filename of the saved graph object

        Raises
        ------
        Exception
            Throws exception when the loaded graph configuration differs from
            the current graph configuration
        """

        with open(filename, "rb") as f:
            loaded_graph = pickle.load(f)

        # ensure that loaded graph confirm to the graph configuration
        valid_config = loaded_graph.graph_config == self.graph.graph_config
        valid_time = loaded_graph.time_horizon == self.graph.time_horizon
        valid_infected = loaded_graph.num_infected == self.graph.num_infected
        valid_population = len(loaded_graph.graph.nodes) == self.params.population_size
        valid_infection_rate = loaded_graph.infection_rate == self.params.generic_infection

        if not(valid_config and valid_time and valid_infected and valid_population and valid_infection_rate):
            raise Exception("The graph to be loaded does not adhere to the graph configuration")

        self.graph = loaded_graph

    def run_single(self):
        """Run a single simulation

        Returns
        -------
        dict
            Results of the simulation
        """

        if self.new_graph_per_run:
            if self.load_graph_filename:
                self.load_graph_from_file(self.load_graph_filename)
            else:
                self.create_graph()

        model = Model(self.params, self.graph, self.verbose)

        model.basic_simulation()

        return model.get_results()

    def run_multiple(self, n):
        """Run multiple simulations and return an averaged result

        Parameters
        ----------
        n : int
            Number of multiple simulation runs

        Returns
        -------
        dict
            Dictionary with averaged results of multiple runs
            of a simulation
        """

        # run simulations and collect results
        all_results = [self.run_single() for _ in range(n)]

        # get averaged results
        averaged = {}
        for state in Model.STATES:
            state_lists = [state_dict[state] for state_dict in all_results]
            averaged[state] = [int(np.round(np.mean(item))) for item in zip(*state_lists)]

        # ensure number of people in each state is equal to
        # the population size at each timestep, otherwise
        # add/remove extra from biggest state
        for timestep in range(self.graph.time_horizon // 7):
            total = sum([averaged[state][timestep] for state in Model.STATES])
            if total != self.params.population_size:
                states_at_timestep = {state: averaged[state][timestep] for state in Model.STATES}
                biggest_state = max(states_at_timestep, key=states_at_timestep.get)
                averaged[biggest_state][timestep] += self.params.population_size - total

        return averaged
