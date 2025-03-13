# ont_rdb
``ont_rdb`` is a package for creating relational databases with an ontological framework.

<figure>
    <img src="ont_rdb/data/ont_rdb_concept1.png" alt="" title="ont_rdb-concept" width="450"/>
</figure>

## Introduction
An ontology is a formal representation of knowledge within a domain that can enhance comprehension and management of that domain's various objects. ``ont_rdb`` supports building, modifying, and sharing arbitrary ontologies by writing "ontology scripts," which are Python scripts satisfying the following properties:

1. The script name is of the form ``{X}_ontology.py``.
2. The script imports the ``informant_class.py`` module, which defines the **informant** class.
3. The script defines classes that ultimately inherit from classes defined in ``informant_class.py``.

The ontology defined by such a script encodes an acyclic, directed graph, with the informant class as the unique source node. The informant class is designed to represent a generic schema, such as is used in SQL, as a Python object. 
<figure>
    <img src="ont_rdb/data/ont_rdb_flow_diagram1.png" alt="Dependencies flow from the informant class script---ontology scripts and scripts that define specific instances of informants will depend on the informant class script. Once ontologies and informant objects within the context of that ontology are defined, they can be exported to related projects in the form of dataframes. Ontologies can be represented by a dataframe representing its associated directed, acyclic graph, while collections of informant objects can be stored in an informant dataframe, which is also defined in the informant class." title="ont_rdb-flow-diagram" width="450"/>
</figure>

``ont_rdb`` is envisioned as operating in tandem with Snakemake and possibly a larger database structure like SQL.

## Motivation

The fusion of a relational databases and ontologies aims to **keep large data analysis projects organized**, especially when multiple steps produce, process and combine new files of various different types. This structure facilitates the tracking and organization of data through "informants," Python objects that encapsulate data and relevant processing methods, simplifying data management.

Informants may compartmentalize methods relevant to data processing operations, and can be used to "expose" or "express" only relevant information from external scripts. Inspired by immunology, informants serve as interpretable interfaces between data and users or processes, improving data handling efficiency.
<figure>
    <img src="ont_rdb/data/MHC1_function.png" alt="Almost all nucleated cells naturally present cytosolic self-peptides bound to the protein major histocompatability complex one (MHC1). Antigens bound to MHC I can be recognized by mature CD8+ T Cells." title="MHC1-function-analogy" width="300"/>
    <figcaption>https://microbenotes.com/mhc-antigen-processing-presentation/#major-histocompatibility-class-ii-mhc-class-ii
    </figcaption>
</figure>

## Features

Within the ``ont_rdb`` package directory, the ``ontologies`` folder stores an example ontology script written for projects that process Hi-C data. Other scripts can be written and loaded into the folder. When scripting an ontology, it is recommended to introduce new fields/attributes/methods of informant sub-classes along with **meta-data** that describes those new fields/attributes/methods in an interpretable way, especially when the fields themselves are not easily understood at face value without additional context.

``ont_rdb`` constructs a dataframe representing an ontology's directed, rooted, acyclic graph (DRAG), and facilitates constructing generic examples from the ontology by populating terminal nodes in the graph (specific objects) and applying forgetful functors to map those specific objects onto corresponding examples of the more general objects they inherit from. The function ``convert_to_informant_class`` serves as this forgetful functor, with parameters that can adjust the manner in which one class is projected into another (ex: ``clip``, ``push``).

<img src="ont_rdb/data/ont_rdb_graph_vis.png" alt="Alt text" title="example-digraph" width="400"/>

The ``ont_rdb_explorer.ipynb`` script can be used to interact with the ontology defined by any chosen script in the ``ontologies`` folder. The script may be selected from a drop-down menu and imported. An **ontology dataframe** representing the associated directed graph can be constructed by following the simple directions in the Jupyter notebook.

Informant dataframes leverage existing pandas query operations and the Informant class to simulate a queryable relational database based on the attributes of stored informant objects using the ``filter`` method, which operates on a query string that can refer to attributes of arbitrary informants, or the informants themselves, through the escape symbol ``@``. For example, the query string

``"(@name == 'my_informant') | (isinstance(@self, File_Informant))"``

when given the ``additional_context`` of ``isinstance`` will refer to informants in the data frame that either have the name attribute of ``my_informant``, or are of the ``File_Informant`` class.

To construct informant dataframes, one may use the auxiliary functions in ``informant_class.py`` to leverage existing directory structures to define and store informant objects associated to files within that directory structure. In particular, the function ``create_file_informant_list_from_folder`` facilitates this operation.

## Installation
Simply run

``pip install git+https://github.com/cfrankston728/ont_rdb.git``

or clone the repository from github.

## Requirements

The dependencies of ``ont_rdb`` can be found listed within the following file:

``./ont_rdb/ont_rdb/workflow/snakemake_rules/envs/environment.yaml``

## Configuration

Using ``ont_rdb`` requires snakemake and the specification of a snakemake profile. Using ``mamba`` as the ``conda-frontend`` is recommended.

## Contributing

Thank you for your interest in contributing to our project! As this is a private repository, we assume you're already familiar with its goals and have been invited to contribute. Here are some guidelines to help you get started:

### Reporting Issues

- **Bug Reports:** If you encounter a bug, please file an issue using our bug report template. Include as much detail as possible: what you were doing when the bug occurred, steps to reproduce the issue, expected vs. actual behavior, and any error messages.
- **Feature Requests:** We welcome ideas for new features. Please submit a feature request issue, describing the feature and why you think it would be a valuable addition.

### Making Contributions

- **Pull Requests:** Before starting work on a significant change, please open an issue to discuss your ideas. This will allow us to give you feedback and help ensure that your time is well spent.
  - Fork the repository (if external access is granted).
  - Create a new branch for your changes.
  - Make your changes and commit them with clear, concise commit messages.
  - Push your branch and submit a pull request to the main branch.
  - Include a description of your changes and the issue number(s) your pull request addresses.
- **Code Review:** All contributions will be reviewed for quality and compatibility with the project goals. We aim to review pull requests promptly, but response times may vary based on current priorities.

### Coding Standards

- Please follow the coding standards and style guidelines for the project. This ensures consistency and maintainability of the codebase.
- Include comments in your code where necessary to explain complex or non-obvious logic.

### Legal

- By contributing to this project, you agree that your contributions will be licensed under its MIT License.
- Ensure that you have the right to use and contribute any code or content you submit.

For more information, feel free to contact the project maintainers.


## License

cfrankston728/ont_rdb is licensed under the

### MIT License

A short and simple permissive license with conditions only requiring preservation of copyright and license notices. Licensed works, modifications, and larger works may be distributed under different terms and without source code.

## Authors
Connor Frankston, Yardımcı Lab, OHSU

## Acknowledgments
I would like to offer a special thanks to Theresa Lusardi, Kenny Pavan, Ben Skubi, and Sam Kupp for their encouragement, support, and engagement with my vision for this project. I would also like to thank Gürkan Yardımcı, Sadik Esener, Matthew Rames, Tuğba and Furkan Özmen, Jungsun Kim, Juyoung Lee, Christopher Eddy, and Yujia Zhang for their knowledge, direction and mentorship.