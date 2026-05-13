import ast
import importlib.util
import os
import sys
from pathlib import Path

import click
import pandas as pd


# ---------------------------------------------------------------------
# Path / import helpers
# ---------------------------------------------------------------------

def get_script_info(script_path):
    """
    Return the module stem and containing folder for a Python script path.
    """
    script_path = Path(script_path).resolve()
    script_name = script_path.stem
    script_folder_path = str(script_path.parent)
    return script_name, script_folder_path


def import_module_from_path(script_path, module_name=None, force_reload=True):
    """
    Import a Python module from a file path using a pickle-safe module name.

    This is intentionally registered in sys.modules before execution.
    Classes stored in the ontology dataframe must remain pickle-able, and
    pickle requires their __module__ name to be importable or at least present
    in sys.modules during serialization.

    Parameters
    ----------
    script_path : str or Path
        Path to the Python script to import.

    module_name : str or None
        Module name to register in sys.modules. If None, the script stem is
        used. This should usually be the real script/module stem, not an
        artificial temporary name.

    force_reload : bool
        If True, replace any existing sys.modules[module_name] entry. This
        avoids stale imports in notebook sessions.

    Returns
    -------
    module
        Imported module object.
    """
    script_path = Path(script_path).resolve()

    if module_name is None:
        module_name = script_path.stem

    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create module spec for {script_path}")

    module = importlib.util.module_from_spec(spec)

    script_folder = str(script_path.parent)
    inserted_path = False
    if script_folder not in sys.path:
        sys.path.insert(0, script_folder)
        inserted_path = True

    previous_module = sys.modules.get(module_name)

    if force_reload or module_name not in sys.modules:
        sys.modules[module_name] = module
    else:
        return sys.modules[module_name]

    try:
        spec.loader.exec_module(module)
    except Exception:
        if previous_module is not None:
            sys.modules[module_name] = previous_module
        else:
            sys.modules.pop(module_name, None)
        raise
    finally:
        if inserted_path:
            try:
                sys.path.remove(script_folder)
            except ValueError:
                pass

    return module


# ---------------------------------------------------------------------
# Ontology dataframe construction
# ---------------------------------------------------------------------

def get_informant_pre_ontology_dataframe(
    script_path,
    script_module,
    source_depth_dictionary,
    dynamic_depth_mode=True,
):
    """
    Parse a Python script for class definitions and create a preliminary
    informant ontology dataframe.

    The dataframe stores class objects, so imported modules must be registered
    under pickle-safe names before this function is called.
    """
    script_path = Path(script_path).resolve()
    rows = []

    with open(script_path, "r") as file:
        tree = ast.parse(file.read(), filename=str(script_path))

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        subclass_name = node.name
        subclass = getattr(script_module, subclass_name, None)

        if subclass is None:
            raise AttributeError(
                f"Class {subclass_name} was found in {script_path}, "
                f"but was not available on imported module {script_module.__name__}."
            )

        if subclass_name in source_depth_dictionary and dynamic_depth_mode:
            source_depth = source_depth_dictionary[subclass_name]
        else:
            subclass_instance = subclass()
            source_depth = getattr(subclass_instance, "source_depth", None)

        rows.append(
            {
                "informant_subclass_name": subclass_name,
                "informant_subclass": subclass,
                "direct_parent_indices": [],
                "direct_child_indices": [],
                "is_sink": 1,
                "source_depth": source_depth,
                "sink_depth": 0,
                "to_nearest_sink": [],
            }
        )

    return pd.DataFrame(rows)


def add_parent_child_indices(informant_ontology_dataframe):
    """
    Populate direct_parent_indices and direct_child_indices in-place.
    """
    for index, row in informant_ontology_dataframe.iterrows():
        informant_subclass = row["informant_subclass"]

        direct_parent_informant_subclasses = [
            parent for parent in informant_subclass.__bases__
            if parent is not object
        ]

        for parent in direct_parent_informant_subclasses:
            parent_matches = informant_ontology_dataframe.loc[
                informant_ontology_dataframe["informant_subclass_name"]
                == parent.__name__
            ].index

            if len(parent_matches) == 0:
                raise ValueError(
                    f"Parent class {parent.__name__} for "
                    f"{informant_subclass.__name__} was not found in the "
                    "ontology dataframe. This usually means the parent class "
                    "was imported from a module that was not included in the "
                    "base informant class script or ontology script."
                )

            parent_index = parent_matches[0]

            informant_ontology_dataframe.at[parent_index, "is_sink"] = 0
            informant_ontology_dataframe.at[
                parent_index,
                "direct_child_indices",
            ].append(index)
            informant_ontology_dataframe.at[
                index,
                "direct_parent_indices",
            ].append(parent_index)

    return informant_ontology_dataframe


