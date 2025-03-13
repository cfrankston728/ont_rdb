from informant_class import Informant, Directory_Informant, File_Informant, convert_to_informant_class
# from graphviz import Digraph

# This is an example script defining an Informant ontology to be used in a computational biology context.
# Users may construct other Informant ontologies by following the pattern outlined in this script, which consists of a streamline of single class inheritances, followed by the introduction of attributes for newly defined Informant subclasses. For larger ontologies, it may be preferable to create multiple, leveled scripts of a similar nature.

# informant_subclass_dataframe.py will automatically construct an annotated ontological digraph for the automated production of Informant subclass examples.

""" informant_class_example_dataframe = pd.DataFrame({'informant_class':[], 'example_list':[]})
informant_class_example_dictionary = dict() """

# Note: January 13, 2024: Include ability to store fully-populated examples of informant classes into an informant_class_example dataframe. []
# Enable the user to include examples only of highly specific informants, and to construct and store examples of more general informants using the convert_to_informant_class, get_distinct_informant_class_attributes, and get_informant_class_inheritance_list functions. []

# Note: 2024-8-8: Plan to make Algorithm and Parameter informants a class in informant_class.py, since they seem to have general utility beyond any specific ontology for computational projects.
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

class Model_Directory(Directory_Informant):
    """
    Directory of a configured model.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config', None)
        self.tb_logs = kwargs.get('tb_logs', None)
        self.weights_tar = kwargs.get('weights_tar', None)
        self.latents_h5 = kwargs.get('latents_h5', None)

class File_Set_Element(File_Informant):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.file_set = kwargs.get('file_set', None)

class Bio_Source(Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.species = kwargs.get('species', None)

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

class Computational_Bio_Source(Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.species = kwargs.get('species', None)
        self.bio_source = kwargs.get('bio_source', None)
        self.bio_source_name = kwargs.get('bio_source_name', None)

class Table_File(File_Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sep = kwargs.get('sep', None)  # '\t' or ','
        # Initialize table_columns with None if not provided
        self.table_columns = kwargs.get('table_columns', None)
        self.header = kwargs.get('header', None)
    
    def get_df(self, sep=None, header=None, names=None, table_column_sep=',', index_col=None, max_depth=None):
        self.auto_update_location(max_depth)
        import pandas as pd
        
        if not hasattr(self, 'sep'):
            self.sep = '\t'
        # Set sep to instance value if not provided
        if sep is None:
            sep = self.sep
        else:
            self.sep = sep
        
        if header is None:
            header = self.header
        
        # Ensure sep is properly set (interpret '\t' as tab)
        if sep == '\\t':  # If sep is the string '\\t', replace with actual tab character
            sep = '\t'
        
        # Ensure table_columns is initialized, even for older objects
        if not hasattr(self, 'table_columns'):
            self.table_columns = None
        
        # If names is not None, update table_columns
        if names is not None:
            self.table_columns = ','.join(names)
        # If table_columns is set but names is None, use table_columns
        elif self.table_columns is not None:
            names = [col.strip("'") for col in self.table_columns.split(table_column_sep)]
        
        # If both table_columns and names are None, use default numeric columns
        return pd.read_csv(self.location, sep=sep, header=header, index_col=index_col, names=names if names is not None else None, engine='python')
    
    def split_table(self, output_dir, chunk_size, prefix='chunk_', file_extension='.tsv'):
        """
        Splits the table into multiple files with a specified chunk size.

        Args:
            output_dir (str): Directory to save the split files.
            chunk_size (int): Number of rows per chunk.
            prefix (str): Prefix for the output file names.
            file_extension (str): File extension for the output files (e.g., '.csv', '.tsv').
        """
        import os
        import pandas as pd

        sep = self.sep
        # Ensure sep is properly set (interpret '\t' as tab)
        if sep == '\\t':  # If sep is the string '\\t', replace with actual tab character
            sep = '\t'

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Read the table in chunks
        chunk_iter = pd.read_csv(self.location, sep=self.sep, chunksize=chunk_size, header=None, engine='python')
        chunk_files = []

        for i, chunk in enumerate(chunk_iter):
            chunk_file_path = os.path.join(output_dir, f"{prefix}{i + 1}{file_extension}")
            chunk.to_csv(chunk_file_path, index=False, sep=sep, header=False)
            chunk_files.append(chunk_file_path)
        
        chunk_file_informants_list = []
        for chunk_file in chunk_files:
            chunk_file_informant = convert_to_informant_class(self, type(self), push=True, suppress=True, location=chunk_file, algorithmic_parameters={'informant': self, 'output_dir':output_dir, 'chunk_size':chunk_size, 'prefix':prefix, 'file_extension':file_extension}, algorithm=Algorithm(name='Table_File.split_table'))
            chunk_file_informants_list.append(chunk_file_informant)
        return chunk_file_informants_list
        
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

class Research_Paper(Article):
    """
    A research paper.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.citation = kwargs.get('citation', None)

