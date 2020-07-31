import itertools
import json
import math
import random

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

### Notes on networks library
# The implementation is currently fully based on networkx.
# A mixed implementation of networkx (small world graph generation) and
# python-igraph (rest of the operations) performed slightly worse in terms
# of runtime but much better in terms of memory usage.
# If memory usage is a concern, using python-igraph is recommended.

class Graph:
    """Graph and related data

    graph : networkx.classes.graph.Graph
        Graph modelling the population
    time_horizon : int
        Number of iterations of the simulation
    num_infected : int
        Number of initial infections
    graph_config : dict
        Dictionary with graph constructor configurations
    infection_rate : float
        Infection probability
    close_nodes_arr : numpy.ndarray
        Array indicating whether a node is close to another node
    """

    def __init__(self):
        # Graph and config
        self.graph = None
        self.time_horizon = None
        self.num_infected = None
        self.graph_config = None
        self.infection_rate = None

        # Simulation structures
        self.close_nodes_arr = None

    def set_simulation_config_from_file(self, filename):
        """Load simulation config from a JSON file

        Parameters
        ----------
        filename : str
            Path to the JSON file
        """

        with open(filename, "r") as f:
            simulation_config = json.loads(f.read())

        self.time_horizon = simulation_config["time_horizon"]
        self.num_infected = simulation_config["num_infected"]
        self.graph_config = simulation_config["graph_config"]

    def create_graph(self, age_structure, infection_rate):
        """Create a navigable small world graph

        Parameters
        ----------
        age_structure : dict
            Dictionary indicating number of people in given age group
        infection_rate : float
            Infection probability
        """

        self.infection_rate = infection_rate

        self._set_navigable_small_world_graph(
            age_structure=age_structure,
            short_connection_diameter=self.graph_config["params"]["short_connection_diameter"],
            long_connection_diameter=self.graph_config["params"]["long_connection_diameter"],
            decay=self.graph_config["params"]["decay"])

    def set_group_interaction_edges(self, behaviour, node, other_nodes,
                                    group_size):
        """Set edges in the graph based on specified group interaction

        Parameters
        ----------
        behaviour : str
            Name of the behaviour
        node : int
            Label of the node
        other_nodes : list
            List of other nodes
        group_size : int
            Number of nodes in a group
        """

        if behaviour == "food_shopping":
            # swap other nodes for only close nodes
            other_nodes = self.close_nodes_arr[node].nonzero()[0].tolist()

        # set group size
        size = group_size if group_size <= len(other_nodes) else len(other_nodes)

        # choose new group members randomly
        new_group = random.sample(other_nodes,
                                  k=size)

        # get new edges to add
        if behaviour == "food_shopping":
            new_edges = [(node, neighbour) for neighbour in new_group]
        else:
            # add the node considered
            new_group.append(node)
            # add edges so that the new group makes a connected subgraph
            new_edges = itertools.combinations(new_group, 2)

        # add new edges
        list(map(self._add_new_interaction_edge, new_edges))

    def remove_group_interaction_edges(self):
        """Remove interaction edges from the graph"""

        # remove new edges
        for (u, v) in self.graph.edges:
            if "interaction_edge" in self.graph[u][v]:
                self.graph.remove_edge(u, v)

    def draw_graph(self, filename):
        """Save a graph visualisation to a file

        The method is intended for development purposes only.
        If a graph has more than 100 nodes the method is not executed.

        Parameters
        ----------
        filename : str
            Path to where to save the resulting visualisation
        """

        if len(self.graph.nodes()) > 100:
            print("[draw_graph] more than 100 nodes in the graph. Skipping.")
            return

        layout = nx.spectral_layout(self.graph)
        weights = [1 + self.graph[u][v]["weight"]
                   if self.graph[u][v] else 1
                   for u, v in self.graph.edges()]

        nx.draw(self.graph, layout,
                with_labels=True,
                edges=self.graph.edges(),
                width=weights,
                node_size=200)

        plt.savefig(filename)

    def _add_new_interaction_edge(self, pair):
        """Add a new interaction edge if it is not already existing

        Parameters
        ----------
        pair : tuple
            Tuple in form (node, new neighbor node)
        """

        if not(self.graph.has_edge(*pair)):
            self.graph.add_edge(*pair, weight=self.infection_rate,
                                interaction_edge=True)

    def _set_navigable_small_world_graph(self, age_structure,
                                         short_connection_diameter,
                                         long_connection_diameter,
                                         decay):
        """Create non-directional Navigable Small World graph

        Parameters
        ----------
        age_structure : dict
            Dictionary indicating number of people in given age group
        short_connection_diameter : int
            Diameter of short connections
        long_connection_diameter : int
            Diameter of long connections
        decay : float
            Decay exponent
        """

        # get total number of people
        num_people = sum(age_structure.values())

        # since the graph constructor takes n as side of the grid
        # and returns n**2 nodes, take ceiling of square root
        # and remove the extra nodes later
        root_num_people = math.ceil(math.sqrt(num_people))

        # construct the graph
        digraph = nx.navigable_small_world_graph(root_num_people,
                                                 short_connection_diameter,
                                                 long_connection_diameter,
                                                 decay,
                                                 dim=2)

        # remove the extra unnecessary nodes
        num_extra = root_num_people**2 - num_people
        extra_nodes = random.sample(list(digraph.nodes),
                                    k=num_extra)
        digraph.remove_nodes_from(extra_nodes)

        # ignore directional edges, move grid location to attribute
        # and relabel with integer values
        graph = nx.convert_node_labels_to_integers(
            digraph.to_undirected(),
            label_attribute="location")

        # remove possible selfloops
        graph.remove_edges_from(nx.selfloop_edges(graph))

        # set the graph and add infection attribute
        self.graph = graph
        self._set_generic_weights()
        self._set_ages(age_structure)

        # precompute close nodes
        self._set_close_nodes_arr()

    def _set_close_nodes_arr(self):
        """Compute and store list of close nodes for each node in the graph

        Nodes are close if they are within Chebyshev distance specified by
        the threshold (treats diagonal connections the same as the adjacent)"""

        threshold = self.graph_config["closeness_threshold"]

        n_nodes = len(self.graph.nodes)
        node_arr = np.zeros((n_nodes, n_nodes))
        for node in self.graph:

            node_location = self.graph.nodes[node]["location"]

            # go over all nodes except node in question
            for other_node in self.graph.nodes:
                if node != other_node:

                    other_location = self.graph.nodes[other_node]["location"]

                    # calculate Chebyshev distance
                    # (includes diagonal neighbours)
                    chebyshev_dist = self._calculate_chebyshev_dist(other_location,
                                                                    node_location)

                    # save node if it is close
                    if chebyshev_dist <= threshold:
                        node_arr[node][other_node] = 1
        self.close_nodes_arr = node_arr

    def _calculate_chebyshev_dist(self, location_a, location_b):
        """Calculate Chebyshev distance

        Parameters
        ----------
        location_a : tuple
            Tuple in form (x, y)
        location_b : tuple
            Tuple in form (x, y)

        Returns
        -------
        int
            Chebyshev distance
        """

        return max(abs(location_a[0] - location_b[0]),
                   abs(location_a[1] - location_b[1]))

    def _set_generic_weights(self):
        """Add generic infection probability to each edge in the graph"""

        nx.set_edge_attributes(self.graph, self.infection_rate, "weight")

    def _set_ages(self, age_structure):
        """Set age of a node based on the age structure of the population

        Parameters
        ----------
        age_structure : dict
            Dictionary indicating number of people in given age group
        """

        age_group_list = []
        for age_group, n in age_structure.items():
            age_group_list += [age_group] * n

        random.shuffle(age_group_list)
        age_group_dict = {i: age_group_list[i] for i in range(len(age_group_list))}

        nx.set_node_attributes(self.graph, age_group_dict, "age_group")
