import click
import swifter

import pandas as pd
import ast
import sys
import importlib
import os

try:
    snakemake
except NameError:
    snakemake = None

if snakemake is not None:
    informant_class_path = snakemake.params['informant_class_path']
    informant_ontology_script = snakemake.input['informant_ontology_script_name'] + '.informant_ontology.py'
    informant_ontology_dataframe_output_path = snakemake.output[0]

##########################################################################################################
def get_script_info(script_path):
    script_name, _ = os.path.splitext(os.path.basename(script_path))
    script_folder_path = os.path.dirname(script_path)
    return script_name, script_folder_path

def get_informant_pre_ontology_dataframe(script_path, 
                                         script_module,
                                         source_depth_dictionary,
                                         dynamic_depth_mode=True):
    
    """ informant_pre_ontology_dataframe = pd.DataFrame({'informant_subclass_name':[], 
                                                 'informant_subclass':[], 
                                                 'direct_parent_indices':[],
                                                 'direct_child_indices':[],
                                                 'is_sink':[], 
                                                 'source_depth':[],
                                                 'sink_depth':[],
                                                 'to_nearest_sink':[]}) """
    
    informant_pre_ontology_dataframe_rows_list = []

    with open(script_path, 'r') as file:
        tree = ast.parse(file.read(), filename=script_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                subclass_name = node.name
                subclass = getattr(script_module, subclass_name, None)

                if subclass_name in source_depth_dictionary and dynamic_depth_mode:
                    source_depth = source_depth_dictionary[subclass_name]
                else:
                    # Initialize a default example of the sub-class to acquire its source_depth.
                    subclass_instance = subclass()
                    source_depth = getattr(subclass_instance, 'source_depth', None)

                informant_pre_ontology_dataframe_rows_list.append({'informant_subclass_name':subclass_name,
                                                  'informant_subclass':subclass,
                                                  'direct_parent_indices':[],
                                                  'direct_child_indices':[],
                                                  'is_sink':1,
                                                  'source_depth':source_depth,
                                                  'sink_depth': 0,
                                                  'to_nearest_sink':[]})
                
    return pd.DataFrame(informant_pre_ontology_dataframe_rows_list)

def main(informant_class_path,
         informant_ontology_script_path,
         informant_ontology_dataframe_output_path):
    # Extract script information to import the appropriate modules
    informant_class_name, informant_class_folder_path = get_script_info(informant_class_path)
    informant_ontology_script_name, informant_ontology_script_folder_path = get_script_info(informant_ontology_script_path)
    # Import the appropriate modules and store relevant items:
    sys.path.append(informant_class_folder_path)
    informant_class_module = importlib.import_module(informant_class_name)
    source_depth_dictionary = informant_class_module.informant_source_depth_dictionary

    sys.path.append(informant_ontology_script_folder_path)
    print(informant_ontology_script_name)
    informant_ontology_script_module = importlib.import_module(informant_ontology_script_name)

    # Define the output path of the dataframe pickle file
    # informant_ontology_dataframe_output_path = '/home/groups/CEDAR/franksto/Informants/Informant_Ontologies/Informant_Ontology_Dataframes/'+informant_ontology_script_name +'_dataframe.pkl'

    informant_baseclass_dataframe = get_informant_pre_ontology_dataframe(informant_class_path,
                                                                         informant_class_module,
                                                                         source_depth_dictionary)
    
    informant_pre_ontology_dataframe = get_informant_pre_ontology_dataframe(informant_ontology_script_path,
                                                                            informant_ontology_script_module,
                                                                            source_depth_dictionary)

    # Create a dataframe to store all defined Informant subclasses, and indicate whether they are "leaf" informants.
    informant_ontology_dataframe = pd.concat([informant_baseclass_dataframe,
                                              informant_pre_ontology_dataframe],
                                             ignore_index=True)

    # Iterate through the rows of the dataframe
    for index, row in informant_ontology_dataframe.iterrows():

        informant_subclass = row['informant_subclass']
        # get informant_class_mro for informant_subclass
        direct_parent_informant_subclasses = [parent for parent in informant_subclass.__bases__ if parent is not object]
        # Use .__bases__...
        # Much could be done in parallel, but for now, whatever.
        for parent in direct_parent_informant_subclasses:

            # get the row corresponding to the parent:
            parent_index = informant_ontology_dataframe.loc[informant_ontology_dataframe['informant_subclass_name'] == parent.__name__].index[0]

            # A parent most surely is not a leaf:
            informant_ontology_dataframe.at[parent_index, 'is_sink'] = 0

            informant_ontology_dataframe.at[parent_index, 'direct_child_indices'].append(index)
            informant_ontology_dataframe.at[index, 'direct_parent_indices'].append(parent_index)

    # Compute sink depth:
    # Iterate through the vertices in order of decreasing source-depth:
    for index, row in informant_ontology_dataframe.sort_values(by='source_depth',
                                                               ascending=False).iterrows():
        # Get the parents of each vertex in this order:
        these_parent_indices = row['direct_parent_indices']
        for parent_index in these_parent_indices:
            # Get the children of each individual parent:
            these_child_indices = informant_ontology_dataframe.at[parent_index, 'direct_child_indices']

            # Compute the arg min and minimum value for sink_depth among these children:
            min_sink_depth = informant_ontology_dataframe.loc[these_child_indices]['sink_depth'].min()
            # Add 1 to find the sink_depth of the parent:
            informant_ontology_dataframe.at[parent_index, 'sink_depth'] = 1 + min_sink_depth

            # Determine the children that attain the minimum sink depth, and store them in the to_nearest_sink list.
            for child_index in these_child_indices:
                if informant_ontology_dataframe.at[child_index, 'sink_depth'] == min_sink_depth and child_index not in  informant_ontology_dataframe.at[parent_index, 'to_nearest_sink']:
                    informant_ontology_dataframe.at[parent_index, 'to_nearest_sink'].append(child_index)

    print(f"Chosen informant ontology script path: {informant_ontology_script_path}")   
    print("Informant subclasses defined in the informant ontology script:\n", informant_ontology_dataframe)
    # print("Leaf-trimmed Informant subclasses defined in the script:\n", trim_leaf(9, informant_ontology_dataframe))
    informant_ontology_dataframe.to_pickle(informant_ontology_dataframe_output_path)

@click.command()
@click.option('--inf','informant_class_path',
              required=True,
              help='Path to Informant class script.')
@click.option('--ont','informant_ontology_script_path',
              required=True,
              help='Path to script defining the desired Informant ontology.')
@click.option('--o','informant_ontology_dataframe_output_path',
              required=True,
              help='Path to output pickle file to save the Informant ontology dataframe.')
def click_main(informant_class_path,informant_ontology_script_path,informant_ontology_dataframe_output_path):
    
    main(informant_class_path,informant_ontology_script_path,informant_ontology_dataframe_output_path)
    
if __name__ == "__main__":
    if snakemake is None:
        click_main()
    else:
        main(informant_class_path,
             informant_ontology_script_path,
             informant_ontology_dataframe_output_path)
        
# print([item.__name__ for item in get_informant_class_mro(sc.HiC_TAD_Boundary_Bed_File)])