from informant_class import Informant, Directory_Informant, File_Informant
# from graphviz import Digraph

# This is an example script defining an Informant ontology to be used in a computational biology context.
# Users may construct other Informant ontologies by following the pattern outlined in this script, which consists of a streamline of single class inheritances, followed by the introduction of attributes for newly defined Informant subclasses. For larger ontologies, it may be preferable to create multiple, leveled scripts of a similar nature.

# informant_subclass_dataframe.py will automatically construct an annotated ontological digraph for the automated production of Informant subclass examples.

""" informant_class_example_dataframe = pd.DataFrame({'informant_class':[], 'example_list':[]})
informant_class_example_dictionary = dict() """

# Note: January 13, 2024: Include ability to store fully-populated examples of informant classes into an informant_class_example dataframe.
# Enable the user to include examples only of highly specific informants, and to construct and store examples of more general informants using the convert_to_informant_class, get_distinct_informant_class_attributes, and get_informant_class_inheritance_list functions.


class DataBase(Informant):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Algorithm(Informant):
    """
    Source with additional attributes for parameters.
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.parameter_descriptions = kwargs.get('parameter_descriptions', None)

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

class ChIP_seq_bigWig_File(bigWig_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bigWig_type = 'ChIP_seq'

class HiC_Loops_File(BedPe_File, HiC_Feature_File):
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.feature_type = 'HiC_TAD_Boundary'

class ATAC_seq_Peak_File(Peak_File):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target = 'ATAC_seq'

class ChIP_seq_bigWigAverage_Over_Bed_File(bigWigAverage_Over_Bed_File):
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