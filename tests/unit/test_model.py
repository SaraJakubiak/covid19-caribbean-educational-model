import random

import networkx as nx
import pytest

from src.graph import Graph
from src.model import Model
from src.params import Params


@pytest.fixture
def simple_graph():
    """Make a simple graph"""

    inner_graph = nx.Graph()
    inner_graph.add_nodes_from([0, 1, 2, 3, 4])
    inner_graph.add_weighted_edges_from([(0, 1, 1.0), (0, 2, 1.0), (2, 3, 1.0)])

    for node in inner_graph.nodes:
        inner_graph.nodes[node]["age_group"] = "(0, 9)"

    graph = Graph()
    graph.graph = inner_graph
    graph.time_horizon = 1

    return graph


@pytest.fixture
def state_transitions():
    """Simplified state transition dictionary"""

    return {
        "E": {"A": {"(0, 9)": 1}},
        "A": {"I": {"(0, 9)": 1}},
        "I": {"H": {"(0, 9)": 1}},
        "H": {"R": {"(0, 9)": 1}}
    }


@pytest.fixture
def dummy_model(simple_graph):
    """Model with dummy parameters"""

    params = Params()
    params.state_transitions = {}
    params.generic_infection = 1.0
    params.vulnerability_data = {}
    params.community_data = {}
    params.population_data = {}
    params.age_structure = {}
    params.population_size = 1
    params.behaviours = []
    params.behaviours_dict = {}

    model = Model(params, simple_graph)
    model.curr_time = 0

    return model


def test_choose_from_distrib(dummy_model):
    """Check if choices from given distribution follow the distribution"""

    n = 10000
    distrib = {"A": {"(0, 9)": 0.1}, "B": {"(0, 9)": 0.2}, "C": {"(0, 9)": 0.7}}
    key_counts = {"A": 0, "B": 0, "C": 0}

    for i in range(n):
        sample = dummy_model._choose_from_distrib("(0, 9)", distrib)
        key_counts[sample] += 1

    for key in distrib:
        assert key_counts[key]/n == pytest.approx(distrib[key]["(0, 9)"], rel=0.1)


def test_do_progression_without_change(dummy_model):
    """Test states which do not progress"""

    states_dict = {0: {
        0: "R",
        1: "D",
        2: "S",
    }, 1: {}}

    dummy_model.states_dict = states_dict
    for i in range(3):
        dummy_model._do_progression(i)

    assert dummy_model.states_dict[0] == dummy_model.states_dict[1]


def test_do_progression_with_change(state_transitions, dummy_model):
    """Test states which can transition during progression"""

    dummy_model.params.state_transitions = state_transitions

    dummy_model.graph.time_horizon = 5
    dummy_model._make_states_dict()
    dummy_model.states_dict[0] = {
        0: "E",
        1: "A",
        2: "I",
        3: "H"}

    # test after one progression
    for node in range(4):
        dummy_model._do_progression(node)
    assert dummy_model.states_dict[1] == {0: "A", 1: "I", 2: "H", 3: "R"}

    # test after five progressions
    for i in range(1, 5):
        dummy_model.curr_time = i
        for node in range(4):
            dummy_model._do_progression(node)
    assert dummy_model.states_dict[4] == {0: "R", 1: "R", 2: "R", 3: "R"}


def test_do_infection(dummy_model):
    """Check infection simulatation for simple graph"""

    states_dict = {
        0: {
            0: "I",
            1: "A",
            2: "S",
            3: "S",
            4: "S"},
        1: {0: "I",
            1: "A",
            2: "S",
            3: "S",
            4: "H"}}

    dummy_model.states_dict = states_dict

    # infection_prob is 1 so that infection is certain
    for i in range(5):
        dummy_model._do_infection(i)

    # infected/asymptomatic stay the same
    assert states_dict[1][0] == "I"
    assert states_dict[1][1] == "A"

    # neighbors have been exposed
    assert states_dict[1][2] == "E"

    # ...and non-neighbors have not
    assert states_dict[1][3] == "S"

    # other states stay the same
    assert states_dict[1][4] == "H"


def test_basic_simulation(dummy_model, state_transitions):
    """Run a sample simulation"""

    # node 3 is initially infected
    random.seed(0)
    dummy_model.graph.num_infected = 1
    dummy_model.graph.time_horizon = 5

    dummy_model.params.state_transitions = state_transitions
    dummy_model.params.generic_infection = 1.0

    dummy_model.basic_simulation()

    assert dummy_model.states_dict[5] == {0: "I", 1: "E", 2: "R", 3: "R", 4: "S"}


def test_get_output(dummy_model):
    """Test the simulation output"""

    # 1 timestep, 2 infections
    dummy_model.states_dict = {1: {
                                    0: "I",
                                    1: "I",
                                    2: "S"
                                }}
    assert dummy_model.get_results()["I"] == [2]

    # 1 timestep, no infections
    dummy_model.states_dict = {1: {
                                    0: "S",
                                    1: "S",
                                    2: "S"
                                }}
    assert dummy_model.get_results()["I"] == [0]

    # 1 timestep, empty dict
    dummy_model.states_dict = {1: {}}
    assert dummy_model.get_results()["I"] == [0]

    # 7 timesteps
    timesteps = 7
    dummy_model.graph.time_horizon = timesteps
    dummy_model.states_dict = {i: {0: "R", 1: "R", 2: "S"} for i in range(timesteps + 1)}
    output_dict = dummy_model.get_results()
    assert output_dict["R"] == [2]

    # sum of states at each timestep is equal to population size
    for i in range(0, timesteps, 7):
        sum_at_i = sum([output_dict[state][i] for state in Model.STATES.keys()])
        assert sum_at_i == 3
