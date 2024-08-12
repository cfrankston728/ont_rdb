import os
import pandas as pd
import swifter
from datetime import datetime
import re
import shutil

from concurrent.futures import ThreadPoolExecutor
from functools import partial
#import sys
#sys.path.append('/home/cfrankston/Projects/ont_rdb/ont_rdb')
# FIX THIS, APPEND PACKAGE DIRECTORY
###############################################################################################################
# Description

""" 
This script defines the Informant class and associated functions.

An Informant is an abstract object designed to identify, reference, annotate, and organize objects and their attributes in such a way that facilitates a personalizable, ontologically-integrated storage of data. They enable users to construct, acquire and explore personalized, arbitrarily-detailed formal ontologies and to annotate and organize data in the context of a chosen ontology.

Associated functions facilitate automated extraction, annotation, and organization of data that is stored within any directory structure by leveraging existing features of its organization. 

Informants can be constructed, stored and saved into auxiliary data-structures such as dataframes. The implementation here expects Informants to be stored within pandas dataframes with specific identifiers.
"""

###############################################################################################################
# Functions to enable efficient integration of defined informants with a pre-computed informant dataframe of a specific structure.

# Define a method to retrieve a informant given a reference_informant_name from a chosen informant_dataframe.
def retrieve_informant(informant_name, 
                       informant_dataframe):
    """
    Retrieve an informant from a chosen informant_dataframe based on its name.

    Args:
        informant_name (str): Name of the informant.
        informant_dataframe (pd.DataFrame): Dataframe containing informant information, with one column 'name' storing the names of informants, and another column 'informant' storing Informant objects.

    Returns:
        Informant: Retrieved informant.
    
    Raises:
        KeyError: If the informant with the specified ID is not found in the informant_dataframe.
    """
    # Output the informant name being searched
    # print(f"Searching for Informant: {informant_name}")

    # Filter the dataframe for rows matching the informant_name
    filtered_df = informant_dataframe.df[informant_dataframe.df['name'] == informant_name]

    # Output the filtered DataFrame
    # print(f"Filtered DataFrame:\n{filtered_df}")

    if not filtered_df.empty:
        return filtered_df.iloc[0]['informant']
    else:
        print(f"Informant ID '{informant_name}' not found in the informant_dataframe.")
        return None

# Define a simple method to update a "redundancy value," which returns False from None, and True from a bool type. This is used to prune redundant information stored within Informants.
def update_redundancy_value(redundancy_value)-> bool:
    """
    Update a redundancy value.

    Args:
        redundancy_value: The input redundancy value.

    Returns:
        bool: Updated redundancy value (False for None, True for a bool type).

    Raises:
        ValueError: If the input is not a valid redundancy value (None, False, or True).
    """
    if redundancy_value is None:
        return False
    elif isinstance(redundancy_value, bool):
        return True
    else:
        raise ValueError(f"Input '{redundancy_value}' is not a valid redundancy value. Valid redundancy values are None, False, or True.")

####################################################################################################
# Some simple Auxiliary functions that enable exploration of Informant ontology.
def set_informant_class_leaf_status_to_False(informant_class):
    informant_class.is_informant_class_leaf = False
    
def get_informant_class_attributes(informant_class)-> list:
    """
    Get the attributes of an informant class.

    Args:
        informant_class: The informant class.

    Returns:
        list: List of attributes of the informant class.
    """
    return list(informant_class().__dict__.keys())

def get_distinct_informant_class_attributes(informant_class_1, 
                                            informant_class_2=None)-> list:
    """
    Get distinct attributes of an informant class compared to another class.

    Args:
        informant_class_1: The first informant class.
        informant_class_2: The second informant class.

    Returns:
        list: List of distinct attributes of the informant class 1 compared to class 2.
    """
    if informant_class_1 == Informant:
        return []
    informant_class_2 = informant_class_2 or informant_class_1.__bases__[0]
    return [attribute for attribute in get_informant_class_attributes(informant_class_1) if attribute not in get_informant_class_attributes(informant_class_2)]