class Feature_Identifier(Algorithm):
    """
    Algorithm with additional attributes for featured_object_type and feature_type.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.featured_object_type = kwargs.get('featured_object_type', None)
        self.feature_type = kwargs.get('feature_type', None)

class HiC_Feature_Identifier(Feature_Identifier):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.featured_object_type = '3D-Genome'
        self.feature_type = kwargs.get('feature_type', None)

class Cell_Line(Bio_Source):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cell_type = kwargs.get('cell_type', None)

class Tissue(Bio_Source):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tissue_type = kwargs.get('tissue_type', None)

class Genome_Assembly(Computational_Bio_Source):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Project(Directory_Informant):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Computational_Bio_File(File_Informant, Computational_Bio_Source):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Computational_Bio_File_Set(File_Set, Computational_Bio_Source):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.computational_bio_file_type = kwargs.get('computational_bio_file_type', None)

class Computational_Genome_Bio_File_Set(Computational_Bio_File_Set):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.computational_genome_bio_file_type = kwargs.get('computational_genome_bio_file_type', None)

class Computational_Common_Genome_Bio_File_Set(Computational_Genome_Bio_File_Set):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.computational_genome_bio_file_type = kwargs.get('computational_genome_bio_file_type', None)
        self.genome_assembly_name = kwargs.get('genome_assembly_name', None)

class Bed_File_Set(Computational_Bio_File_Set):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.computational_bio_file_type = "Bed_File"

class bigWigAverage_Over_Bed_File_Set(Bed_File_Set):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.computational_bio_file_type = "Bed_File"
        self.bed_file_type = "bigWigAverage_Over_Bed_File"

class ChIP_seq_bigWigAverage_Over_Bed_File_Set(bigWigAverage_Over_Bed_File_Set):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.computational_bio_file_type = "Bed_File"
        self.bed_file_type = "bigWigAverage_Over_Bed_File"
        

class HiC_TAD_Boundary_Caller(HiC_Feature_Identifier):
    """
    A feature identifier specialized for Hi-C TAD boundaries.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.feature_type = 'TAD_Boundary'

class HiC_Loop_Caller(HiC_Feature_Identifier):
    """
    A feature identifier specialized for Hi-C loops.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.feature_type = 'Loop'

class Computational_Genome_Bio_File(Computational_Bio_File):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.genome_assembly_name = kwargs.get('genome_assembly_name', None)
        self.aliases = kwargs.get('aliases', None)

class Chromosome_File(Computational_Genome_Bio_File):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.genome_assembly_name = kwargs.get('genome_assembly_name', None)
        self.aliases = kwargs.get('aliases', None)
        self.chromosome = kwargs.get('chromosome', None)

class Curried_HiC_Loop_Caller(HiC_Loop_Caller):
    """
    A feature identifier specialized for Hi-C loops.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.curried_parameters = kwargs.get('curried_parameters', None)

class Curried_HiC_TAD_Boundary_Caller(HiC_TAD_Boundary_Caller):
    """
    A feature identifier specialized for Hi-C TAD Boundaries.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.curried_parameters = kwargs.get('curried_parameters', None)

class HiC_Feature_File(Computational_Genome_Bio_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hic_file = kwargs.get('HiC_File', None)
        self.feature_type = kwargs.get('feature_type', None)
        if self.hic_file is not None:
            self.genome_assembly_name = kwargs.get('genome_assembly_name', self.hic_file.genome_assembly_name)
            self.quality_threshold = kwargs.get('quality_threshold', self.hic_file.quality_threshold)
            self.hic_type = kwargs.get('hic_type', self.hic_file.hic_type)
            self.species = kwargs.get('species', self.hic_file.species)
        
class Genome_File(Computational_Genome_Bio_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class HiC_File(Computational_Genome_Bio_File):
    """
    A file class specialized for Hi-C files, including attributes for genome assembly, quality threshold, and Hi-C type.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.file_type = '.hic'
        self.quality_threshold = kwargs.get('quality_threshold', None)
        self.hic_type = kwargs.get('hic_type', None)
        self.bio_source = kwargs.get('bio_source', None)

        self.expressed = False
    
    def load_object(self): # In principle this is not necessary, we can define a function that takes in a HiC_File informant and returns a hic_object elsewhere and probably should. But this works fine.
        from hicstraw import HiCFile
        hic_object = HiCFile(self.location)
        

        return(hic_object)
    
    # def express_info(self):

    
class Parameters(Informant):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.algorithm = kwargs.get('algorithm', None)
        self.parameter_descriptions = kwargs.get('parameter_descriptions', {})
        self.parameters = kwargs.get('parameters', {})

