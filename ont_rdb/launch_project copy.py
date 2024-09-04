import click
import pandas as pd
import os
import shutil
from datetime import datetime
import importlib.util

@click.command()
@click.argument('project_name')
@click.argument('informant_class_path')
@click.argument('ontology_script_path')
@click.argument('informant_dataframe_path')
@click.argument('base_directory')
def launch_project(project_name, informant_class_path, ontology_script_path, informant_dataframe_path, base_directory):
    """
    Initialize an ont_rdb project with symbolic links.
    """
    #try:
    project_dir = create_project_structure(base_directory, project_name)
    print("Created project structure.")
    create_symlinks(project_dir, informant_class_path, ontology_script_path, informant_dataframe_path)
    print("Linked informant_class script, ontology and informants.")
    create_metadata_file(project_dir, informant_class_path, ontology_script_path, informant_dataframe_path)
    print("Created metadata file.")
    create_symlink_for_consolidate_script(project_dir)
    print("Copied consolidate_project.py.")
    create_explorer_notebook(project_dir, project_name)
    print("Created explorer notebook.")
    #except Exception as e:
    #    click.echo(f"Error: {str(e)}", err=True)

def create_project_structure(base_directory, project_name):
    project_dir = os.path.join(base_directory, project_name)
    subdirs = ["informants", "ontology", "data", "src", "archive", "log", "controller"]
    for subdir in subdirs:
        os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)
    return project_dir

def create_symlinks(project_dir, informant_class_path, ontology_script_path, informant_dataframe_path):
    os.symlink(informant_class_path, os.path.join(project_dir, "src", "informant_class.py"))
    os.symlink(ontology_script_path, os.path.join(project_dir, "ontology", os.path.basename(ontology_script_path)))
    os.symlink(informant_dataframe_path, os.path.join(project_dir, "informants", os.path.basename(informant_dataframe_path)))

def create_metadata_file(project_dir, informant_class_path, ontology_script_path, informant_dataframe_path):
    metadata = {
        "project_name": os.path.basename(project_dir),
        "date_of_creation": str(datetime.now()),
        "informant_class_path": informant_class_path,
        "ontology_script_path": ontology_script_path,
        "informant_dataframe_path": informant_dataframe_path
    }
    with open(os.path.join(project_dir, "metadata.txt"), "w") as f:
        for key, value in metadata.items():
            f.write(f"{key}: {value}\n")

def create_symlink_for_consolidate_script(project_dir):
    consolidate_script_path = os.path.join(os.path.dirname(__file__), 'consolidate_project.py')
    os.symlink(consolidate_script_path, os.path.join(project_dir, "src", "consolidate_project.py"))

