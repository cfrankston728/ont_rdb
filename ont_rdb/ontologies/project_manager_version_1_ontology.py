from informant_class import Informant, Directory_Informant, File_Informant
# from graphviz import Digraph

# informant_subclass_dataframe.py will automatically construct an annotated ontological digraph for the automated production of Informant subclass examples.

""" informant_class_example_dataframe = pd.DataFrame({'informant_class':[], 'example_list':[]})
informant_class_example_dictionary = dict() """

# Note: January 13, 2024: Include ability to store fully-populated examples of informant classes into an informant_class_example dataframe. []
# Enable the user to include examples only of highly specific informants, and to construct and store examples of more general informants using the convert_to_informant_class, get_distinct_informant_class_attributes, and get_informant_class_inheritance_list functions. []

def is_valid_date_string(date_string):
    if date_string is None:
        return False
    else:
        try:
            year, month, day = [int(x) for x in date_string.split('-')]
            is_leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            if month < 1 or month > 12:
                return False
            
            days_in_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
            if month == 2 and is_leap_year:
                days_in_month[2] = 29
            
            if day < 1 or day > days_in_month[month]:
                return False
            
            return True
        except ValueError:
            # If there was a problem with conversion or splitting, return False
            return False

def get_date_value(date_string):
    if is_valid_date_string(date_string):
        year, month, day = [int(x) for x in date_string.split('-')]
        return (year + month/32 + day/32**2)
    else:
        return None

class DataBase(Informant):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Algorithm(Informant):
    """
    Informant with additional attributes for parameters.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.parameter_descriptions = kwargs.get('parameter_descriptions', None)
        self.script_path = kwargs.get('script_path', None)

class Parameters(Informant):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.algorithm = kwargs.get('algorithm', None)
        self.parameter_descriptions = kwargs.get('parameter_descriptions', {})
        self.parameters = kwargs.get('parameters', {})

class File_Set(Directory_Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Institution(Informant):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Article(Informant):
    """
    A research paper.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Website(Informant):
    """
    A website paper.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.url = kwargs.get('url', None)

class Laboratory(Informant):
    """
    A website paper.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Company(Institution):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class University(Institution):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Github_Repository(Website):
    """
    A website paper.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Ontology_Script(File_Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Algorithm_Script(File_Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.algorithm = kwargs.get('algorithm', None)

class Project(Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Project_Build(Project, Directory_Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build = kwargs.get('build', None)
        self.ontology_script = kwargs.get('ontology_script', None)

class Log(Directory_Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Log_Entry(File_Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_type = kwargs.get('file_type', None)
        self.date = kwargs.get('date', None)
        self.log = kwargs.get('log', None)
    
    def has_valid_date(self):
        return is_valid_date_string(self.date)
    def date_value(self):
        return get_date_value(self.date)

class Project_Log_Entry(Log_Entry):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.project = kwargs.get('project', None)

class Project_Build_Log_Entry(Project_Log_Entry):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.project_build = kwargs.get('project_build', None)

class Project_Log(Log):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.project = kwargs.get('project', None)

class Project_Build_Log(Project_Log):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.project_build = kwargs.get('project_build', None)

class Compiled_Log(File_Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

############################################################################################################################################

if __name__ == "__main__":
    pass