import pytest
from src.params import Params


@pytest.fixture
def dummy_params():
    """Sample valid parameters"""

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

    return params


def test_behaviour_dict_conversion(dummy_params):
    """Test behaviour dictionary conversion method"""

    dummy_params.behaviours = ["a_0_0", "b_1_1"]

    behaviours_dict = dummy_params._convert_behaviours_to_dict()

    assert behaviours_dict == {"a": {"num_people": 0,
                                     "visits": 0},
                               "b": {"num_people": 1,
                                     "visits": 1}}