def create_explorer_notebook(project_dir, project_name):
    print(f"Creating explorer notebook for {project_name} in {project_dir}.") 
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# explorer.ipynb\n",
                    "## Import the informant class and selected ontology for this project.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from informant_class import *\n",
                    "import importlib.util\n",
                    "import os\n",
                    "import sys\n",
                    "\n",
                    "# Define this project directory: \n",
                    f"this_project_directory = '{project_dir}/'\n",
                    "\n",
                    "# Define the path to the ontology script (assuming it's the only .py file in the ontology directory)\n",
                    "ontology_dir = \"../ontology\"\n",
                    "ontology_script_name = next(file for file in os.listdir(ontology_dir) if file.endswith(\".py\"))\n",
                    "ontology_script_path = os.path.join(ontology_dir, ontology_script_name)\n",
                    "# Extract the module name by removing the '.py' extension\n",
                    "ontology_name = os.path.splitext(ontology_script_name)[0]\n",
                    "\n",
                    "# Function to import module from file path\n",
                    "def import_module_from_path(module_name, path):\n",
                    "    if path not in sys.path:\n",
                    "        sys.path.append(os.path.dirname(path))\n",
                    "    spec = importlib.util.spec_from_file_location(module_name, path)\n",
                    "    module = importlib.util.module_from_spec(spec)\n",
                    "    spec.loader.exec_module(module)\n",
                    "    sys.modules[module_name] = module # Register the module\n",
                    "    return module\n",
                    "\n",
                    "# Import the ontology script\n",
                    "print(ontology_script_path)\n",
                    "ont = import_module_from_path(ontology_name, ontology_script_path)\n",
                    "\n",
                    "# Now you can use informant_class and ontology_script as needed\n",
                    "print(ont)\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "informants_path = this_project_directory + 'informants/'\n",
                    "selection = ''\n",
                    "\n",
                    "import os\n",
                    "import pandas as pd\n",
                    "\n",
                    "def load_pickles_to_dict(directory):\n",
                    "    # Initialize an empty dictionary to store the dataframes\n",
                    "    Informant_Dataframes_dict = {}\n",
                    "    \n",
                    "    # Iterate over all files in the given directory\n",
                    "    for filename in os.listdir(directory):\n",
                    "        # Check if the file has a .pkl extension\n",
                    "        if filename.endswith('.pkl'):\n",
                    "            # Construct the full file path\n",
                    "            file_path = os.path.join(directory, filename)\n",
                    "            # Load the pickle file into a pandas dataframe\n",
                    "            this_inf_dataframe = Informant_Dataframe()\n",
                    "            this_inf_dataframe.load_df(file_path)\n",
                    "            # Store the dataframe in the dictionary with the key as the filename without .pkl suffix\n",
                    "            key = filename[:-4]\n",
                    "            Informant_Dataframes_dict[key] = this_inf_dataframe\n",
                    "    \n",
                    "    return Informant_Dataframes_dict\n",
                    "\n",
                    "directory = informants_path + selection\n",
                    "Informant_Dataframes_dict = load_pickles_to_dict(directory)\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Define Algorithms that will produce output informants from input informants (including parameters).\n"
                ]
            },
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": [
                    "this_algorithm_param_descriptions = {\n",
                    "}\n",
                    "this_algorithm = ont.Algorithm(name='',\n",
                    "                              description='',\n",
                    "                              parameter_descriptions=this_algorithm_param_descriptions,\n",
                    "                              script_path = '')\n",
                    "this_algorithm.__dict__\n"
                ]
            },
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": [
                    "import numpy as np\n",
                    "from itertools import product\n",
                    "\n",
                    "def construct_parameter_combinations_df(algorithm, parameter_combination_generators):\n",
                    "    \"\"\"\n",
                    "    Constructs an Informant Dataframe of parameter combinations for the Algorithm.\n",
                    "    parameter_combination_generators will be a dictionary containing lists of values for each parameter.\n",
                    "        Note: In general, it is possible to construct parameter combinations separately.\n",
                    "    \"\"\"\n",
                    "    if parameter_combination_generators is not None:\n",
                    "        keys = list(parameter_combination_generators.keys())\n",
                    "        values = [parameter_combination_generators[key] for key in keys]\n",
                    "\n",
                    "        # Generate all combinations of parameters using numpy\n",
                    "        parameter_combinations_array = np.array(np.meshgrid(*values)).T.reshape(-1, len(values))\n",
                    "        parameter_combinations_list = [dict(zip(keys, combination)) for combination in parameter_combinations_array]\n",
                    "    else:\n",
                    "        parameter_combinations_list = []\n",
                    "\n",
                    "    # Define a function to create Parameters\n",
                    "    def create_parameters(param_combination):\n",
                    "        return ont.Parameters(\n",
                    "            algorithm=algorithm,\n",
                    "            tags=[algorithm.name],\n",
                    "            parameter_descriptions=algorithm.parameter_descriptions,\n",
                    "            parameters=param_combination\n",
                    "        )\n",
                    "\n",
                    "    # Using ThreadPoolExecutor to parallelize the creation of Parameters\n",
                    "    with ThreadPoolExecutor() as executor:\n",
                    "        parameters_list = list(executor.map(create_parameters, parameter_combinations_list))\n",
                    "\n",
                    "    parameters_informant_dataframe = Informant_Dataframe()\n",
                    "    parameters_informant_dataframe.append(parameters_list)\n",
                    "    return parameters_informant_dataframe\n"
                ]
            },
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": [
                    "from concurrent.futures import ThreadPoolExecutor\n",
                    "\n",
                    "# Generate the parameter combinations for each algorithm:\n",
                    "this_algorithm_param_generators = {}\n",
                    "\n",
                    "param_combos = construct_parameter_combinations_df(this_algorithm, this_algorithm_param_generators)\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Prepare Output Paths and Corresponding Informants\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import datetime\n",
                    "\n",
                    "# Get the current date\n",
                    "current_date = datetime.date.today()\n",
                    "\n",
                    "# Extract year, month, and day\n",
                    "year = current_date.year\n",
                    "month = current_date.month\n",
                    "day = current_date.day\n",
                    "\n",
                    "# Format the date as 'YYYY-M-D'\n",
                    "formatted_date = f\"{year}-{month}-{day}\"\n",
                    "\n",
                    "# Print the formatted date\n",
                    "print(formatted_date)\n",
                    "trial_id = 'trial_1'\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import os\n",
                    "\n",
                    "def get_basename(path, num_parents=0):\n",
                    "    parts = []\n",
                    "    current_path = path\n",
                    "\n",
                    "    # Collect the specified number of parent directories\n",
                    "    for _ in range(num_parents + 1):  # +1 to include the basename itself\n",
                    "        current_path, tail = os.path.split(current_path)\n",
                    "        if tail:\n",
                    "            parts.append(tail)\n",
                    "        else:\n",
                    "            break\n",
                    "\n",
                    "    # Reverse the parts to get the correct order and join them with the OS separator\n",
                    "    return os.path.join(*reversed(parts))\n"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.8.5"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    notebook_path = os.path.join(project_dir, "src", f"explorer.ipynb")
    with open(notebook_path, 'w') as f:
        import json
        json.dump(notebook_content, f, indent=2)

if __name__ == "__main__":
    launch_project()