def get_informant_class_mro(informant_class)-> list:
    """
    Get the inheritance list of an informant class.

    Args:
        informant_class: The informant class.

    Returns:
        list: List of classes in the inheritance hierarchy of the informant class.
    """
    return [item for item in informant_class.mro() if item != object]

def get_informant_inherited_attributes_list(informant_class)-> dict:
    """
    Get inherited attributes of an informant class.

    Args:
        informant_class: The informant class.

    Returns:
        dict: Dictionary mapping class names to distinct inherited attributes.
    """
    return {item.__name__:get_distinct_informant_class_attributes(item) for item in informant_class.mro() if item != object}


informant_source_depth_dictionary = {'Informant':0}
# informant_sink_depth_dictionary = {'Informant':0} # sink_depth will be computed in the informant_ontology_dataframe.py script.
####################################################################################################
# Informant class definition:
# UPDATE, 2024-8-8: I will include "algorithm" and "algorithmic_parameters" attributes for every informant to help track process flows. The "algorithm" attribute will obtain an Algorithm informant (A{f}) that describes (f) such that it has parameters (with their descriptions, as I have already included), and that is coordinated with the informants obtainable from the "algorithmic_parameters" attribute. In particular, the parameter descriptions of the algorithm will encode the keys to a dictionary stored under the "algorithmic_parameters" attribute, and within the "algorithmic_parameters" attribute dictionary, those keys will correspond to informants and parameter instantiations [Xi] such that [f o Xi] is the object being described.
# This means that, probably, I should encode the Algorithm and Parameters informant sub-classes directly in this script rather than in any particular ontology.

