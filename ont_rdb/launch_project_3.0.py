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
@click.argument('explorer_auxiliaries_path')
@click.argument('informant_dataframe_path')
@click.argument('base_directory')
def launch_project(project_name, informant_class_path, ontology_script_path, explorer_auxiliaries_path, informant_dataframe_path, base_directory):
    """
    Initialize an ont_rdb project with symbolic links.
    """
    #try:
    project_dir = create_project_structure(base_directory, project_name)
    print("Created project structure.")
    create_symlinks(project_dir, informant_class_path, ontology_script_path, explorer_auxiliaries_path, informant_dataframe_path)
    print("Linked informant_class script, ontology and informants.")
    create_metadata_file(project_dir, informant_class_path, ontology_script_path, explorer_auxiliaries_path, informant_dataframe_path)
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

def create_symlinks(project_dir, informant_class_path, ontology_script_path, explorer_auxiliaries_path, informant_dataframe_path):
    os.symlink(informant_class_path, os.path.join(project_dir, "src", "informant_class.py"))
    os.symlink(explorer_auxiliaries_path, os.path.join(project_dir, "src", "explorer_auxiliaries.py"))
    os.symlink(ontology_script_path, os.path.join(project_dir, "ontology", os.path.basename(ontology_script_path)))
    os.symlink(informant_dataframe_path, os.path.join(project_dir, "informants", os.path.basename(informant_dataframe_path)))

