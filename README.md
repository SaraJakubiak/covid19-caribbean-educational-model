# COVID-19 in Jamaica: An Educational Model

## About
Graph-based modelling of COVID-19 spread in the Caribbean developed for the Centre for Design Informatics at The University of Edinburgh.

> Please note the model is intended for **educational purposes only**.
> 
> The repository does not include real Caribbean based data.

## Usage

### Setup
Project dependencies are listed in [env.yaml](./env.yaml) file, which can be used to create a virtual environment with `conda`.

```{shell}
conda env create -f env.yaml
conda activate covid19-caribbean-model
```

See [conda environments documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) for more information.

### Data
See the [data description](data/README.md) for detailed information about the origin and expected formatting of the data files. 

### Single simulation
Run a simulation for a single set of parameters. The model is run 10 times by default and the results are averaged.

#### Example
```{shell}
python -m src.run_single -i sample
```

#### Usage
```{shell}
usage: run_single.py [-h] -i file [-o file] [-n int] [-lg str] [-ng] [-q]
                     [-gp file] [-dtp file]

Runs the simulation once based on the files provided

optional arguments:
  -h, --help            show this help message and exit
  -i file, --input_spec_file file
                        JSON file specifying locations of data files required
                        for the specification. See input files specification
                        in data/README.md for details. 'real' defaults to
                        data/real/input-spec.json; 'sample' defaults to
                        data/sample/sample-input-spec.json
  -o file, --output_filename file
                        Filename where the results should be saved.
                        data/output/sample-output.json by default.
  -n int, --number_of_runs int
                        Number of runs of the simulation. If bigger than 1,
                        the simulation results are averaged across the runs.
                        10 by deafult.
  -lg str, --load_graph_dir str
                        When supplied, attempts to load graph from a file
                        {community_name}-graph.pkl in specified directory.
  -ng, --new_graph      Construct a graph on per simulation basis instead of
                        once per run.
  -q, --quiet           Do not print results to console.
  -gp file, --graph_plot_filename file
                        When supplied, saves PNG graph visualisation to given
                        filename.
  -dtp file, --doubling_time_plot_filename file
                        When supplied, saves PNG doubling time plot to given
                        filename.
```

### Multiple simulations
Run a simulation for each combination of app inputs provided.

#### Example
```{shell}
python -m src.run_all -i sample
```

#### Usage
```{shell}
usage: run_all.py [-h] -i file [-o dir] [-n int] [-tasks int] [-chunk int]
                  [-cpu int] [-uinter] [-dinter] [-gensample] [-lg str] [-ng]
                  [-sp]

Runs the simulation for each combination of app inputs provided

optional arguments:
  -h, --help            show this help message and exit
  -i file, --input_spec_file file
                        JSON file specifying locations of data files required
                        for the specification. See input files specification
                        in data/README.md for details. 'real' defaults to
                        data/real/input-spec.json; 'sample' defaults to
                        data/sample/sample-input-spec.json
  -o dir, --output_dir dir
                        Directory where the results should be saved.
                        data/output/ by default.
  -n int, --number_of_runs int
                        Number of runs per single simulation. If bigger than
                        1, the simulation results are averaged across the
                        runs. 10 by default.
  -tasks int, --max_tasks_per_child int
                        Number of maximum tasks per child subprocess. 1 by
                        default.
  -chunk int, --chunksize int
                        Chunksize of multiprocessing pool mapping. 1 by
                        default.
  -cpu int, --cpu int   Number of worker processes to use. Number of CPU cores
                        by default.
  -uinter, --use_intermediary
                        Compute only variants not already present in
                        intermediary/ directory.
  -dinter, --delete_intermediary
                        Delete the intermediary/ directory after the
                        simulations finish. intermediary/ directory stores
                        graphs and results of every variant in separate files
                        which are joint together after all simulations finish.
  -gensample, --generate_sample
                        Do not run the simulation and return dummy results
                        instead.
  -lg str, --load_graph_dir str
                        When supplied, attempts to load graph from a file
                        {community_name}-graph.pkl in specified directory.
  -ng, --new_graph      Construct a graph on per simulation basis instead of
                        once per community.
  -sp, --single_processing
                        Do not use multiprocessing.
```

### Graph generation
Graphs can be precomputed and saved to a file so that the simulation can load them and skip the graph building step.

#### Example
```{shell}
python -m src.generate_graphs -i sample -c A,B
```

#### Usage
```{shell}
usage: generate_graphs.py [-h] -i file [-o dir] [-c csv names]

Generate and save graphs for communities

optional arguments:
  -h, --help            show this help message and exit
  -i file, --input_spec_file file
                        JSON file specifying locations of data files required
                        for the specification. See input files specification
                        in data/README.md for details. 'real' defaults to
                        data/real/input-spec.json; 'sample' defaults to
                        data/sample/sample-input-spec.json
  -o dir, --output_dir dir
                        Directory where the results should be saved.
                        data/output/tmp by default.
  -c csv names, --communities csv names
                        Comma-separated list of communities for which to
                        generate graphs. If not supplied, generates graphs for
                        all communities listed in the community data file.
```

### Testing
A suit of unit tests is provided and can be run using

```{shell}
python -m pytest tests/
```

## License
[The 2-Clause BSD License](./LICENSE.md)