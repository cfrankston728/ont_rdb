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
    try:
        project_dir = create_project_structure(base_directory, project_name)
        create_symlinks(project_dir, informant_class_path, ontology_script_path, informant_dataframe_path)
        create_metadata_file(project_dir, informant_class_path, ontology_script_path, informant_dataframe_path)
        create_symlink_for_consolidate_script(project_dir)
        create_explorer_notebook(project_dir, project_name)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

def create_project_structure(base_directory, project_name):
    project_dir = os.path.join(base_directory, project_name)
    subdirs = ["informants", "ontology", "data", "src"]
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
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# {project_name}_explorer.ipynb\n",
                    "## Import the informant class and selected ontology for this project.\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import informant_class\n",
                    "import importlib.util\n",
                    "import os\n",
                    "\n",
                    "# Define the path to the ontology script (assuming it's the only .py file in the ontology directory)\n",
                    "ontology_dir = \"../ontology\"\n",
                    "ontology_script_name = next(file for file in os.listdir(ontology_dir) if file.endswith(\".py\"))\n",
                    "ontology_script_path = os.path.join(ontology_dir, ontology_script_name)\n",
                    "\n",
                    "# Function to import module from file path\n",
                    "def import_module_from_path(module_name, path):\n",
                    "    spec = importlib.util.spec_from_file_location(module_name, path)\n",
                    "    module = importlib.util.module_from_spec(spec)\n",
                    "    spec.loader.exec_module(module)\n",
                    "    return module\n",
                    "\n",
                    "# Import the ontology script\n",
                    "ontology_script = import_module_from_path(\"ontology_script\", ontology_script_path)\n",
                    "\n",
                    "# Now you can use informant_class and ontology_script as needed\n",
                    "print(informant_class)\n",
                    "print(ontology_script)\n"
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
    
    notebook_path = os.path.join(project_dir, "src", f"{project_name}_explorer.ipynb")
    with open(notebook_path, 'w') as f:
        import json
        json.dump(notebook_content, f, indent=2)

if __name__ == "__main__":
    launch_project()
