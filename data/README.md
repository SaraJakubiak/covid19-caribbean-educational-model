# Model Data

## About
* Sample input files can be found in [sample/ folder](sample/)
    * [Infection data](sample/sample-infection-data.json)
      * serious illness (H) rates have been estimated based on [data from China](https://www.thelancet.com/journals/laninf/article/PIIS1473-3099(20)30243-7/fulltext)
      * other transitions have been estimated from [world data](https://www.worldometers.info/coronavirus/coronavirus-incubation-period/) and [Scotland data](https://www.ed.ac.uk/files/atoms/files/report_summary_-_model-based_evaluation_of_the_role_of_deprivation_on_deaths_due_to_covid-19_in_scotland.pdf)
    * [Simulation configuration](sample/sample-simulation-config.json) has been derived experimentally to match recorded doubling time in first weeks of infection spread under no intervention (doubling time approximately 2 days)
    * **Note: epidemiological estimates are approximate only and derived from a variety of sources over various stages of the pandemic, and as such should not be used for precise prediction or policy-making**

## Input files format
### Input files specification
Locations of the input files. Required by both ```src/run_single.py``` and ```src/run_all.py``` as ```-i``` flag.
```
{
    "community_data_filename": filepath,
    "infection_data_filename": filepath,
    "simulation_config_filename": filepath
    "app_input_filename": filepath, optional, required by src/run_single.py,
    "app_input_values_filename": filepath, optional, required by src/run_all.py,
}
```

### Community data
Data describing the age structure of the communities to be simulated. For each age-class the corresponding integer gives the number of people in the community in that age class - thi sis important because rates of different disease outcomes vary by age class.  The age categories are inclusive - that is, class `'(10,19)'` includes people of ages 10 through 19, including people of age 10 and people of age 19.  

```
{
    "community_name": {
        "age_structure": : {
            "(0,9)": int,
            "(10,19)": int,
            "(20,49)": int,
            "(50,59)": int,
            "(60,69)": int,
            "(70,79)": int,
            "(80, 150)": int
        }
    }
}
```

### Infection data
Data about both the probability of transmission given contact and the rates of progression through disease states.  Value `"generic_infection"` gives the probability of transmission given a contact between an infectious individual and a susceptible individual (currently all contacts have this same probability of transmission regardless of the nature of the contact).  Values in `"state_transitions"` specify the probability of movement from a disease state at a single time step (notionally, one time step is a day).  These probabilities may vary by age group. 

The current compartmental model in use is an expanded **SEIR** model, including the states **S**usceptible, **E**xposed, **A**symptomatic, **I**nfected, **H**ospitalised, **R**ecovered, and **D**ead.  Both asymptomatic and infectious people are considered to be capable of transmitting the disease.  

```
{
    "generic_infection": float,
    "state_transitions": {
        "state_a": {"state_b": {"age_group": float}}, 
    }
}
```

### Simulation configuration
Configuration values for simulations. Currently supported graph constructors are:
* [navigable_small_world](sample/sample-simulation-config.json)
  * *Please note the configuration values provided are based on small amount of data, and have been adjusted to produce an approximately 2-day epidemic doubling time*

```
{
    "time_horizon": int,
    "num_infected": int,
    "graph_config": {
        "name": name of the graph constructor,
        "params": dictionary of parameters relevant to the graph constructor,
        "closeness_threshold": int
    }
}
```

### App Input
Parameters provided by the application. See [All runs output](#All-runs-output) for more information.
```
{
    "community": community name,
    "behaviours": list of behaviours and their attributes (for example "food_shopping_1_1")
}
```

### App Input Values
Possible parameters generated from the application.

```
{
    "community": list of communities,
    "behaviour": list of behaviours (for example, food shopping),
    "num_visits": {
        "behavior_name": list of possible values of number of visits per week
    },
    "num_people": {
        "behavior_name": list of possible values of number of people met
    }
}
```

### Graphs
Additionally, the simulation can use a saved graph instead of creating a new one from scratch:
* the graphs can be generated with [supplied script](../src/generate_graphs.py)
* during loading the graph is validated against the [simulation config](sample/sample-simulation-config.json) to ensure that a graph is up to data with the specification in the file
* the saved graph is a pickled [Graph object](../src/graph.py) which holds the graph as well as its parameters

## Output format
### Single run output
Results of a single simulation
```
{
    "state_name": list of people in given state at given timestep 
}
```

### Simulations results for given community
Results of simulations over combinations of parameters for single community. See [example](output/results-example.json).

The data follows the form:
```
{
    "results": {
        "behaviour1_visits_people": {
            "behaviour2_visits_people": results of a single simulation (if only 2 behaviours present otherwise further nested)
            ...
        },
        "behaviour1_0_0": {
            ...
            "behaviour2_0_0": results of a single simulation
        }
    }
    "timestamp": str, time at beginning of the simulation,
    "community_data": {
        "name": str
        "population": int,
        "age_structure": : {
            "(0,9)": int,
            ...},
    }
    "sim_config": {
        "time_horizon": int,
        "num_infected": int,
        "graph_config": {
            "name": name of the graph constructor,
            "params": dictionary of parameters relevant to the graph constructor,
            "closeness_threshold": int
    },
    "infection_data": {"generic_infection": float,
                        "state_transitions": "state_a": {"state_b": {"age_group": float}}
    }
}
```
* each behaviour name is joint with its attributes: number of visits per week and number of people met. For example, "food_shopping_1_5" is food shopping behaviour with 1 visit per week and 5 people met.
* additionally, there is always behaviour_0_0 variant which should be chosen when:
  * the behaviour should not be considered
  * the value of either number of visits or people met is 0