def create_metadata_file(project_dir, informant_class_path, ontology_script_path, explorer_auxiliaries_path, informant_dataframe_path):
    metadata = {
        "project_name": os.path.basename(project_dir),
        "date_of_creation": str(datetime.now()),
        "informant_class_path": informant_class_path,
        "ontology_script_path": ontology_script_path,
        "explorer_auxiliaries_path":explorer_auxiliaries_path,
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
    
    cell_lines = [
    "from explorer_auxiliaries import *",
    "",
    "# Register project directory",
    "this_project_directory = os.path.dirname(os.getcwd())",
    'print(f"PROJECT DIRECTORY REGISTERED:\\n{this_project_directory}")',
    "",
    "# Load ontology script",
    'ontology_dir = "../ontology"',
    "",
    "ontology_script_path, ontology_name = next(",
    "    (os.path.join(ontology_dir, file), os.path.splitext(file)[0]) ",
    "    for file in os.listdir(ontology_dir) if file.endswith('.py')",
    ")",
    "",
    'print(f"\\nONTOLOGY REGISTERED:\\n{ontology_script_path}")',
    "ont = import_module_from_path(ontology_name, ontology_script_path)",
    "",
    "# Initialize informant dataframe dictionary",
    "idfs = {}"
    ]

    # Convert list into a multi-line string for writing
    jupyter_code_cell = "\n".join(cell_lines)

    notebook_content = {# TITLE CELL
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# explorer.ipynb\n",
                    "## Import the informant class and selected ontology for this project.\n"
                ]
            },# LOAD ONT_RDB MODULES, DEFINE AUX FUNCTIONS
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": jupyter_code_cell
            },
            {# INITIALIZE TRIAL
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Initialize this trial instance\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "\n",
                    "# Get the current date\n",
                    "current_date = datetime.date.today()\n",
                    "\n",
                    "# Extract year, month, and day\n",
                    "year = current_date.year\n",
                    "month = current_date.month\n",
                    "day = current_date.day\n",
                    "\n",
                    "# Format the date as 'YYYY/MM/DD' with leading zeros for month and day\n",
                    "formatted_date = f\"{year:04d}-{month:02d}-{day:02d}\"\n",
                    "\n",
                    "# Print the formatted date\n",
                    "print(formatted_date)\n",
                    "\n",
                    "trial_id = '0-trial-1'\n"
                ]
            },
            {# LINK DATA
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Link Data to this project\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "\n",
                    "target_directory = ''\n",
                    "link_name = ''\n",
                    "create_symlink(target_directory, link_name)\n"
                ]
            },
            {# CONSTRUCT INFORMANTS FOR LINKED DATA
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Construct Informants for linked data\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "informants_list = create_file_informant_list_from_folder(\n",
                    "    root_folder=\"\",\n",
                    "    explicit=True,\n",
                    "    suppress=True,\n",
                    "    description=\"\",\n",
                    "    use_location=True,\n",
                    "    attribute_sequence=[],\n",
                    "    informant_class=Informant,\n",
                    "    tags=[]\n",
                    ")"
                ]
            },
            {# STORE INFORMANTS INTO INFORMANT DATAFRAMES
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Store informants into informant dataframes. Choose an appropriate idf_key for future reference.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "idf_key = ''\n",
                    "idfs[idf_key] = Informant_Dataframe()\n",
                    "idfs[idf_key].append(informants_list)\n"
                ]
            },
            {# OPTIONALLY MODIFY INFORMANTS
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Optionally Modify Informants\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "for x in idfs[idf_key].df['informant']:\n",
                    "    pass\n"
                ]
            },
            {# SAVE INFORMANT DATAFRAMES
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Save Informant Dataframes\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "save_informant_dataframes(idfs, formatted_date, trial_id)\n",
                ]
            },
            {# LOAD INFORMANT DATAFRAMES
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Load Informant Dataframes\n"
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
                    "directory = informants_path + selection\n",
                    "idfs = load_pickles_to_dict(directory)\n"
                ]
            },
            {# DEFINE ALGORITHMS TO PROCESS INFORMANTS
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Define Algorithms that will produce output informants from input informants (including parameters). \n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "this_algorithm_name = ''\n",
                    "this_algorithm_param_descriptions = {}\n",
                    "this_algorithm = ont.Algorithm(\n",
                    "    name=this_algorithm_name,\n",
                    "    description='',\n",
                    "    tags=[],\n",
                    "    parameter_descriptions=this_algorithm_param_descriptions,\n",
                    "    script_path='',\n",
                    "    language='python'\n",
                    ")\n",
                    "this_algorithm.__dict__\n",
                    "Informant_Dataframes_dict['Algorithms'] = Informant_Dataframe()\n",
                    "Informant_Dataframes_dict['Algorithms'].append([this_algorithm])\n"
                ]
            },
            {# DEFINE PARAMETER COMBINATION GENERATORS FOR EACH ALGORITHM
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Define parameter generators for each algorithm. \n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Generate the parameter combinations for each algorithm:\n",
                    "informant_list = None\n",
                    "this_algorithm_param_generators = {\n",
                    "    'informant': informant_list\n",
                    "}\n",
                    "\n",
                    "param_combos = construct_parameter_combinations_df(this_algorithm, this_algorithm_param_generators)\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Apply this function to each combination in param_combos\n",
                    "unpacked_combinations = [unpack_informant_params(combo, this_algorithm) for combo in param_combos.df['informant']]\n",
                    "\n",
                    "# Now `unpacked_combinations` contains fully unpacked parameter combinations\n"
                ]
            },
            {# PREPARE OUTPUT PATHS (LOCATIONS) AND CORRESPONDING OUTPUT INFORMANTS
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Prepare Output Locations and Corresponding Informants. \n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    
                ]
            },
            {# GENERATE PARAMETER-SPECIFIED OUTPUT PATHS FOR EXPERIMENTAL TRIALS
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Generate parameter-specified output paths for experimental trials. \n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Prepare references for this experiment, including the date, logical reference to the output files, and a reference to the trial (change upon completion of a trial)\n",
                    "# This will automatically track chronology per day.\n",
                    "# July 3, 2024: I should also check whether the experiment/trial directory already exists, and require an override to continue. []\n",
                    "this_experiment_title = 'output_informants'\n",
                    "this_experiment = os.path.join(formatted_date, this_experiment_title)\n",
                    "#trial_id = 'trial_4_unique_locations'\n",
                    "\n",
                    "# The outputs will be stored in the data directory under the appropriate name:\n",
                    "data_dir = os.path.join(this_project_directory, 'data')\n",
                    "output_dir = os.path.join(data_dir, this_experiment, trial_id)\n",
                    "\n",
                    "# Prepare an informant dataframe to reference the output files:\n",
                    "Output_informant_df = Informant_Dataframe()\n",
                    "Output_informant_list = []\n",
                    "\n",
                    "# For each parameter combination, prepare a corresponding informant to refer to a designated Output file:\n",
                    "for param_combo_id in range(len(param_combos.df)):\n",
                    "    # We extract each parameter combination's informant:\n",
                    "    this_param_combo = param_combos.df.loc[param_combo_id]['informant']\n",
                    "    # Note that the algorithm is already referenced by the parameter combination:\n",
                    "    this_algorithm = this_param_combo.algorithm\n",
                    "    # We can extract the parameter values as well:\n",
                    "    these_params = this_param_combo.parameters\n",
                    "\n",
                    "    this_input_informant = these_params['informant']\n",
                    "\n",
                    "    # The parameters I have passed are Informants, and we should account for that. This is sloppy and will be addressed later:\n",
                    "    #non_inf_params = list(these_params)[1:len(these_params)]\n",
                    "    #this_output_dir_extension = this_bw.target + '/' + this_bw.bigWig_signal\n",
                    "    # We will also include meta data in the name of the output paths, which will correspond to the meta-data stored in the Informant:\n",
                    "\n",
                    "    # Finally we will define an informant object for the file that will be constructed in the chosen path, and we will also store this path in the informant object:\n",
                    "    \n",
                    "    # Use the input informant to push information through the process flow, including new attributes.\n",
                    "    output_informant = convert_to_informant_class(this_input_informant, Informant, suppress=True, push=True,\n",
                    "                                                  algorithm=this_algorithm,\n",
                    "                                                  algorithmic_parameters=these_params)\n",
                    "    output_informant.location = output_dir + '/'\n",
                    "    for key in sorted(this_algorithm_param_generators):\n",
                    "        value = these_params[key]\n",
                    "\n",
                    "        # Determine how to append the value based on its type\n",
                    "        if isinstance(value, str):\n",
                    "            # Append the key and value directly as strings\n",
                    "            output_informant.location = os.path.join(output_informant.location, f\"{key}-{value}\")\n",
                    "        elif hasattr(value, 'name'):\n",
                    "            # Append the key and the 'name' attribute of the value\n",
                    "            output_informant.location = os.path.join(output_informant.location, f\"{key}-{value.name}\")\n",
                    "        else:\n",
                    "            # Handle the case where neither condition is met (optional)\n",
                    "            pass\n",
                    "    output_informant.name = f'{this_algorithm_name}-output-' + output_informant.name + '-input'\n",
                    "    output_informant.description = f'Output of {this_algorithm_name} applied to ' + output_informant.description\n",
                    "    # Update the attributes that will change for the output informant (ex: name, description, location)\n",
                    "\n",
                    "    # Append the constructed informant to the list of informant outputs:\n",
                    "    Output_informant_list.append(output_informant)\n",
                    "\n",
                    "# Finally, append all of the constructed output informants to the output informant dataframe.\n",
                    "Output_informant_df.append(Output_informant_list)\n",
                    "\n",
                    "# These output informants refer to the path that will contain constructed files, but these paths are not necessarily populated yet.\n",
                    "# To populate these paths, we will need to construct the files that are to be located there.\n",
                    "# We can refer to the Algorithm, Parameters, and location of each informant to define a command that will construct the desired output file.\n",
                    "# These data have been stored within each output informant itself.\n"
                ]
            },
            {# PREPARE CONSTRUCTOR COMMANDS TO POPULATE LOCATIONS OF OUTPUT INFORMANTS
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Prepare Constructor Commands to populate Locations of Output Informants. \n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "commands_list = []\n",
                    "for x in Output_informant_df.df['informant']:\n",
                    "    command_line_params = build_command_line_params(x.algorithmic_parameters, use_keys=True)\n",
                    "\n",
                    "    # If dealing with individual Bed files, use x.location\n",
                    "    #this_location = x.location\n",
                    "\n",
                    "    # If dealing with bin-labeled bed files, use the extension including the name of the base bed file it belongs to:\n",
                    "    this_location = x.location\n",
                    "    #print(this_location)\n",
                    "    this_command = f'mkdir -p {os.path.dirname(this_location)} && {this_algorithm.language} {this_algorithm.script_path} {command_line_params} --output-dir {this_location}'\n",
                    "    x.constructor_command = this_command\n",
                    "    commands_list.append(this_command)\n",
                    "commands_list[0]\n"
                ]
            },
            {# UPDATE AND SAVE INFORMANT DATAFRAMES
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Update and Save Informant Dataframes. \n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "output_key = ''\n",
                    "idfs[output_key] = Output_informant_df\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "save_informant_dataframes(Informant_Dataframes_dict)\n"
                ]
            },
            {# DEFINE FUNCTION TO DETERMINE IF OUTPUT INFORMANTS WERE SUCCESSFULLY POPULATED
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Define a function to determine if output informants were successfully populated. \n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def is_successful(x):\n",
                    "    return False\n"
                ]
            },
            {# GENERATE SHELL SCRIPTS TO SUBMIT TO COMPUTING CLUSTER
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Generate Shell Scripts to submit to Computing Cluster. \n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def generate_shell_scripts(commands_list, batch_size, data_dir, this_experiment, trial_id, formatted_date):\n",
                    "    # Directory to store the generated shell scripts\n",
                    "    scripts_dir = os.path.join(data_dir, f\"{this_experiment}_constructors\", trial_id)\n",
                    "    os.makedirs(scripts_dir, exist_ok=True)\n",
                    "\n",
                    "    job_base_name = '_'.join([formatted_date, trial_id, this_experiment])\n",
                    "    \n",
                    "    # Calculate the number of batches\n",
                    "    num_batches = math.ceil(len(commands_list) / batch_size)\n",
                    "\n",
                    "    # Loop over the commands in batches and create a shell script for each batch\n",
                    "    for batch_num in range(num_batches):\n",
                    "        script_name = f\"submit_job_batch_{batch_num+1}.sh\"\n",
                    "        script_path = os.path.join(scripts_dir, script_name)\n",
                    "\n",
                    "        # SLURM job script template\n",
                    "        script_content = f\"\"\"#!/bin/bash\n",
                    "#SBATCH --partition exacloud\n",
                    "#SBATCH --output={job_base_name}_batch_{batch_num+1}_%j.out         ### File in which to store job output\n",
                    "#SBATCH --error={job_base_name}_batch_{batch_num+1}_%j.err          ### File in which to store job error messages\n",
                    "#SBATCH --cpus-per-task=2\n",
                    "#SBATCH --mem=95G\n",
                    "#SBATCH --time=4:00:00\n",
                    "#SBATCH --job-name={job_base_name}_batch_{batch_num+1}\n",
                    "\n",
                    "#conda activate pyTAD_analysis\n",
                    "\"\"\"\n",
                    "\n",
                    "        # Get the commands for the current batch\n",
                    "        batch_commands = commands_list[batch_num * batch_size : (batch_num + 1) * batch_size]\n",
                    "\n",
                    "        # Add each command to the script\n",
                    "        for command in batch_commands:\n",
                    "            script_content += f\"/usr/bin/time {command}\\n\"\n",
                    "\n",
                    "        # Write the script content to the file\n",
                    "        with open(script_path, \"w\") as script_file:\n",
                    "            script_file.write(script_content)\n",
                    "\n",
                    "        # Make the script executable\n",
                    "        os.chmod(script_path, 0o755)\n",
                    "\n",
                    "    print(f\"Generated {num_batches} shell scripts in {scripts_dir}\")\n",
                    "    print(f\"Execute the following command to submit to slurm:\\n\")\n",
                    "    print(f'mkdir -p {os.path.join(data_dir, this_experiment)}_process_err_out && cd {os.path.join(data_dir, this_experiment)}_process_err_out && for script in {scripts_dir}/*.sh; do sbatch \"$script\"; done')\n",
                    "\n",
                    "# Example usage\n",
                    "#data_dir = \"/path/to/data_dir\"\n",
                    "#this_experiment = \"experiment_name\"\n",
                    "#trial_id = \"trial_id\"\n",
                    "#formatted_date = \"20230706\"\n",
                    "this_output_key = ''\n",
                    "unsuccessful_informants = [x for x in  Informant_Dataframes_dict[this_output_key].parallel_filter(\"(not is_successful(@self))\",\n",
                    "                                                                                   additional_context = {'is_successful':is_successful})['informant']]\n",
                    "\n",
                    "these_locations = [x.location for x in unsuccessful_informants]\n",
                    "# Execute the directory removal in parallel\n",
                    "with concurrent.futures.ThreadPoolExecutor() as executor:\n",
                    "    results = list(executor.map(remove_directory, these_locations))\n",
                    "    \n",
                    "this_commands_list = [x.constructor_command for x in unsuccessful_informants]\n",
                    "#[x.constructor_command for x in  Informant_Dataframes_dict['scHiCluster_imputed_files'].df['informant']]\n",
                    "num_commands = len(this_commands_list)\n",
                    "batch_size = 1#math.ceil(num_commands/36)\n",
                    "#print(informants)]\n",
                    "\n",
                    "generate_shell_scripts(this_commands_list, batch_size, data_dir, this_experiment, trial_id, formatted_date)\n"
                ]
            },
            {# INVESTIGATE INFORMANTS
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Investigate informants. \n"
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