class Informant:
    """
    Base class for all Informants.
    An Informant is an abstract object designed to identify and organize attributes of objects that are stored in memory.

    Informants are designed to facilitate the construction and organization of an arbitrarily-detailed object-annotation structure or filing system.
    In particular, Informants are designed to facilitate extraction, annotation, and organization of data that is stored within an existing directory structure.

    Attributes:
        name (str): Identifier for the informant.
        description (str): Description of the informant.
        tags (list): List of tags associated with the informant.
        reference_informant_names (list): List of informant IDs for parents to the informant.
        informant_class (str): Type of the informant.
        is_informant_leaf (bool): Indicates whether 
        time_stamp: Timestamp associated with the informant.

        algorithm (object): Algorithm that was used to construct the informant data, containing a dictionary of parameter descriptions and a path to a script and/or documentation.
        algorithmic_parameters (object): Parameters that were fed into the Algorithm to instantiate the particular informant's data, a dictionary that associates informants to the parameters of the Algorithm.
        constructor_command (str): A bash command that is used to construct the informant's associated data stored in its location.
    """
    def __init__(self, dynamic_depth_mode=True, explicit=True, overwrite=False, suppress=False, **kwargs):

        #########################################################################
        # Initialize attributes that will be stored for every Informant and by default reference kwargs:
        self.name = kwargs.get('name', None)
        self.description = kwargs.get('description', None)
        self.tags = kwargs.get('tags', [])
        self.reference_informant_names = kwargs.get('reference_informant_names', [])
        # self.time_stamp = kwargs.get('time_stamp', None)
        
        self.algorithm = kwargs.get('algorithm', None)
        self.algorithmic_parameters = kwargs.get('algorithmic_parameters', None) # Since some other informants in the current ontology have 'parameters' as an attribute, I named this "algorithmic_parameters".
        self.constructor_command = kwargs.get('constructor_command', '')
        ###########################################################################
        # Initialize attributes that will be stored for every Informant and by default do NOT reference kwargs:        
        self.informant_class = self.__class__.__name__
        self.reference_informant_name_redundancy_values = {reference_informant_name:None for reference_informant_name in self.reference_informant_names}
        self.source_depth = 0
        # self.sink_depth = 0

        if self.informant_class in informant_source_depth_dictionary and dynamic_depth_mode:
                self.source_depth = informant_source_depth_dictionary[self.informant_class]
        else:
            direct_parent_informant_subclasses = [parent for parent in self.__class__.__bases__ if parent is not object]
            self.source_depth = 1 + max(parent_class().source_depth for parent_class in direct_parent_informant_subclasses)
            if self.informant_class not in informant_source_depth_dictionary:
                informant_source_depth_dictionary[self.informant_class] = self.source_depth

        # self.remove_redundant_reference_informant_names()
        if explicit:
                for key, value in kwargs.items():
                    if key in ['informant_class',
                               'reference_informant_name_redundancy_values',
                               'source_depth'] and not overwrite:
                        if not suppress:
                            print(f"Warning: Attribute '{key}' was not set explicitly because '{key}' by default does not reference kwargs and 'overwrite' is False. To initialize an Informant object with an explicit value of '{key}', 'overwrite' must be set to True. Note that overwriting such a key can have unexpected effects and may lead to errors, and therefore should be avoided if possible.")
                    else:
                        setattr(self, key, value)
    def add_tag(self, tag):
        """
        Add a tag to the list of tags associated with the informant.

        Args:
            tag (str): Tag to be added.
        """
        self.tags.append(tag)

    def remove_tag(self, tag):
        """
        Remove a tag from the list of tags associated with the informant.

        Args:
            tag (str): Tag to be added.
        """
        self.tags = [tag_item for tag_item in self.tags if tag_item != tag]
    
    def get_reference_informant_name_rooted_tree(self, reference_informant_dataframe, level=0):
        if self.reference_informant_names == []:
            if level > 0:
                return [self.name]
        elif level in [0, 1]:
            tree_extension = []
            for reference_informant_name in self.reference_informant_names:
                retrieved_informant = retrieve_informant(reference_informant_name, reference_informant_dataframe)
                if retrieved_informant is not None:
                    tree_extension.append(retrieved_informant.get_reference_informant_name_rooted_tree(reference_informant_dataframe, level=1))

            if level == 0:
                return tree_extension
            else:
                return [self.name, tree_extension]
        return []
        
    def update_reference_informant_name_redundancy(self, 
                                             reference_informant_dataframe, 
                                             level=0, 
                                             tallying_informant=None):
        """
        Recursively updates the redundancy values of source informants for a chosen "tallying_informant" and removes redundant names from the list. source-Informant relationships are stored in the passed reference_informant_dataframe.

        If a rooted digraph is constructed whose root is a specified Informant R, whose nodes are all Informants, and whose edges are direct parent-child relations from source-Informants to other Informants, the non-redundant source-Informants of R are those nodes in the rooted digraph that have a direct parent-child relation to R and have no direct parent-child relation to any other node of the digraph.  
        """

        # Check to see if there are any reference_informant_names
        if self.reference_informant_names == []:
            # If not, then either this is a terminal source informant, or there are no source informants.
            # Level is updated recursively, and if it is >0, then this is a terminal source informant.
            if level > 0:
                # We record this terminal source informant name and update its redundancy value.
                # tallying_informant is also updated recursively, and is guaranteed to be populated by a informant if level > 0.

                # Update the redundancy value for this source informant name in the tallying informant's source informant redundancy values:
                this_name = self.name
                this_redundancy_value = tallying_informant.reference_informant_name_redundancy_values[this_name]
                tallying_informant.reference_informant_name_redundancy_values[this_name] = update_redundancy_value(this_redundancy_value)
        else:
            # Otherwise, there are more reference_informant_names to investigate.
            # For each of them, we retrieve the corresponding source informant and find its (higher order) reference_informant_names.
            # Then we recursively update the redundancy values of the tallying informant.
            for reference_informant_name in self.reference_informant_names:
                this_name = reference_informant_name
                this_redundancy_value = tallying_informant.reference_informant_name_redundancy_values[this_name]
                tallying_informant.reference_informant_name_redundancy_values[this_name] = update_redundancy_value(this_redundancy_value)

                retrieved_informant = retrieve_informant(reference_informant_name, reference_informant_dataframe)

                if retrieved_informant is not None:
                    retrieved_informant.update_reference_informant_name_redundancy(reference_informant_dataframe, 
                                                                                                level=1, 
                                                                                                tallying_informant=self)
        # The only alternative is that the informant has no source informant names. In this case there is nothing to update.