def add_sink_depths(informant_ontology_dataframe):
    """
    Populate sink_depth and to_nearest_sink in-place.
    """
    sorted_dataframe = informant_ontology_dataframe.sort_values(
        by="source_depth",
        ascending=False,
    )

    for index, row in sorted_dataframe.iterrows():
        these_parent_indices = row["direct_parent_indices"]

        for parent_index in these_parent_indices:
            these_child_indices = informant_ontology_dataframe.at[
                parent_index,
                "direct_child_indices",
            ]

            min_sink_depth = informant_ontology_dataframe.loc[
                these_child_indices,
                "sink_depth",
            ].min()

            informant_ontology_dataframe.at[parent_index, "sink_depth"] = (
                1 + min_sink_depth
            )

            for child_index in these_child_indices:
                child_sink_depth = informant_ontology_dataframe.at[
                    child_index,
                    "sink_depth",
                ]

                parent_to_nearest_sink = informant_ontology_dataframe.at[
                    parent_index,
                    "to_nearest_sink",
                ]

                if (
                    child_sink_depth == min_sink_depth
                    and child_index not in parent_to_nearest_sink
                ):
                    parent_to_nearest_sink.append(child_index)

    return informant_ontology_dataframe


def main(
    informant_class_path,
    informant_ontology_script_path,
    informant_ontology_dataframe_output_path,
):
    """
    Build and save an informant ontology dataframe.

    This function is intentionally independent of Snakemake. It can be called
    directly from Python, from the Click CLI below, or from any external
    workflow runner.
    """
    informant_class_path = Path(informant_class_path).resolve()
    informant_ontology_script_path = Path(informant_ontology_script_path).resolve()
    informant_ontology_dataframe_output_path = Path(
        informant_ontology_dataframe_output_path
    ).resolve()

    informant_ontology_dataframe_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    informant_class_name, _ = get_script_info(informant_class_path)
    informant_ontology_script_name, _ = get_script_info(
        informant_ontology_script_path
    )

    informant_class_module = import_module_from_path(
        informant_class_path,
        module_name=informant_class_name,
        force_reload=True,
    )

    if not hasattr(informant_class_module, "informant_source_depth_dictionary"):
        raise AttributeError(
            f"{informant_class_path} does not define "
            "informant_source_depth_dictionary."
        )

    source_depth_dictionary = (
        informant_class_module.informant_source_depth_dictionary
    )

    informant_ontology_script_module = import_module_from_path(
        informant_ontology_script_path,
        module_name=informant_ontology_script_name,
        force_reload=True,
    )

    informant_baseclass_dataframe = get_informant_pre_ontology_dataframe(
        informant_class_path,
        informant_class_module,
        source_depth_dictionary,
    )

    informant_pre_ontology_dataframe = get_informant_pre_ontology_dataframe(
        informant_ontology_script_path,
        informant_ontology_script_module,
        source_depth_dictionary,
    )

    informant_ontology_dataframe = pd.concat(
        [
            informant_baseclass_dataframe,
            informant_pre_ontology_dataframe,
        ],
        ignore_index=True,
    )

    informant_ontology_dataframe = add_parent_child_indices(
        informant_ontology_dataframe,
    )

    informant_ontology_dataframe = add_sink_depths(
        informant_ontology_dataframe,
    )

    print(f"Chosen informant ontology script path: {informant_ontology_script_path}")
    print(
        "Informant subclasses defined in the informant ontology script:\n",
        informant_ontology_dataframe,
    )

    informant_ontology_dataframe.to_pickle(
        informant_ontology_dataframe_output_path,
    )

    return informant_ontology_dataframe


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

@click.command()
@click.option(
    "--inf",
    "informant_class_path",
    required=True,
    help="Path to Informant class script.",
)
@click.option(
    "--ont",
    "informant_ontology_script_path",
    required=True,
    help="Path to script defining the desired Informant ontology.",
)
@click.option(
    "--o",
    "informant_ontology_dataframe_output_path",
    required=True,
    help="Path to output pickle file to save the Informant ontology dataframe.",
)
def click_main(
    informant_class_path,
    informant_ontology_script_path,
    informant_ontology_dataframe_output_path,
):
    main(
        informant_class_path,
        informant_ontology_script_path,
        informant_ontology_dataframe_output_path,
    )


if __name__ == "__main__":
    click_main()