# For this project it is particularly useful to specify information about this algorithm:
hicstraw_getMatrixZoomData = Algorithm(name="hicstraw.getMatrixZoomData",
                                          description="A method of hic objects from the hicstraw package, which returns a matrixZoomData object associated to the hic object. The matrixZoomData is an auxiliary object that navigates sub-matrices of its associated hic contact map on a pair of selected chromosomes, at a chosen resolution, normalization, and observation type.",
                                          reference_informant_names=['Juicer_Github'],
                                          parameter_descriptions={'chr1':'The first chromosome to select from a HiC_File.',
                           'chr2':'The second chromosome to select from a HiC_File.',
                           'obs_type':"The 'observation type,' which determines whether to return the matrixZoomData object directly after the normalization step ('observed'), or to transform the normalized matrix by: dividing each matrix entry value by: the smoothed mean entry value for all entries with components that lie at the same genomic distance from each other ('oe'), where the mean is smoothed by adding a nominal positive perturbation to the raw mean in case it is zero. To be clear, this transformation is applied after normalization.",
                           'norm': "The normalization method used to transform the matrixZoomData's matrix entries, applied to the raw-count matrix produced according to the selected binning resolution. Examples are 'NONE,' 'KR,' 'VC,' 'VC_SQRT', and 'SCALE, possibly among others. To be clear, this transformation is applied after binning raw reads to the chosen resolution.",
                           'resolution_units':"A parameter that should be set to 'BP,' standing for 'base-pair,' which is the genomic unit count as which the resolution parameter is to be interpreted.",
                           'res':'The resolution at which to bin the raw paired-read counts into a matrix.'})

class hicstraw_getMatrixZoomData_Parameters(Parameters):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        required_reference_informants = ['Juicer', 'hicstraw.getMatrixZoomData']
        for required_reference_informant in required_reference_informants:
            if required_reference_informant not in self.reference_informant_names:
                self.reference_informant_names.append(required_reference_informant)
        self.algorithm = 'hicstraw.getMatrixZoomData'
        self.parameters = {parameter_name:None for parameter_name in hicstraw_getMatrixZoomData.parameter_descriptions.keys()}
        self.parameters.update(kwargs.get('parameters', {}))
        #self.set_parameters()
    
    def set_parameters(self, *param_args, **param_kwargs):
        parameter_keys = hicstraw_getMatrixZoomData.parameter_descriptions.keys()
        param_args_dict = dict(zip(parameter_keys, param_args))
        param_args_dict.update(param_kwargs)
        self.parameters = param_args_dict

class bigWig_File(Computational_Genome_Bio_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_type = '.bigWig'
        self.target = kwargs.get('target', None)
        self.bigWig_type = kwargs.get('bigWig_type', None)
        self.bigWig_signal = kwargs.get('bigWig_signal', None)
        
class Bed_File(Computational_Genome_Bio_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_type = '.bed'
        self.gz = kwargs.get('gz', None)

class BedPe_File(Computational_Genome_Bio_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_type = '.bedpe'
        self.gz = kwargs.get('gz', None)

class Pairs_File(Computational_Genome_Bio_File):
    def __init__(self, **kwargs):
        suppress = kwargs.get('suppress',False)
        super().__init__(**kwargs)
        self.file_type = '.pairs'
        self.gz = kwargs.get('gz', None)
        self.chr1 = kwargs.get('chr1',1)
        self.pos1 = kwargs.get('pos1',2)
        self.chr2 = kwargs.get('chr2',3)
        self.pos2 = kwargs.get('pos2',4)
        if not suppress:
            print(f"Check to verify chromosome and position arguments.")
            
        

class ChIP_seq_bigWig_File(bigWig_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bigWig_type = 'ChIP_seq'

class HiC_Loops_File(BedPe_File, HiC_Feature_File):
    # July 3, 2024: NOTE: I may want to include the HiC file, Loop_Caller and Parameter settings as required attributes for this kind of informant. []
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.feature_type = 'HiC_Loop'

class Peak_File(Bed_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target = kwargs.get('target', None)

class bigWigAverage_Over_Bed_File(Bed_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bigWig_type = kwargs.get('bigWig_type', None)
        self.bigWig_signal = kwargs.get('bigWig_signal', None)

class PeakCount_Over_Bed_File(Bed_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.peak_type = kwargs.get('peak_type', None)
        
class ChIP_seq_PeakCount_Over_Bed_File(Bed_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.peak_type = 'ChIP_seq'
        self.ChIP_signal = kwargs.get('ChIP_signal', None)
        self.target = kwargs.get('target', None)

class HiC_TAD_Boundary_Bed_File(Bed_File, HiC_Feature_File):
    # July 3, 2024: NOTE: I may want to include the HiC file, TAD_Caller and Parameter settings as required attributes for this kind of informant. []
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.feature_type = 'HiC_TAD_Boundary'

class ATAC_seq_Peak_File(Peak_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target = 'ATAC_seq'

class ChIP_seq_bigWigAverage_Over_Bed_File(bigWigAverage_Over_Bed_File):
    # July 3, 2024: NOTE: I may want to include the bed file and bigwig file as required attributes for this kind of informant. []
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bigWig_type = 'ChIP_seq'
        self.target = kwargs.get('target', None)

""" class Absurd_Informant(HiC_File, Research_Paper, Institution):
    def __init__(self, **kwargs):
        super().__init__(**kwargs) """
############################################################################################################################################

if __name__ == "__main__":
    pass