#################################################################################################
# A useful function for the pruning away of redundant information stored in an informant, with reference to a pre-constructed dataframe

def update_reference_informant_name_redundancy(informant:Informant, 
                                         reference_informant_dataframe):
    """
    Leverages the Informant.update_reference_informant_name_redundancy method to recursively update the redundancy values of source informants, with the tallying informant chosen as the passed informant itself.
    """
    # Let the informant update its source informant name redundancies, using itself as the tallying informant.
    informant.update_reference_informant_name_redundancy(reference_informant_dataframe, 
                                                      tallying_informant=informant)
    informant.reference_informant_names = [reference_informant_name for reference_informant_name in informant.reference_informant_name_redundancy_values if informant.reference_informant_name_redundancy_values[reference_informant_name] == False]
    del informant.__dict__['reference_informant_name_redundancy_values']

############################################################################
# Basic Informant Sub-Classes:
class Directory_Informant(Informant):
    """
    Informant with additional attributes for location.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.location = kwargs.get('location', None)
        self.external_locations = kwargs.get('external_locations', None)
    def file_list(self):
        folder_path = self.location
        if os.path.isdir(folder_path):
            with os.scandir(folder_path) as entries:
                files = [entry.name for entry in entries if entry.is_file()]
        else:
            files = 'Invalid folder path'
        return files
    def file_count(self):
        this_file_list = self.file_list()
        if this_file_list == 'Invalid folder path':
            return -1
        return len(this_file_list)

class File_Informant(Directory_Informant):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.file_type = kwargs.get('file_type', None)
    def rename_location(self, new_location):
        # Check if the file exists at the current location
        if os.path.exists(self.location):
            # Move the file to the new location
            shutil.move(self.location, new_location)
            # Update the location attribute
            self.location = new_location
        else:
            print(f"File does not exist at {self.location}")
    def is_populated(self):
        return os.path.exists(self.location)
    def loc_type_count(self, file_types=None, max_depth=None):
        if file_types is None:
            if self.file_type is not None:
                file_types = [self.file_type]
            else:
                return -1
        
        if not isinstance(file_types, list):
            file_types = [file_types]
        
        count = 0
        if os.path.isdir(self.location):
            for root, _, files in os.walk(self.location):
                # Calculate the current depth
                current_depth = root[len(self.location):].count(os.sep)
                if max_depth is not None and current_depth > max_depth:
                    # If the current depth exceeds max_depth, skip this directory
                    continue

                for file in files:
                    if any(file.endswith(ft) for ft in file_types):
                        count += 1
        elif os.path.isfile(self.location):
            if any(self.location.endswith(ft) for ft in file_types):
                count = 1

        return count
    def auto_update_location(self, max_depth=None):
        """
        Automatically searches for a unique file of the given file_type in the location
        and updates the location attribute to point to that file. 
        The search can be limited by specifying a max_depth.
        """
        if self.file_type is None:
            return
        
        if os.path.isdir(self.location):
            matching_files = []
            for root, dirs, files in os.walk(self.location):
                # Calculate the current depth
                current_depth = root[len(self.location):].count(os.sep)
                if max_depth is not None and current_depth > max_depth:
                    # If the current depth exceeds max_depth, skip this directory
                    dirs[:] = []  # Clear dirs to prevent os.walk from going deeper
                    continue

                for file in files:
                    if file.endswith(self.file_type):
                        matching_files.append(os.path.join(root, file))
            
            if len(matching_files) == 1:
                self.location = matching_files[0]
            elif len(matching_files) > 1:
                print(f"Warning: Multiple files found matching {self.file_type}. Location not updated.")
            else:
                print(f"No files found matching {self.file_type}.")

    
        

###################################################################################
# Functions for constructing Basic Informants from pre-existing directory structures:


def get_folder_path_sequences(root_folder) -> list:
    """
    Retrieves folder path sequences for all files accessible from within the specified root folder.

    Args:
        root_folder (str): Root folder path.

    Returns:
        list: List of folder sequences.
    """
    folder_sequences = []

    # Define a helper function to process files in a single folder
    def process_files_in_folder(args):
        folder_path, files = args
        sequences = []
        for file in files:
            # Get the relative path to the file from the root folder
            relative_path = os.path.relpath(os.path.join(folder_path, file), root_folder)
            
            # Split the relative path into a list of folder names
            folder_sequence = relative_path.split(os.path.sep)
            sequences.append(folder_sequence)
        return sequences

    # Collect all folder paths and file lists
    folder_files_list = [(folder_path, files) for folder_path, _, files in os.walk(root_folder)]

    # Use ThreadPoolExecutor to process folders in parallel
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_files_in_folder, folder_files_list))

    # Flatten the list of lists
    folder_sequences = [item for sublist in results for item in sublist]

    return folder_sequences

# Define the get_folder_path_sequences function, which is to be used as a sub-routine in create_file_informant_list_from_folder.
def get_folder_path_sequences_old(root_folder)->list:
    """
    Retrieves folder path sequences for all files accessible from within the specified root folder.

    Args:
        root_folder (str): Root folder path.

    Returns:
        list: List of folder sequences.
    """
    folder_sequences = []

    for folder_path, _, files in os.walk(root_folder):
        for file in files:
            # Get the relative path to the file from the root folder
            relative_path = os.path.relpath(os.path.join(folder_path, file), root_folder)
            
            # Split the relative path into a list of folder names
            folder_sequence = relative_path.split(os.path.sep)

            # Append the folder sequence to the list
            folder_sequences.append(folder_sequence)

    return folder_sequences

def create_file_informant_list_from_folder(root_folder,
                                           explicit=True,
                                           suppress=True,
                                           use_location=False, 
                                           attribute_sequence=[], 
                                           informant_class=None, 
                                           **kwargs)->list:
    """
    Extracts file informants from a folder.

    Args:
        root_folder (str): Root folder path.
        use_location (bool): Whether the file location is to be stored in the informant attributes.
        attribute_sequence (list): Designates how to assign folder names as attributes of the informant.
        informant_class: Subclass of Informant to be used.
        **kwargs: Additional keyword arguments.

    Returns:
        list: List of file informants.
    """

    # Initialize a default class_example of the informant_class.
    # This will allow us to obtain the relevant kwargs for constructing individual informants of the desired class.
    class_example = informant_class(explicit=explicit, suppress=suppress)

    # Get the folder_sequences for all files under the chosen root_folder
    folder_sequences = get_folder_path_sequences(root_folder)

    # Define a helper function for creating an informant
    def create_informant(file_folder_sequence):
        # Set the default attributes from the default class_example
        arguments_dictionary = class_example.__dict__.copy()

        if explicit:
            arguments_dictionary.update(**kwargs)

        # Store the location of the file if desired and applicable
        if use_location:
            arguments_dictionary.update({'location': os.path.join(root_folder, *file_folder_sequence)})

        # Retrieve the attributes that are designated by the path to the file
        arguments_dictionary.update(dict(zip(attribute_sequence, file_folder_sequence)))

        # Store the remaining attributes that are uniform throughout the folder
        arguments_dictionary.update({key: kwargs.get(key, arguments_dictionary.get(key)) for key in arguments_dictionary})

        # Initialize and return the current file informant
        return informant_class(explicit=explicit, suppress=suppress, informants=kwargs.get('informants', []), **arguments_dictionary)

    # Use ThreadPoolExecutor to create informants in parallel
    informant_list = []
    with ThreadPoolExecutor() as executor:
        informant_list = list(executor.map(create_informant, folder_sequences))

    return informant_list

def create_file_informant_list_from_folder_old(root_folder, 
                                           use_location=False, 
                                           attribute_sequence=[], 
                                           informant_class = File_Informant, 
                                               suppress=True,
                                           **kwargs)->list:
    """
    Extracts file informants from a folder.

    Args:
        root_folder (str): Root folder path.
        use_location (bool): Whether the file location is to be stored in the informant attributes.
        attribute_sequence (list): Designates how to assign folder names as attributes of the informant.
        informant_class: Subclass of Informant to be used.
        **kwargs: Additional keyword arguments.

    Returns:
        list: List of file informants.
    """

    # Initialize a default class_example of the informant_class.
    # This will allow us to obtain the relevant kwargs for constructing individual informants of the desired class.
    class_example = informant_class()

    informant_list = []

    # Get the folder_sequences for all files under the chosen root_folder
    folder_sequences = get_folder_path_sequences(root_folder)

    # For each file, we want to create a corresponding informant with attributes designated by the path to that file
    for file_folder_sequence in folder_sequences:

        # Set the default attributes from the default class_example
        arguments_dictionary = class_example.__dict__

        # Store the location of the file if desired and applicable
        if (use_location and isinstance(class_example,Directory_Informant)): # This needs editing March 11, 2024
            arguments_dictionary.update({'location': os.path.join(root_folder, *file_folder_sequence)})
        
        # Retrieve the attributes that are designated by the path to the file
        arguments_dictionary.update(dict(zip(attribute_sequence, file_folder_sequence)))

        # Store the remaining attributes that are uniform throughout the folder
        arguments_dictionary.update({key:kwargs.get(key, arguments_dictionary[key]) for key in arguments_dictionary})

        # Initialize and append the current file informant
        this_informant = informant_class(informants=kwargs.get('informants', []),suppress=suppress,**arguments_dictionary)
        informant_list.append(this_informant)

    return(informant_list)

def convert_to_informant_class(informant:Informant, new_informant_class, suppress=False, clip=True, push=False, **kwargs):
    """
    clip (bool) : Whether to restrict transferred attributes only to those attributes that are necessarily defined for all instances of the initial informant's class.
    If clip is False, then additional attributes of the informant that extend beyond those that must belong to all instances of its class are included in the transfer.

    push (bool) : Whether to restrict transferred attributes to those attributes that are necessarily defined for all instances of the new informant class.
    If push is True, then additional attributes of the original informant that extend beyond those that must belong to all instances of the new class are transfered to the converted informant.

    True push overrides True clip. NOTE: 2024-8-8: Looking back, these are probably not mutually exclusive...

    prevent (bool) : 
    suppress (bool) : Whether to ignore warnings regarding attributes that may not be populated in the final converted informant.
    """
    warning = None
    informant_class_inheritance_name_list = [item.__name__ for item in get_informant_class_mro(informant.__class__)]
    if not suppress and new_informant_class.__name__ not in informant_class_inheritance_name_list:
            warning = f"WARNING: Converted Informant '{informant.name}' of class '{informant.informant_class}' to informant class '{new_informant_class.__name__},' but the '{informant.informant_class}' informant class was not a descendent from '{new_informant_class.__name__}.' Some attributes of the converted informant may therefore be unpopulated or inappropriately constructed, and one may wish to check the converted informant for veracity. This warning has been added as an attribute."
            if not suppress:
                print(warning)
    
    if push:
        clip=False

    if clip:
        source_attribute_names = get_informant_class_attributes(informant.__class__)
        attributes_to_store = {attribute_name:informant.__dict__[attribute_name] for attribute_name in source_attribute_names}
    else:
        attributes_to_store = informant.__dict__

    attributes_to_store.update(kwargs)

    new_informant = new_informant_class(suppress=suppress, **attributes_to_store)
    if push:
        new_informant.__dict__.update(attributes_to_store)
    
    new_informant.informant_class = new_informant_class.__name__
    if warning:
        new_informant.__dict__.update({'warning':warning})
    return new_informant


class Informant_Dataframe(Informant):
    def __init__(self, pd_dict = {'name':[], 'informant':[], 'entry_time':[], 'verification_status':[]}, **kwargs):
        super().__init__(**kwargs)
        self.df = pd.DataFrame(pd_dict)
        self.df_names = self.df['name']
    
    def load_df(self, df_pkl_path, allow_duplicates=False, replace=False, verify=False):
        this_df = pd.read_pickle(df_pkl_path)
        if list(this_df.columns) == list(self.df.columns):
            self.df = this_df
            self.df_names = self.df['name']
        else:
            informant_list = list(this_df['informant'])
            self.append(informant_list, allow_duplicates, replace, verify)

    def set_df(self, df):
        self.df = df.copy(deep=True)
        self.df_names = self.df['name']

    def append(self, informants_list, allow_duplicates=False, replace=False, verify=False):
        now = datetime.now()
        # Format the date as "month_day_year"
        formatted_date = now.strftime("%m_%d_%Y")
        verification_status = 'pending'
        if verify:
            verification_status = formatted_date

        for informant in informants_list:
            this_name = informant.name

            this_row = {'name':this_name, 'informant':informant, 'entry_time':formatted_date, 'verification_status':verification_status}
            if this_name not in self.df_names or allow_duplicates:
                # Create a datetime object (for example, the current date and time)
                self.df = pd.concat([self.df, pd.DataFrame([this_row])], ignore_index=True)
            elif replace:
                index_to_replace = self.df.index[self.df['name'] == this_name].tolist()[0]
                print(f"The informant name {this_name} was already stored in the dataframe. Since 'replace' is True, the old informant was replaced.")
                self.df.loc[index_to_replace] = this_row
            else:
                print(f"The informant name {this_name} was already stored in the dataframe. Since 'replace' is False, the old informant was not replaced.")
        
    def save_df(self, df_pkl_path):
        self.df.to_pickle(df_pkl_path)


    def filter(self, expression, additional_context=None, absent=False):
        """
        Filters the DataFrame based on a custom boolean expression that evaluates attributes of the 'informant' objects.

        The method identifies attributes in the expression prefixed with '@', checks if these attributes exist in each 'informant' object, 
        and evaluates the expression for each row in the DataFrame. If an attribute is missing, the part of the expression involving that 
        attribute is treated as determined by the 'absent' argument, which is 'False' by default, or 'True' if specified.

        Args:
            expression (str): A boolean expression used for filtering. Attributes of 'informant' should be prefixed with '@'.
                              Logical operators '&' (AND) and '|' (OR) can be used.

        Returns:
            pd.DataFrame: A filtered DataFrame containing rows where the expression evaluates to True.

        Example:
            # Example Informant class
            class MyInformant(Informant):
                def __init__(self, name, age, **kwargs):
                    self.name = name
                    self.age = age

            # Create a DataFrame with Informant objects
            df = Informant_Dataframe()
            df.append([MyInformant("Alice", 30), MyInformant("Bob", 25)])

            # Filter the DataFrame where name is 'Alice' OR age is less than 28
            filtered_df = df.filter("(@name == 'Alice') | (@age < 28)")
        """
        filtered_indices = []

        # Wrap the entire expression in parentheses
        expression = f"({expression})"

        # The special escape string @informant will refer to the entire informant.
        expression = expression.replace("@self", "informant")

        # Extract the attribute names of interest
        attribute_names = set(re.findall(r'@(\w+)', expression))

        for index, row in self.df.iterrows():
            informant = row['informant']

            modified_expression = expression

            # Check that the attribute exists
            for attr in attribute_names:
                attr_exists = hasattr(informant, attr)

                if attr_exists:
                    # Replace '@attribute' with 'informant.attribute'
                    modified_expression = modified_expression.replace(f"@{attr}", f"informant.{attr}")
                else:
                    # Replace the entire condition involving the missing attribute with the absent argument.
                    pattern = rf'(?<=\(|&|\|) *[^()]*@{attr}[^()]* *(?=\)|&|\|)'
                    substring = re.search(pattern, modified_expression)
                    if substring:
                        modified_expression = modified_expression.replace(substring.group(), str(absent))

            # Evaluate the modified expression safely
            eval_context = {'informant': informant, 'isinstance': isinstance}
            if additional_context:
                eval_context.update(additional_context)
            try:
                if eval(modified_expression, eval_context):
                    filtered_indices.append(index)
            except Exception as e:
                print(f"Error evaluating expression: {e}")
                continue

        return self.df.loc[filtered_indices].copy(deep=True)

    def informant_dict_list(self):
        return [x.__dict__ for x in self.df['informant']]

    def informant_attribute_list(self, attribute):
        return [x.__dict__[attribute] for x in self.df['informant']]

############################################################################################################################################
if __name__ == "__main__":
    pass