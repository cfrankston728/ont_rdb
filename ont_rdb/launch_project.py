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
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

def create_project_structure(base_directory, project_name):
    project_dir = os.path.join(base_directory, project_name)
    subdirs = ["informants", "ontology", "data", "src"]
    for subdir in subdirs:
        os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)
    return project_dir

def create_symlinks(project_dir, informant_class_path, ontology_script_path, informant_dataframe_path):
    src_symlink = os.path.join(project_dir, "src", "informant_class.py")
    ontology_symlink = os.path.join(project_dir, "ontology", os.path.basename(ontology_script_path))
    informants_symlink = os.path.join(project_dir, "informants", os.path.basename(informant_dataframe_path))

    if not os.path.islink(src_symlink):
        os.symlink(informant_class_path, src_symlink)
    if not os.path.islink(ontology_symlink):
        os.symlink(ontology_script_path, ontology_symlink)
    if not os.path.islink(informants_symlink):
        os.symlink(informant_dataframe_path, informants_symlink)

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
    consolidate_symlink = os.path.join(project_dir, "src", "consolidate_project.py")
    if not os.path.islink(consolidate_symlink):
        os.symlink(consolidate_script_path, consolidate_symlink)

if __name__ == "__main__":
    launch_project()
