import json


class Params:
    """Class for storing parameters information and loading external data

    Attributes
    ----------
    state_transitions: dict
        Dictionary of state transitions in form
        {initial_state: {new_state: {"age_group": probability}}}
    generic_infection : float
        Generic infection probability
    community_data : dict
        Dictionary with data about communities
    community : str
        Name of the community
    age_structure : dict
        Dictionary with number of people in given age groups
    population_size : int
        Size of the population
    behaviours: list
        List of behaviour tuples
    behaviours_dict: dict
        Dictionary representation of behaviours
    """

    def __init__(self):

        # Infection data
        self.state_transitions = None
        self.generic_infection = None

        # Community and population data
        self.community_data = None
        self.community = None
        self.age_structure = None
        self.population_size = None

        # App input
        self.behaviours = None
        self.behaviours_dict = None

    def set_infection_data_from_file(self, filename):
        """Load infection data from a JSON file

        Parameters
        ----------
        filename : str
            Path to the JSON file
        """

        with open(filename, "r") as f:
            infection_data = json.loads(f.read())

        self.state_transitions = infection_data["state_transitions"]
        self.generic_infection = infection_data["generic_infection"]

    def set_community_data_from_file(self, filename):
        """Load community data from a JSON file

        Parameters
        ----------
        filename : str
            Path to the JSON file
        """

        with open(filename, "r") as f:
            self.community_data = json.loads(f.read())

    def set_app_input(self, community, behaviours):
        """Set parameter values from the app input

        Parameters
        ----------
        community : str
            Name of the community
        behaviours : dict
            Dictionary of behaviours in form
            {behaviour_name: {behaviour_parameters}}
        """

        self.set_community(community)
        self.behaviours = behaviours

    def set_community(self, community):
        """Set community value and retrieve associated parameters

        Parameters
        ----------
        community : str
            Name of the community

        Raises
        ------
        Exception
            Throws exception if there is no community data loaded
        Exception
            Throws exception if the community is not in community data
        """

        if self.community_data is None:
            raise Exception("Please load the community data first.")
        if community not in self.community_data:
            raise Exception("Community {} not found in the community data".format(community))

        self.community = community
        self.age_structure = self.community_data[community]["age_structure"]
        self.population_size = sum(self.age_structure.values())

    def _convert_behaviours_to_dict(self):
        """Create a dictionary with behaviour and their attributes
        based on the behaviour strings (aka variants)

        Returns
        -------
        dict
            Dictionary in form
            {behaviour_name: {"num_people": int, "visits": int}}
        """

        behaviours_dict = {}
        for behaviour in self.behaviours:
            splitted = behaviour.split("_")
            name = "_".join(splitted[:-2])
            behaviours_dict[name] = {"visits": int(splitted[-2]),
                                     "num_people": int(splitted[-1])}
        return behaviours_dict
