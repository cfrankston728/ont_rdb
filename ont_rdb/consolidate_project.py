import os
import shutil
import click

@click.command()
@click.argument('project_directory')
def consolidate(project_directory):
    """
    Replace symbolic links with copies of the files they link to in the given project directory.
    """
    try:
        consolidate_symlinks(os.path.join(project_directory, "src"), project_directory)
        consolidate_symlinks(os.path.join(project_directory, "ontology"), project_directory)
        consolidate_symlinks(os.path.join(project_directory, "informants"), project_directory)
        click.echo("Symbolic links have been replaced with file copies successfully.")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

def consolidate_symlinks(directory, project_directory):
    consolidate_script_path = os.path.join(project_directory, "src", "consolidate_project.py")
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.islink(file_path) and file_path != consolidate_script_path:
                target_path = os.readlink(file_path)
                os.remove(file_path)
                shutil.copy(target_path, file_path)

if __name__ == "__main__":
    consolidate()
