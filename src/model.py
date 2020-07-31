import random
from collections import Counter
from functools import partial
import matplotlib.pyplot as plt


class Model:
    """Base model for simulating COVID-19 spread in Jamaica

    Parameters
    ----------
    params : src.Params
        Parameters holding object
    graph : src.Graph
        Graph holding object
    console_log : bool, optional
        Log execution output, by default False
    STATES : dict
        Dictionary with state names
    """

    STATES = {"S": "Susceptible",
              "E": "Exposed",
              "A": "Asymptomatic",
              "I": "Symptomatic",
              "H": "Hospitalised",
              "D": "Dead",
              "R": "Recovered"}

    def __init__(self, params, graph, console_log=False):
        self.params = params
        self.graph = graph
        self.console_log = console_log

    def basic_simulation(self):
        """Run the simulation"""

        self.params.behaviours_dict = self.params._convert_behaviours_to_dict()

        # choose a random set of initially infected
        infected = random.sample(list(self.graph.graph),
                                 k=self.graph.num_infected)

        self._make_states_dict()
        step_zero_states_dict = self.states_dict[0]
        for vertex in infected:
            step_zero_states_dict[vertex] = "I"

        for time in range(self.graph.time_horizon):
            self.curr_time = time

            nodes = self.graph.graph.nodes

            # use map for better performance
            # use list to force map evaluation
            list(map(self._add_interactions, nodes))
            list(map(self._do_progression, nodes))
            list(map(self._do_infection, nodes))

            self._remove_interactions()

        if self.console_log:
            self.print_state_counts(self.graph.time_horizon)

    def get_results(self):
        """Returns dictionary with results of the simulation

        The results are reported every 7 steps.

        Returns
        -------
        dict
            Dictionary in form {state: [number of nodes in given state]}
        """

        output_dict = {key: [] for key in Model.STATES.keys()}

        for step in range(1, self.graph.time_horizon + 1, 7):
            counts = self._get_state_counts(step)
            for state in output_dict:
                output_dict[state].append(counts[state])

        return output_dict

    def print_state_counts(self, time, letter_only=False):
        """Print the summary of number of nodes in given state at given time

        Parameters
        ----------
        time : int
            Timestep
        letter_only : bool, optional
            Print the state string letter instead of the full name,
            by default False
        """

        counts = self._get_state_counts(time)

        print("Time:", time)
        for letter, name in Model.STATES.items():
            if letter_only:
                print("{:<5}{:>5}".format(letter, counts[letter]))
            else:
                print("{:<15}{:>10}".format(name, counts[letter]))
        print("-"*30)

    def plot_doubling_time(self, filename):
        """Create plot of cumulative cases and doubling time
        and save it to a file.

        Parameters
        ----------
        filename : str
            Name of the file where the figure is to be saved
        """

        # generate list of cumulative cases
        # where cases is everyone not is state "S"
        infectious_counts = []
        for timestep in range(self.graph.time_horizon):
            counts = self._get_state_counts(timestep)
            timestep_count = self.params.population_size - counts["S"]
            infectious_counts.append(timestep_count)

        # generate the list of doubling times
        # ie how many timesteps is takes for
        # number of cases to double
        double_times = []
        for ix in range(len(infectious_counts)):
            for ix_future in range(ix + 1, len(infectious_counts)):
                if infectious_counts[ix_future] >= infectious_counts[ix] * 2:
                    double_times.append(ix_future - ix)
                    break

        # since double_times will be shorter, append extra
        # None for plotting
        diff = len(infectious_counts) - len(double_times)
        if diff != 0:
            double_times += [None] * diff

        # construct the figure
        # based on https://matplotlib.org/gallery/api/two_scales.html
        fig, ax1 = plt.subplots()

        color = "tab:red"
        ax1.set_xlabel("timestep")
        ax1.set_ylabel("cumulative cases", color=color)
        ax1.plot(range(len(infectious_counts)), infectious_counts, color=color)
        ax1.tick_params(axis="y", labelcolor=color)
        ax1.set_xticks(range(0, len(infectious_counts), 5))

        ax2 = ax1.twinx()
        color = "tab:blue"
        ax2.set_ylabel("timesteps to double", color=color)
        ax2.plot(range(len(infectious_counts)), double_times, color=color)
        ax2.tick_params(axis="y", labelcolor=color)
        ax2.set_yticks(range(11))

        ax1.grid(True, axis="x")
        fig.tight_layout()
        plt.savefig(filename)

    def _make_states_dict(self):
        """Create states dictionary for timestep 0 where
        each node from graph has state 'S'
        """

        states_dict = {timestep: {} for timestep in range(self.graph.time_horizon + 1)}
        for guy in self.graph.graph:
            states_dict[0][guy] = "S"

        self.states_dict = states_dict

    def _choose_from_distrib(self, age_group, distrib):
        """Randomly choose a state based on given distribution

        Parameters
        ----------
        age_group : str
            Name of the age group
        distrib : dict
            Dictionary in form {state: {age_group: prob}}

        Returns
        -------
        str
            Randomly chosen item
        """

        curr_sum = 0
        max_sum = random.random()
        for value in distrib:
            curr_sum += distrib[value][age_group]
            if max_sum <= curr_sum:
                return value

        print(("Something has gone wrong - no next state was returned. "
               "Choosing arbitrarily."))
        print(distrib)
        return min(distrib.keys())

    def _add_interactions(self, node):
        """Add interactions to the graph based on the number of visits
        of set behaviours

        Parameters
        ----------
        node : int
            Name of node in the graph
        """

        # get the current "weekday"
        weekday = self.curr_time % 7

        # get all other nodes
        other_nodes = [other_node for other_node in self.graph.graph if other_node != node]

        # set up the week
        if weekday == 0:
            for behaviour, behaviour_dict in self.params.behaviours_dict.items():
                # randomly choose days for each interaction
                chosen_days = random.sample(range(7), k=behaviour_dict["visits"])
                self.graph.graph.nodes[node][behaviour] = {"visit_days": chosen_days}

        # do the interactions
        for behaviour, behaviour_dict in self.params.behaviours_dict.items():
            # add given behaviour if it should happen on current weekday
            if weekday in self.graph.graph.nodes[node][behaviour]["visit_days"]:

                # set the interactions
                self.graph.set_group_interaction_edges(
                    behaviour=behaviour,
                    node=node,
                    other_nodes=other_nodes,
                    group_size=behaviour_dict["num_people"]
                )

    def _remove_interactions(self):
        """Remove the added interactions from the graph"""

        self.graph.remove_group_interaction_edges()

    def _do_progression(self, node):
        """Progress the states based on the state transition dictionary

        Simplest sensible model: no age classes, uniform transitions
        between states, each vertex will have a state at each timestep.

        Parameters
        ----------
        node : int
            Name of node in the graph
        """

        next_time = self.curr_time + 1

        # get the state, then then possibilities
        state = self.states_dict[self.curr_time][node]
        node_age_group = self.graph.graph.nodes[node]["age_group"]

        # R, D, S stay the same (assumes recovery grants immunity)
        # E, A, I, H change based on transitions
        if state not in ["R", "D", "S"]:
            self.states_dict[next_time][node] = self._choose_from_distrib(
                                    node_age_group,
                                    self.params.state_transitions[state])
        else:
            self.states_dict[next_time][node] = state

    def _do_infection(self, node):
        """Spread the infection

        Parameters
        ----------
        node : int
            Name of node in the graph"""

        state = self.states_dict[self.curr_time][node]

        if state == "I" or state == "A":
            list(map(partial(self._infect_neighbours, node),
                     self.graph.graph.neighbors(node)))

    def _infect_neighbours(self, node, neighbour):
        """Infect a neighbour node

        Parameters
        ----------
        node : int
            Label of the node
        neighbour : int
            Label of the neighbour node
        """

        if self.states_dict[self.curr_time][neighbour] == "S":
            infection_prob = self.graph.graph[node][neighbour]["weight"]
            luck = random.random()
            if luck <= infection_prob:
                self.states_dict[self.curr_time + 1][neighbour] = "E"

    def _get_state_counts(self, time):
        """Return the number of nodes in given state at given time

        Parameters
        ----------
        time : int
            Time step at which the states are counted

        Returns
        -------
        dict
            Dictionary in form {state: count}
        """
        return Counter(self.states_dict[time].values())
